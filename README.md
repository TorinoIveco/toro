# TORO Insights

Plataforma de inteligência de CRM para concessionária de veículos e caminhões.
Transforma o export do módulo *Leads Qualificados* (Microsoft Dynamics) em
dashboards, funil comercial, análise de campanhas, inteligência geográfica e
lead scoring (XGBoost), ancorada na regra: `Fase do Negócio = "GANHO E ENTREGUE"` ⟹ venda.

## Documentação
A concepção (Fase 1) está em [`docs/`](docs/): SRS, dicionário de dados, MER e DDL.

## Stack
Python 3.12+ · Streamlit · PostgreSQL (Supabase) · Pandas/NumPy · Plotly ·
Scikit-Learn/XGBoost · SQLAlchemy + psycopg · Pydantic · Loguru.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env        # edite DATABASE_URL e DOCUMENTO_HASH_SALT
```

## Uso

```bash
# 1) Cria schema + tabelas + seed das 28 fases
python scripts/init_db.py

# 2) Carrega um export do Dynamics (TRUNCATE + load do snapshot)
python scripts/run_etl.py "/caminho/Leads Qualificados.xlsx"

# Testes
pytest
```

## Arquitetura (Clean Architecture)
```
src/toro_insights/
  config/          # settings via ambiente (Twelve-Factor)
  domain/          # regras de negócio puras (RN-*) + constantes
  schemas/         # validação Pydantic (RNF-09)
  etl/             # extract → transform → load → pipeline
  infrastructure/  # db (Repository Pattern) + nf (integração de notas)
  utils/           # logging (Loguru)
scripts/           # init_db, run_etl (CLI)
tests/             # pytest
```

## Dashboard

```bash
streamlit run streamlit_app.py     # abre em http://localhost:8501
```
Login padrão em `.env` (`APP_USUARIO` / `APP_SENHA`).

## Lead Scoring (treino)
```bash
python scripts/train_model.py            # treina XGBoost e salva models/lead_scoring.joblib
```
O treino exige base com as duas classes (vendas e não-vendas).

## Status
- ✅ Fase 1 — Descoberta e Modelagem
- ✅ Fase 2 — Engenharia de Dados (ETL + integração de NF)
- ✅ Fase 3 — Tela 1: Dashboard Executivo
- ✅ Fase 4 — Tela 2: Funil Comercial
- ✅ Fase 5 — Tela 3: Análise de Campanhas (ranking + insights automáticos)
- ✅ Fase 6 — Tela 4: Inteligência Geográfica (cidades/estados, treemap)
- ✅ Fase 7 — Tela 5: Lead Scoring (XGBoost, ROC AUC ~0,97)
- ✅ Tela 6 — Análise de Produtos (faturamento por gama/modelo/produto/cidade)

- ✅ Camada 6 — Assistente Inteligente (chat consultor com Google Gemini + tool-calling)
- ✅ Tela de administração — Atualizar Dados (upload de planilhas + ETL + retreino pela UI)

Todas as 7 telas do briefing + o Assistente IA concluídos. App multipágina (`views/`):
dashboard, funil, campanhas, geografia, scoring, produtos, assistente
(navegação em `streamlit_app.py`). Banco em produção: **Supabase** (PostgreSQL 17).

### Assistente IA
Pacote `src/toro_insights/assistant/` (context, tools, agent). Usa `GEMINI_API_KEY`
do `.env`. Só envia dados **agregados** ao modelo (LGPD). Ferramentas de
function-calling para consultar KPIs, desempenho por dimensão, funil, produtos e scoring.
