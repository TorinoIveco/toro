# TORO Insights — Modelo Entidade-Relacionamento (MER)

Modelagem **pragmática**: 1 fato (`crm_leads`) + 1 dimensão de governança
(`dim_fase_negocio`) + 1 auditoria de cargas (`etl_carga`). Campanha/Concessionária/
Vendedor/Município ficam denormalizados em `crm_leads` na v1 (ótimo p/ Pandas/
Streamlit) e podem virar dimensões próprias depois.

```mermaid
erDiagram
    ETL_CARGA ||--o{ CRM_LEADS : "origina"
    DIM_FASE_NEGOCIO ||--o{ CRM_LEADS : "classifica"
    CRM_LEADS ||--o{ NF_FATURAMENTO : "fatura (1:N)"
    ETL_CARGA ||--o{ NF_FATURAMENTO : "origina"

    ETL_CARGA {
        bigserial   carga_id PK
        text        arquivo_origem
        date        snapshot_date
        int         qtd_linhas
        text        hash_arquivo
        text        status
        timestamptz criado_em
    }
    DIM_FASE_NEGOCIO {
        text     fase_original PK
        text     bucket_funil
        smallint ordem_funil
        boolean  is_ganho
        boolean  is_perda
        boolean  is_descartar
    }
    CRM_LEADS {
        uuid      oportunidade_id PK
        bigint    carga_id FK
        text      fase_negocio FK
        text      campanha
        text      concessionaria
        text      vendedor
        text      cidade
        char      uf
        text      necessidade
        text      status_relacionamento
        numeric   valor_faturado
        boolean   venda_concretizada
        smallint  target_ml
        timestamp data_criacao
    }
    NF_FATURAMENTO {
        bigserial item_id PK
        uuid      oportunidade_id FK
        text      numero_nf
        date      data_emissao
        text      produto
        text      gama
        text      modelo
        numeric   quantidade
        numeric   valor_unitario
        numeric   valor_total
        bigint    carga_id FK
    }
```

## Relacionamentos
- `etl_carga (1) → (N) crm_leads`: cada linha pertence à carga que a inseriu.
- `dim_fase_negocio (1) → (N) crm_leads`: cada oportunidade referencia uma fase.
- `crm_leads (1) → (N) nf_faturamento`: uma venda tem vários itens de NF; a
  receita da oportunidade é a soma dos `valor_total`. `oportunidade_id` **repete**
  em `nf_faturamento` (grão de item).
- Cliente (CPF/CNPJ) **não** é entidade própria na v1: pode repetir entre
  oportunidades; identificado por `documento` / `documento_hash`.
