"""Constantes do domínio: mapeamento de colunas e valores canônicos."""

from __future__ import annotations

#: Nome da aba relevante no Excel exportado do Dynamics.
SHEET_LEADS = "Leads Qualificados"

#: Valor (normalizado) que caracteriza venda concretizada (RN-01).
TARGET_FASE = "GANHO E ENTREGUE"

#: Mapeamento: cabeçalho exato do Excel (Dynamics) -> coluna destino em crm_leads.
#: Colunas não listadas (checksum, código, 2ª Data de Modificação) são descartadas.
COLUMN_MAP: dict[str, str] = {
    "(Não Modificar) Oportunidade": "oportunidade_id",
    "(Não Modificar) Data de Modificação": "data_modificacao",
    "Data de Criação": "data_criacao",
    "Nome da Conta (Conta) (Conta)": "cliente_nome",
    "Razão do Status": "razao_status",
    "Nome da Campanha": "campanha",
    "Documento (BR: CPF/CNPJ) (Conta) (Conta)": "documento",
    "Status de Relacionamento (Conta) (Conta)": "status_relacionamento",
    "Concessionária (Conta) (Conta)": "concessionaria",
    "Vendedor (Conta) (Conta)": "vendedor",
    "Fase do Negócio": "fase_negocio",
    "Data Associação Vendedor": "data_associacao_vendedor",
    "Tempo Atendimento Lead (Hora)": "tempo_atendimento_horas",
    "Data Primeiro Atendimento": "data_primeiro_atendimento",
    "Celular (Conta) (Conta)": "celular",
    "Email (Conta) (Conta)": "email",
    "Necessidade do Cliente": "necessidade",
    "Cidade (Conta) (Conta)": "cidade",
    "Estado (Conta) (Conta)": "uf",
    "Data de Previsão do Faturamento": "data_prevista_faturamento",
}

#: Mapeamento: cabeçalho do relatório de NF (ERP) -> coluna destino em nf_faturamento.
#: A chave 'oportunidade_id' é o mesmo GUID do CRM. Cabeçalhos são casados de
#: forma tolerante a espaços múltiplos (ver nf_extract).
NF_COLUMN_MAP: dict[str, str] = {
    "(Não Modificar) Oportunidade": "oportunidade_id",
    "nº da NF": "numero_nf",
    "Data Emissão": "data_emissao",
    "Produto": "produto",
    "Gama": "gama",
    "Modelo": "modelo",
    "Quantidade": "quantidade",
    "Valor Un.": "valor_unitario",
    "Valor Total": "valor_total",
}

#: Colunas de data (parse com dayfirst=True).
DATE_COLUMNS = [
    "data_criacao",
    "data_modificacao",
    "data_associacao_vendedor",
    "data_primeiro_atendimento",
    "data_prevista_faturamento",
]

#: Bucket atribuído a fases ainda não mapeadas em dim_fase_negocio.
BUCKET_NAO_MAPEADO = "A classificar"
ORDEM_NAO_MAPEADO = 50

#: UFs válidas (Brasil) para normalização/validação geográfica.
UFS_VALIDAS = frozenset(
    "AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split()
)
