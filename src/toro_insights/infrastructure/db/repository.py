"""Repository Pattern — toda a I/O com PostgreSQL fica isolada aqui."""

from __future__ import annotations

from datetime import date

import pandas as pd
from sqlalchemy import Engine, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.types import Date

from toro_insights.config.settings import get_settings
from toro_insights.domain.constants import BUCKET_NAO_MAPEADO, ORDEM_NAO_MAPEADO


class CrmLeadRepository:
    """Acesso a dados de `toro.crm_leads`, `dim_fase_negocio` e `etl_carga`."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._schema = get_settings().db_schema

    # ---------------------------------------------------------------- DDL
    def aplicar_ddl(self, ddl_sql: str) -> None:
        """Executa o script DDL (cria schema, tabelas, seed). Idempotente."""
        with self._engine.begin() as conn:
            conn.execute(text(ddl_sql))

    # ----------------------------------------------------- dim_fase_negocio
    def carregar_mapa_fases(self) -> pd.DataFrame:
        """Retorna o mapeamento fase -> bucket/ordem/flags de `dim_fase_negocio`."""
        query = text(f"SELECT * FROM {self._schema}.dim_fase_negocio")
        return pd.read_sql(query, self._engine)

    def registrar_fases_nao_mapeadas(self, fases: list[str]) -> int:
        """Insere fases ausentes em `dim_fase_negocio` como 'A classificar'.

        Garante integridade referencial e evita perda silenciosa de dados novos.
        Retorna a quantidade inserida.
        """
        if not fases:
            return 0
        stmt = text(
            f"""
            INSERT INTO {self._schema}.dim_fase_negocio
                (fase_original, bucket_funil, ordem_funil, is_ganho, is_perda, is_descartar)
            VALUES (:fase, :bucket, :ordem, FALSE, FALSE, FALSE)
            ON CONFLICT (fase_original) DO NOTHING
            """
        )
        params = [
            {"fase": f, "bucket": BUCKET_NAO_MAPEADO, "ordem": ORDEM_NAO_MAPEADO} for f in fases
        ]
        with self._engine.begin() as conn:
            conn.execute(stmt, params)
        return len(fases)

    # -------------------------------------------------------------- etl_carga
    def iniciar_carga(self, arquivo: str, snapshot: date, hash_arquivo: str) -> int:
        """Cria registro de auditoria (status em_processamento) e retorna carga_id."""
        stmt = text(
            f"""
            INSERT INTO {self._schema}.etl_carga
                (arquivo_origem, snapshot_date, hash_arquivo, status)
            VALUES (:arq, :snap, :hash, 'em_processamento')
            RETURNING carga_id
            """
        )
        with self._engine.begin() as conn:
            return int(conn.execute(stmt, {"arq": arquivo, "snap": snapshot, "hash": hash_arquivo}).scalar_one())

    def finalizar_carga(self, carga_id: int, qtd: int, status: str) -> None:
        """Fecha o registro de auditoria com a contagem e o status final."""
        stmt = text(
            f"UPDATE {self._schema}.etl_carga SET qtd_linhas=:q, status=:s WHERE carga_id=:id"
        )
        with self._engine.begin() as conn:
            conn.execute(stmt, {"q": qtd, "s": status, "id": carga_id})

    def hash_ja_carregado(self, hash_arquivo: str) -> bool:
        """True se já existe carga concluída com o mesmo hash de arquivo."""
        stmt = text(
            f"SELECT 1 FROM {self._schema}.etl_carga "
            f"WHERE hash_arquivo=:h AND status='concluida' LIMIT 1"
        )
        with self._engine.connect() as conn:
            return conn.execute(stmt, {"h": hash_arquivo}).first() is not None

    # -------------------------------------------------------------- crm_leads
    def truncar_e_carregar(self, df: pd.DataFrame) -> int:
        """RN-04 — TRUNCATE em crm_leads e recarrega o snapshot inteiro.

        Tudo em uma única transação: ou a base nova entra completa, ou nada muda.
        """
        with self._engine.begin() as conn:
            conn.execute(text(f"TRUNCATE TABLE {self._schema}.crm_leads"))
            df.to_sql(
                "crm_leads",
                conn,
                schema=self._schema,
                if_exists="append",
                index=False,
                method="multi",
                chunksize=1000,
                dtype={
                    # Garante o cast correto de tipos especiais do Postgres.
                    "oportunidade_id": PG_UUID(as_uuid=False),
                    "data_prevista_faturamento": Date(),
                },
            )
        return len(df)

    def atualizar_valor_faturado(self, oportunidade_id: str, valor: float) -> None:
        """RN-13 — grava o Valor Faturado (vindo da NF) em uma oportunidade."""
        stmt = text(
            f"UPDATE {self._schema}.crm_leads SET valor_faturado=:v WHERE oportunidade_id=:id"
        )
        with self._engine.begin() as conn:
            conn.execute(stmt, {"v": valor, "id": oportunidade_id})

    # ---------------------------------------------------------- nf_faturamento
    def truncar_e_carregar_nf(self, df: pd.DataFrame) -> int:
        """TRUNCATE em nf_faturamento e recarrega os itens (snapshot)."""
        with self._engine.begin() as conn:
            conn.execute(text(f"TRUNCATE TABLE {self._schema}.nf_faturamento RESTART IDENTITY"))
            df.to_sql(
                "nf_faturamento", conn, schema=self._schema, if_exists="append",
                index=False, method="multi", chunksize=1000,
                dtype={"oportunidade_id": PG_UUID(as_uuid=False), "data_emissao": Date()},
            )
        return len(df)

    def agregar_valor_faturado(self) -> int:
        """RN-13 — soma valor_total por oportunidade e grava em crm_leads.valor_faturado.

        Zera antes para refletir remoções; retorna nº de oportunidades atualizadas.
        """
        with self._engine.begin() as conn:
            conn.execute(text(f"UPDATE {self._schema}.crm_leads SET valor_faturado = NULL"))
            res = conn.execute(
                text(
                    f"""
                    UPDATE {self._schema}.crm_leads c
                    SET valor_faturado = s.total
                    FROM (
                        SELECT oportunidade_id, SUM(valor_total) AS total
                        FROM {self._schema}.nf_faturamento
                        GROUP BY oportunidade_id
                    ) s
                    WHERE c.oportunidade_id = s.oportunidade_id
                    """
                )
            )
            return res.rowcount

    def contar_nf_orfas(self) -> int:
        """Itens de NF cujo oportunidade_id não existe em crm_leads (órfãos)."""
        stmt = text(
            f"""
            SELECT count(DISTINCT n.oportunidade_id)
            FROM {self._schema}.nf_faturamento n
            LEFT JOIN {self._schema}.crm_leads c ON c.oportunidade_id = n.oportunidade_id
            WHERE c.oportunidade_id IS NULL
            """
        )
        with self._engine.connect() as conn:
            return int(conn.execute(stmt).scalar_one())

    def buscar_nf(self) -> pd.DataFrame:
        """Itens de NF para a camada de analytics de produtos."""
        return pd.read_sql(text(f"SELECT * FROM {self._schema}.nf_faturamento"), self._engine)

    def buscar_nf_enriquecido(self) -> pd.DataFrame:
        """Itens de NF + dimensões da venda (geo, loja, campanha) para a Tela de Produtos."""
        query = text(
            f"""
            SELECT n.item_id, n.oportunidade_id, n.numero_nf, n.data_emissao,
                   n.produto, n.gama, n.modelo, n.quantidade,
                   n.valor_unitario, n.valor_total,
                   c.cidade, c.uf, c.concessionaria, c.campanha, c.vendedor
            FROM {self._schema}.nf_faturamento n
            JOIN {self._schema}.crm_leads c ON c.oportunidade_id = n.oportunidade_id
            """
        )
        return pd.read_sql(query, self._engine)

    def buscar_leads(self, where: str = "", params: dict | None = None) -> pd.DataFrame:
        """Leitura genérica para a camada de analytics/dashboards."""
        query = f"SELECT * FROM {self._schema}.crm_leads"
        if where:
            query += f" WHERE {where}"
        return pd.read_sql(text(query), self._engine, params=params or {})
