# TORO Insights — Dicionário de Dados (`toro.crm_leads`)

Legenda: **PK** chave · **PII** dado pessoal (LGPD) · **DRV** derivado no ETL ·
**⛔ML** proibido como feature de scoring (vazamento, RN-10)

| Coluna (destino) | Origem (Dynamics) | Tipo | Notas |
|---|---|---|---|
| `oportunidade_id` **PK** | (Não Modificar) Oportunidade | UUID | GUID do Dynamics; chave natural |
| `carga_id` **DRV** | — | BIGINT | FK → `etl_carga` |
| `data_criacao` | Data de Criação | TIMESTAMP | Entrada do lead; base temporal |
| `data_modificacao` | (Não Modificar) Data de Modificação | TIMESTAMP | Última atualização do estágio |
| `data_associacao_vendedor` | Data Associação Vendedor | TIMESTAMP | SLA comercial |
| `data_primeiro_atendimento` | Data Primeiro Atendimento | TIMESTAMP | SLA de resposta |
| `data_prevista_faturamento` | Data de Previsão do Faturamento | DATE | Forecast · ⛔ML |
| `ano` **DRV** | — | SMALLINT | `EXTRACT(YEAR FROM data_criacao)` |
| `cliente_nome` **PII** | Nome da Conta | TEXT | Mascarar na UI |
| `documento` **PII** | Documento (CPF/CNPJ) | TEXT | Vem mascarado; pode repetir |
| `documento_hash` **DRV** | — | TEXT | SHA-256 p/ dedupe/ligação NF |
| `tipo_pessoa` **DRV** | — | CHAR(2) | PF (11 díg) / PJ (14 díg) |
| `celular` **PII** | Celular | TEXT | Mascarar na UI |
| `email` **PII** | Email | TEXT | Mascarar na UI |
| `campanha` | Nome da Campanha | TEXT | Dimensão de Marketing |
| `concessionaria` | Concessionária | TEXT | Dimensão (loja) |
| `vendedor` | Vendedor | TEXT | Dimensão (anulável) |
| `cidade` | Cidade | TEXT | Geo (texto livre → normalizar) |
| `uf` | Estado | CHAR(2) | Geo |
| `necessidade` | Necessidade do Cliente | TEXT | Feature ML (anulável) |
| `status_relacionamento` | Status de Relacionamento | TEXT | Feature ML (Novo/Sem/Com) |
| `fase_negocio` | Fase do Negócio | TEXT | ⭐ Fonte do target; FK → `dim_fase_negocio` |
| `razao_status` | Razão do Status | TEXT | Secundário/auditoria · ⛔ML |
| `bucket_funil` **DRV** | — | TEXT | via `dim_fase_negocio` |
| `ordem_funil` **DRV** | — | SMALLINT | ordenação das etapas |
| `valor_faturado` | NF (fonte externa) | NUMERIC(14,2) | R$; só em vendas · ⛔ML |
| `tempo_atendimento_horas` | Tempo Atendimento Lead (Hora) | INTEGER | em horas |
| `tempo_resposta_horas` **DRV** | — | NUMERIC | 1º atend − criação (se consistente) |
| `dias_no_funil` **DRV** | — | NUMERIC | modificação − criação |
| `venda_concretizada` **DRV** | — | BOOLEAN | RN-01 |
| `target_ml` **DRV** | — | SMALLINT | 1/0 |
| `is_perda` **DRV** | — | BOOLEAN | RN-07 |
| `flag_data_inconsistente` **DRV** | — | BOOLEAN | DQ (datas fora de ordem) |

**Colunas descartadas** (internas do Dynamics): `Soma de Verificação da Linha`
(checksum), `Código` (código interno), 2ª `Data de Modificação` duplicada.

## Tabela `toro.nf_faturamento` (itens de NF — grão de item, 1 oportunidade : N itens)

Fonte: relatório de faturamento do ERP. Liga à venda por `oportunidade_id`
(mesmo GUID do CRM). RN-13. `crm_leads.valor_faturado` = `SUM(valor_total)` por oportunidade.

| Coluna | Origem (ERP) | Tipo | Notas |
|---|---|---|---|
| `item_id` **PK** | — | BIGSERIAL | chave técnica |
| `oportunidade_id` | (Não Modificar) Oportunidade | UUID | FK lógica → `crm_leads`; **repete** (1:N) |
| `numero_nf` | nº da NF | TEXT | pode repetir entre itens da mesma NF |
| `data_emissao` | Data Emissão | DATE | |
| `produto` | Produto | TEXT | ex.: "S-Way 540 6x4" |
| `gama` | Gama | TEXT | segmento: Leve / Médio / Semi-Pesado / Pesado |
| `modelo` | Modelo | TEXT | ex.: "S-Way", "Tector", "Daily Chassi" |
| `quantidade` | Quantidade | NUMERIC | |
| `valor_unitario` | Valor Un. | NUMERIC(14,2) | |
| `valor_total` | Valor Total | NUMERIC(14,2) | base do somatório de receita |
| `carga_id` | — | BIGINT | FK → `etl_carga` |

Itens **sem `oportunidade_id`** vão para quarentena (não atribuíveis a uma venda).

## Domínios controlados

- **`Status de Relacionamento`** (3): Novo · Sem Relacionamento · Com Relacionamento
- **`Fase do Negócio`** (28 valores) → ver mapeamento em `dim_fase_negocio` (DDL).
- **`Razão do Status`** (14): Aberta · Encaminhado Para o Vendedor · Em Andamento ·
  Em Negociação · Suspenso · Aguardando Faturamento · Faturado · Aguardando Entrega
  do Produto · Aguardando Ganhar Oportunidade · Ganho(a) · Perdida · Desistiu do
  Negócio · Esgotado(a)
