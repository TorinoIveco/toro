"""Testes das regras de negócio puras (não exigem banco)."""

from __future__ import annotations

from datetime import datetime

from toro_insights.domain import rules


class TestTarget:
    def test_ganho_e_entregue_eh_venda(self):
        assert rules.calcular_target("Ganho e Entregue") == (True, 1)

    def test_case_e_espacos_normalizados(self):
        assert rules.calcular_target("  GANHO  E   ENTREGUE ") == (True, 1)

    def test_outras_fases_nao_sao_venda(self):
        for fase in ["Ganha", "Faturado", "Em Negociação", "Perdida", None, ""]:
            assert rules.calcular_target(fase) == (False, 0)


class TestTipoPessoa:
    def test_pf_11_digitos(self):
        assert rules.inferir_tipo_pessoa("123.456.789-09") == "PF"

    def test_pj_14_digitos(self):
        assert rules.inferir_tipo_pessoa("12.345.678/0001-95") == "PJ"

    def test_mascarado_indeterminado(self):
        assert rules.inferir_tipo_pessoa("079.***.***-55") is None


class TestHashDocumento:
    def test_deterministico_e_com_salt(self):
        h1 = rules.hash_documento("12345678909", "s1")
        h2 = rules.hash_documento("123.456.789-09", "s1")
        assert h1 == h2  # ignora máscara
        assert h1 != rules.hash_documento("12345678909", "s2")  # salt muda o hash

    def test_vazio_retorna_none(self):
        assert rules.hash_documento(None, "s") is None


class TestDuracoes:
    def test_tempo_resposta_positivo(self):
        c = datetime(2024, 1, 1, 0, 0)
        a = datetime(2024, 1, 1, 5, 30)
        assert rules.calcular_tempo_resposta_horas(c, a) == 5.5

    def test_tempo_resposta_negativo_eh_none(self):
        c = datetime(2024, 1, 2)
        a = datetime(2024, 1, 1)
        assert rules.calcular_tempo_resposta_horas(c, a) is None

    def test_datas_inconsistentes(self):
        c = datetime(2024, 6, 1)
        assert rules.datas_inconsistentes(c, datetime(2020, 1, 1), None, None) is True
        assert rules.datas_inconsistentes(c, datetime(2024, 6, 2), None, None) is False
