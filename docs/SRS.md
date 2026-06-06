# TORO Insights — SRS (Software Requirements Specification)

> Plataforma de inteligência de CRM para concessionária de veículos e caminhões.
> Base: ISO/IEC/IEEE 29148. Documento vivo — atualizado a cada fase.
> Status: **Fase 1 concluída (Descoberta e Modelagem)**. Próximo: Fase 2 (Engenharia de Dados).

---

## 1. Problem Statement

Uma concessionária (rede TORINO/IVECO, múltiplas lojas) opera o módulo *Leads
Qualificados* do **Microsoft Dynamics CRM**. Hoje o **Gerente de Marketing** baixa
manualmente um Excel consolidado com a foto atual das oportunidades. Os dados
existem, mas vivem como planilha estática: não há visão consolidada de conversão,
funil, desempenho por campanha/região/loja, nem priorização de leads. Decisões de
investimento de marketing e foco comercial são tomadas por intuição.

**Estado ideal:** uma plataforma (TORO Insights) que ingere o export do Dynamics,
padroniza/versiona os dados e entrega dashboards de conversão, funil comercial,
ranking de campanhas, inteligência geográfica e um score preditivo de fechamento —
ancorado na regra-mãe `Fase do Negócio = "GANHO E ENTREGUE"` ⟹ venda.

**Persona primária:** Gerente de Marketing (login/senha, autoatendimento Streamlit).
**Beneficiário secundário:** Direção Comercial.

**Métrica de sucesso da plataforma:**
1. Substituir a análise manual em planilha por dashboards self-service.
2. Ranking acionável de campanhas por taxa de conversão e R$ faturado.
3. Lead score com **ROC AUC ≥ 0,75** validado (Quente/Morno/Frio).

---

## 2. Tabela dos 4 Grandes Riscos

| Risco | Avaliação | Mitigação |
|---|---|---|
| Valor (vão usar?) | 🟢 Baixo | Gerente já baixa o Excel mensalmente; entregar Tela 1 cedo. |
| Usabilidade | 🟢 Baixo | Persona única, dados pré-configurados, filtros globais consistentes. |
| Viabilidade Técnica | 🟠 Médio-Alto | Snapshot sem histórico; vazamento de dados no ML; desbalanceamento do target; texto livre em cidade/campanha. → RISCO-01..04. |
| Viabilidade de Negócio | 🟠 Médio | LGPD (CPF/CNPJ, celular, e-mail, nome). → RISCO-05. |

---

## 3. Requisitos Funcionais (RF)

| ID | Requisito | Critério de aceite |
|---|---|---|
| RF-01 | Autenticação por login/senha (persona Gerente de Marketing) | Acesso só após login; sessão Streamlit. |
| RF-02 | Ingestão de Excel consolidado (upload) com validação e carga auditada | Arquivo aceito, validado (Pydantic), carregado; registro em `etl_carga`. |
| RF-03 | Integração da NF para `valor_faturado` (CPF/CNPJ + data) | Valor casado por janela de data; múltiplos casamentos sinalizados. |
| RF-04 | Tela 1 — Dashboard Executivo | KPIs (leads, vendas, conversão, R$) + gráficos campanha/cidade/ano. |
| RF-05 | Tela 2 — Funil Comercial | Volume por etapa, conversão entre etapas, gargalos, taxa de perda. |
| RF-06 | Tela 3 — Análise de Campanhas | Leads/vendas/conversão por campanha; ranking melhor/pior; insights. |
| RF-07 | Tela 4 — Inteligência Geográfica | Conversão por cidade/UF; Top 10 cidades e estados. |
| RF-08 | Tela 5 — Lead Scoring (XGBoost) | Probabilidade %, classe Quente/Morno/Frio, importância de variáveis, métricas. |
| RF-09 | Exportação Excel dos resultados (OpenPyXL/XlsxWriter) | Download de tabelas/relatórios em .xlsx. |

Rastreabilidade: RF-04..08 atendem às 10 perguntas de negócio do briefing.

---

## 4. Requisitos Não-Funcionais (RNF)

| ID | Requisito |
|---|---|
| RNF-01 | Stack obrigatória: Python 3.12+, Streamlit, PostgreSQL (Supabase), Pandas/NumPy, Plotly, Scikit-Learn/XGBoost, Joblib, Pydantic, Loguru, OpenPyXL/XlsxWriter. |
| RNF-02 | Clean Architecture + SOLID; Repository Pattern; Service Layer; type hints; docstrings. |
| RNF-03 | Config via ambiente (.env / python-dotenv); segredos fora do código (Twelve-Factor). |
| RNF-04 | Logs estruturados com Loguru. |
| RNF-05 | LGPD: mascaramento de PII na UI; hash do documento; criptografia em repouso (Supabase); segredos gerenciados. |
| RNF-06 | ML: métricas Accuracy/Precision/Recall/F1/ROC AUC; anti-vazamento (RN-10); persistência via Joblib. |
| RNF-07 | Desempenho: dashboards responsivos com cache do Streamlit. |
| RNF-08 | Testabilidade (pytest), modularização, baixo acoplamento. |
| RNF-09 | Validação de dados de entrada com Pydantic. |

---

## 5. Regras de Negócio (RN)

| ID | Regra |
|---|---|
| RN-01 ⭐ | **Target:** `venda_concretizada = (UPPER(TRIM(fase_negocio)) = 'GANHO E ENTREGUE')`; `target_ml = 1` se verdadeiro, senão `0`. (A base grava "Ganho e Entregue".) |
| RN-02 | Fonte da verdade do funil/target é `fase_negocio`. `razao_status` é secundário (auditoria). |
| RN-03 | Granularidade: 1 linha = 1 oportunidade. PK = `oportunidade_id` (GUID). CPF/CNPJ pode repetir. |
| RN-04 | Carga = snapshot consolidado que substitui a base; cada carga registrada em `etl_carga` (auditoria + snapshot_date). |
| RN-05 | Base analítica exclui `Desconsiderar(Erro no Cadastro)` (is_descartar). |
| RN-06 | Mapeamento das 28 fases → buckets de funil governado em `dim_fase_negocio`. |
| RN-07 | Perda = {Perdida, Perdemos para Concorrência, Desistência do Cliente, Financiamento não Aprovado, Reprovado pelo Gerente}. `Não Faturado` = em andamento (bucket Faturamento), NÃO é perda. |
| RN-08 | `tempo_atendimento_horas` em horas. `tempo_resposta_horas` = (1º atendimento − criação) só quando datas consistentes; senão `flag_data_inconsistente=TRUE`. |
| RN-09 | `tipo_pessoa`: 11 dígitos → PF, 14 → PJ. |
| RN-10 ⚠️ | Anti-vazamento ML: `valor_faturado`, `data_prevista_faturamento`, `razao_status`, `fase_negocio`/`bucket_funil` e datas pós-criação dependentes de desfecho NÃO podem ser features de scoring. |
| RN-11 | LGPD: `cliente_nome`, `documento`, `celular`, `email` mascarados na UI; `documento` pseudonimizado por hash. |
| RN-12 | `ano` = ano de `data_criacao`. |
| RN-13 | Integração NF: `valor_faturado` casado à oportunidade por CPF/CNPJ + data (janela). Múltiplos casamentos → sinalizar para revisão. |

---

## 6. Catálogo de KPIs

> Base analítica (B) = todas as oportunidades exceto `is_descartar` (RN-05).

| KPI | Fórmula |
|---|---|
| Total de Leads | `COUNT(*) em B` |
| Total de Vendas | `COUNT(*) WHERE target_ml=1` |
| Taxa de Conversão | `Vendas / Leads` |
| Receita Faturada | `SUM(valor_faturado) WHERE venda` |
| Ticket Médio | `Receita / Vendas` |
| Conversão por Campanha / Cidade / UF / Concessionária / Vendedor / Necessidade | `vendas/leads GROUP BY dimensão` |
| Volume por Etapa do Funil | `COUNT GROUP BY bucket_funil` |
| Taxa de Perda | `is_perda / Leads` |
| Tempo Médio de Resposta | `AVG(tempo_resposta_horas)` |
| Tempo Médio no Funil | `AVG(dias_no_funil)` |
| Evolução Anual | KPIs `GROUP BY ano` |

Deferido (P3): "Oportunidades Paradas" — fora do escopo v1.

---

## 7. Restrições, Premissas e Pendências

**Premissas:** export = arquivo único consolidado que substitui a base; `valor_faturado`
vem de fonte externa (NF), não do Dynamics.

**Pendências (`[a confirmar]`):**
- P2 detalhe: chave/forma exata de obtenção dos dados de NF e janela de data para o casamento.
- Domínios completos de `Necessidade do Cliente` (nulo na amostra).
- Volume real da base (linhas, anos de histórico).

---

## 8. Contexto Regulatório (LGPD)

Dados pessoais tratados: nome, CPF/CNPJ, celular, e-mail. Finalidade: analítica
interna (marketing/comercial). Princípios aplicados: minimização, mascaramento na
apresentação, pseudonimização (hash) do documento, criptografia em repouso e
controle de acesso. Threat model formal (STRIDE) e nível ASVS alvo → Fase de Segurança.
