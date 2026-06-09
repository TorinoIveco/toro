"""Geração da planilha de contatos no formato Brevo (pandas puro, testável).

Roda inteiramente server-side a partir da base do CRM. NÃO envolve LLM nem
qualquer terceiro — a PII (e-mail, telefone, nome) nunca sai do app.
"""

from __future__ import annotations

import re
from io import BytesIO

import pandas as pd

#: Colunas do CSV de importação do Brevo, na ordem esperada.
COLUNAS_BREVO = [
    "CONTACT ID", "EMAIL", "FIRSTNAME", "LASTNAME",
    "SMS", "LANDLINE_NUMBER", "WHATSAPP", "INTERESTS",
]


def telefone_e164(celular: object, ddi: str = "55") -> str:
    """Normaliza um celular brasileiro para o formato internacional (+55DDDNUMERO).

    Retorna '' quando o número é vazio, mascarado ou inválido — o Brevo exige
    formato E.164. Ex.: '(65) 99999-9999' -> '+5565999999999'.
    """
    if celular is None:
        return ""
    digitos = re.sub(r"\D", "", str(celular))
    if not digitos:
        return ""
    # Já vem com DDI 55 (12 ou 13 dígitos: 55 + DDD + 8/9 dígitos).
    if digitos.startswith(ddi) and len(digitos) >= 12:
        return "+" + digitos
    digitos = digitos.lstrip("0")
    # DDD (2) + número (8 ou 9). Mascarados/parciais caem fora desta faixa.
    if 10 <= len(digitos) <= 11:
        return f"+{ddi}{digitos}"
    return ""


def split_nome(nome: object) -> tuple[str, str]:
    """Divide o nome em (FIRSTNAME, LASTNAME). Primeiro token vs. restante."""
    n = str(nome).strip() if nome is not None else ""
    if not n or n.lower() == "nan":
        return "", ""
    partes = n.split()
    return partes[0], " ".join(partes[1:])


def montar_interests(*valores: object) -> str:
    """Concatena campos de interesse não vazios com ' | ' (ex.: necessidade + campanha)."""
    limpos = []
    for v in valores:
        s = str(v).strip() if v is not None else ""
        if s and s.lower() != "nan":
            limpos.append(s)
    return " | ".join(limpos)


def _email_valido(email: object) -> bool:
    s = str(email).strip().lower() if email is not None else ""
    return bool(s) and "@" in s and "*" not in s and s != "nan"


def montar_planilha_brevo(df: pd.DataFrame) -> pd.DataFrame:
    """Converte leads do CRM no DataFrame de contatos do Brevo.

    Regras:
    - mantém apenas linhas com e-mail válido (Brevo deduplica/importa por e-mail);
    - deduplica por e-mail preservando a 1ª ocorrência (chame já ordenado por
      potencial desc para manter o melhor contato de cada pessoa);
    - SMS = LANDLINE_NUMBER = WHATSAPP = celular normalizado (E.164);
    - INTERESTS = necessidade + campanha.
    """
    if df.empty:
        return pd.DataFrame(columns=COLUNAS_BREVO)

    g = df.copy()
    g = g[g["email"].apply(_email_valido)]
    if g.empty:
        return pd.DataFrame(columns=COLUNAS_BREVO)

    g["__email"] = g["email"].astype(str).str.strip().str.lower()
    g = g.drop_duplicates(subset="__email", keep="first")

    nomes = g.get("cliente_nome", pd.Series([None] * len(g))).apply(split_nome)
    fones = g.get("celular", pd.Series([None] * len(g))).apply(telefone_e164)
    # INTERESTS: do mais acionável (o que a pessoa quer) ao mais genérico.
    vazio = pd.Series([None] * len(g))
    produto = g.get("produto_interesse", vazio)
    modelo = g.get("modelo_interesse", vazio)
    necessidade = g.get("necessidade", vazio)
    campanha = g.get("campanha", vazio)
    interesses = [
        montar_interests(p, m, n, c)
        for p, m, n, c in zip(produto, modelo, necessidade, campanha)
    ]

    out = pd.DataFrame(
        {
            "CONTACT ID": "",  # vazio: o Brevo gera/deduplica pelo EMAIL
            "EMAIL": g["__email"].values,
            "FIRSTNAME": [n[0] for n in nomes],
            "LASTNAME": [n[1] for n in nomes],
            "SMS": fones.values,
            "LANDLINE_NUMBER": fones.values,
            "WHATSAPP": fones.values,
            "INTERESTS": interesses,
        },
        columns=COLUNAS_BREVO,
    )
    return out.reset_index(drop=True)


def gerar_csv(df_brevo: pd.DataFrame) -> bytes:
    """Serializa o DataFrame Brevo em CSV (UTF-8 com BOM, compatível com Excel/Brevo)."""
    return df_brevo.to_csv(index=False).encode("utf-8-sig")


def gerar_xlsx(df_brevo: pd.DataFrame) -> bytes:
    """Serializa o DataFrame Brevo em XLSX."""
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df_brevo.to_excel(writer, sheet_name="Contatos", index=False)
    buffer.seek(0)
    return buffer.getvalue()
