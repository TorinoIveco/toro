-- ============================================================
-- TORO Insights — Schema v1 (Fase 1: Descoberta e Modelagem)
-- PostgreSQL / Supabase
-- ============================================================
CREATE SCHEMA IF NOT EXISTS toro;
-- (hash do documento é feito em Python; sem dependência de extensões)

-- ------------------------------------------------------------
-- 1) Auditoria de cargas (RN-04)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS toro.etl_carga (
    carga_id       BIGSERIAL PRIMARY KEY,
    arquivo_origem TEXT NOT NULL,
    snapshot_date  DATE NOT NULL,
    qtd_linhas     INTEGER NOT NULL DEFAULT 0,
    hash_arquivo   TEXT,
    status         TEXT NOT NULL DEFAULT 'em_processamento'
                   CHECK (status IN ('em_processamento','concluida','falha')),
    criado_em      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ------------------------------------------------------------
-- 2) Dimensão de governança das fases (RN-06)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS toro.dim_fase_negocio (
    fase_original TEXT PRIMARY KEY,
    bucket_funil  TEXT NOT NULL,
    ordem_funil   SMALLINT NOT NULL,
    is_ganho      BOOLEAN NOT NULL DEFAULT FALSE,
    is_perda      BOOLEAN NOT NULL DEFAULT FALSE,
    is_descartar  BOOLEAN NOT NULL DEFAULT FALSE
);

-- Seed das 28 fases reais (mapeamento validado — Fase 1)
INSERT INTO toro.dim_fase_negocio
    (fase_original, bucket_funil, ordem_funil, is_ganho, is_perda, is_descartar)
VALUES
    -- 1. Prospecção
    ('Intenção ou Prospecção',            'Prospecção',            1, FALSE, FALSE, FALSE),
    ('Oportunidade Aberta',               'Prospecção',            1, FALSE, FALSE, FALSE),
    ('Informações do Cliente',            'Prospecção',            1, FALSE, FALSE, FALSE),
    ('Montagem de Cadastro',              'Prospecção',            1, FALSE, FALSE, FALSE),
    ('Produto de Interesse',              'Prospecção',            1, FALSE, FALSE, FALSE),
    -- 2. Negociação
    ('Em Negociação',                     'Negociação',            2, FALSE, FALSE, FALSE),
    ('Negociação Iniciada',               'Negociação',            2, FALSE, FALSE, FALSE),
    ('Condições de Pagamento',            'Negociação',            2, FALSE, FALSE, FALSE),
    -- 3. Proposta
    ('Proposta Comercial',                'Proposta',              3, FALSE, FALSE, FALSE),
    -- 4. Crédito/Financiamento
    ('Analise de Crédito',                'Crédito/Financiamento', 4, FALSE, FALSE, FALSE),
    ('Aguardando Aprovação Financeira',   'Crédito/Financiamento', 4, FALSE, FALSE, FALSE),
    ('Financiamento Aprovado',            'Crédito/Financiamento', 4, FALSE, FALSE, FALSE),
    -- 5. Aprovação Gerência
    ('Aprovação do Gerente',              'Aprovação Gerência',    5, FALSE, FALSE, FALSE),
    -- 6. Faturamento/Fechamento (inclui 'Não Faturado' = em andamento, RN-07/P1)
    ('Aguardando Faturamento',            'Faturamento',           6, FALSE, FALSE, FALSE),
    ('Aguardando Confirmação do Cliente', 'Faturamento',           6, FALSE, FALSE, FALSE),
    ('Finalização',                       'Faturamento',           6, FALSE, FALSE, FALSE),
    ('Faturado',                          'Faturamento',           6, FALSE, FALSE, FALSE),
    ('Faturamento Parcial',               'Faturamento',           6, FALSE, FALSE, FALSE),
    ('Aguardando Entrega do Produto',     'Faturamento',           6, FALSE, FALSE, FALSE),
    ('Ganha',                             'Faturamento',           6, FALSE, FALSE, FALSE),
    ('Não Faturado',                      'Faturamento',           6, FALSE, FALSE, FALSE),
    -- 7. Ganho (sucesso) — RN-01
    ('Ganho e Entregue',                  'Ganho',                 7, TRUE,  FALSE, FALSE),
    -- Perda — RN-07
    ('Perdida',                           'Perda',                99, FALSE, TRUE,  FALSE),
    ('Perdemos para Concorrência',        'Perda',                99, FALSE, TRUE,  FALSE),
    ('Desistência do Cliente',            'Perda',                99, FALSE, TRUE,  FALSE),
    ('Financiamento não Aprovado',        'Perda',                99, FALSE, TRUE,  FALSE),
    ('Reprovado pelo Gerente',            'Perda',                99, FALSE, TRUE,  FALSE),
    -- Descartar — RN-05
    ('Desconsiderar(Erro no Cadastro)',   'Descartar',             0, FALSE, FALSE, TRUE)
ON CONFLICT (fase_original) DO NOTHING;

-- ------------------------------------------------------------
-- 3) Tabela principal (fato)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS toro.crm_leads (
    oportunidade_id           UUID PRIMARY KEY,
    carga_id                  BIGINT REFERENCES toro.etl_carga(carga_id),
    -- datas
    data_criacao              TIMESTAMP,
    data_modificacao          TIMESTAMP,
    data_associacao_vendedor  TIMESTAMP,
    data_primeiro_atendimento TIMESTAMP,
    data_prevista_faturamento DATE,
    ano                       SMALLINT,
    -- PII (LGPD — RN-11)
    cliente_nome              TEXT,
    documento                 TEXT,
    documento_hash            TEXT,
    tipo_pessoa               CHAR(2) CHECK (tipo_pessoa IN ('PF','PJ')),
    celular                   TEXT,
    email                     TEXT,
    -- dimensões
    campanha                  TEXT,
    concessionaria            TEXT,
    vendedor                  TEXT,
    cidade                    TEXT,
    uf                        CHAR(2),
    necessidade               TEXT,
    status_relacionamento     TEXT,
    -- status / funil
    fase_negocio              TEXT REFERENCES toro.dim_fase_negocio(fase_original),
    razao_status              TEXT,
    bucket_funil              TEXT,
    ordem_funil               SMALLINT,
    -- métricas / target
    valor_faturado            NUMERIC(14,2),
    tempo_atendimento_horas   INTEGER,
    tempo_resposta_horas      NUMERIC,
    dias_no_funil             NUMERIC,
    venda_concretizada        BOOLEAN NOT NULL DEFAULT FALSE,
    target_ml                 SMALLINT NOT NULL DEFAULT 0 CHECK (target_ml IN (0,1)),
    is_perda                  BOOLEAN NOT NULL DEFAULT FALSE,
    -- qualidade
    flag_data_inconsistente   BOOLEAN NOT NULL DEFAULT FALSE
);

-- ------------------------------------------------------------
-- 3b) Itens de faturamento (NF) — grão de item (1 oportunidade : N itens)
--     RN-13: liga à venda por oportunidade_id (mesmo GUID do CRM).
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS toro.nf_faturamento (
    item_id         BIGSERIAL PRIMARY KEY,
    oportunidade_id UUID NOT NULL,           -- FK lógica p/ crm_leads (soft)
    numero_nf       TEXT,
    data_emissao    DATE,
    produto         TEXT,
    gama            TEXT,                     -- segmento: Leve/Médio/Semi-Pesado/Pesado
    modelo          TEXT,
    quantidade      NUMERIC,
    valor_unitario  NUMERIC(14,2),
    valor_total     NUMERIC(14,2),
    carga_id        BIGINT REFERENCES toro.etl_carga(carga_id)
);
CREATE INDEX IF NOT EXISTS idx_nf_oportunidade ON toro.nf_faturamento(oportunidade_id);
CREATE INDEX IF NOT EXISTS idx_nf_gama         ON toro.nf_faturamento(gama);
CREATE INDEX IF NOT EXISTS idx_nf_modelo       ON toro.nf_faturamento(modelo);

-- ------------------------------------------------------------
-- 4) Índices p/ filtros dos dashboards
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_leads_ano       ON toro.crm_leads(ano);
CREATE INDEX IF NOT EXISTS idx_leads_campanha  ON toro.crm_leads(campanha);
CREATE INDEX IF NOT EXISTS idx_leads_uf_cidade ON toro.crm_leads(uf, cidade);
CREATE INDEX IF NOT EXISTS idx_leads_conc      ON toro.crm_leads(concessionaria);
CREATE INDEX IF NOT EXISTS idx_leads_vendedor  ON toro.crm_leads(vendedor);
CREATE INDEX IF NOT EXISTS idx_leads_fase      ON toro.crm_leads(fase_negocio);
CREATE INDEX IF NOT EXISTS idx_leads_target    ON toro.crm_leads(target_ml);
CREATE INDEX IF NOT EXISTS idx_leads_documento ON toro.crm_leads(documento_hash);
