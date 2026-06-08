"""Testes da geração da planilha Brevo."""

from __future__ import annotations

import pandas as pd

from toro_insights.export import brevo


def test_telefone_e164_normaliza_celular_br():
    assert brevo.telefone_e164("(65) 99999-9999") == "+5565999999999"
    assert brevo.telefone_e164("65 9999-9999") == "+556599999999"  # 10 dígitos
    assert brevo.telefone_e164("5565999999999") == "+5565999999999"  # já com DDI


def test_telefone_e164_descarta_invalido_ou_mascarado():
    assert brevo.telefone_e164("(15) 99753-****") == ""  # mascarado
    assert brevo.telefone_e164(None) == ""
    assert brevo.telefone_e164("") == ""
    assert brevo.telefone_e164("123") == ""  # curto demais


def test_split_nome():
    assert brevo.split_nome("ANTONIO AUGUSTO BISPO") == ("ANTONIO", "AUGUSTO BISPO")
    assert brevo.split_nome("MARIA") == ("MARIA", "")
    assert brevo.split_nome(None) == ("", "")


def test_montar_interests_ignora_vazios():
    assert brevo.montar_interests("Caminhão pesado", "Limpa Estoque") == "Caminhão pesado | Limpa Estoque"
    assert brevo.montar_interests(None, "Camp X") == "Camp X"
    assert brevo.montar_interests(None, None) == ""


def test_montar_planilha_filtra_email_invalido_e_deduplica():
    df = pd.DataFrame(
        [
            {"email": "a@x.com", "cliente_nome": "JOAO SILVA", "celular": "(65) 99999-9999",
             "necessidade": "Pesado", "campanha": "Camp1"},
            {"email": "a@x.com", "cliente_nome": "JOAO SILVA", "celular": "(65) 99999-9999",
             "necessidade": "Pesado", "campanha": "Camp1"},  # duplicado
            {"email": "***@hotmail.com", "cliente_nome": "MASC", "celular": None,
             "necessidade": None, "campanha": None},  # email mascarado -> fora
            {"email": "", "cliente_nome": "SEM EMAIL", "celular": "65999999999",
             "necessidade": None, "campanha": None},  # sem email -> fora
        ]
    )
    out = brevo.montar_planilha_brevo(df)
    assert list(out.columns) == brevo.COLUNAS_BREVO
    assert len(out) == 1  # 1 válido após dedup e remoção de inválidos
    linha = out.iloc[0]
    assert linha["EMAIL"] == "a@x.com"
    assert linha["FIRSTNAME"] == "JOAO" and linha["LASTNAME"] == "SILVA"
    assert linha["SMS"] == linha["WHATSAPP"] == linha["LANDLINE_NUMBER"] == "+5565999999999"
    assert linha["INTERESTS"] == "Pesado | Camp1"
    assert linha["CONTACT ID"] == ""


def test_montar_planilha_vazia():
    assert brevo.montar_planilha_brevo(pd.DataFrame()).empty
    assert list(brevo.montar_planilha_brevo(pd.DataFrame()).columns) == brevo.COLUNAS_BREVO


def test_gerar_csv_tem_cabecalho_correto():
    df = pd.DataFrame(
        [{"email": "a@x.com", "cliente_nome": "J S", "celular": "65999999999",
          "necessidade": "N", "campanha": "C"}]
    )
    csv = brevo.gerar_csv(brevo.montar_planilha_brevo(df)).decode("utf-8-sig")
    cabecalho = csv.splitlines()[0]
    assert cabecalho == "CONTACT ID,EMAIL,FIRSTNAME,LASTNAME,SMS,LANDLINE_NUMBER,WHATSAPP,INTERESTS"
