"""Testes da autenticação por perfil (RBAC)."""

from __future__ import annotations

from types import SimpleNamespace

from toro_insights.presentation.auth import (
    PERFIL_ASSISTENTE,
    PERFIL_GERENTE,
    autenticar,
)


def _settings(assistente: bool = True) -> SimpleNamespace:
    return SimpleNamespace(
        app_usuario="gerente",
        app_senha="senha-gerente",
        app_assistente_usuario="assistente" if assistente else "",
        app_assistente_senha="senha-assistente" if assistente else "",
    )


def test_gerente_autentica():
    assert autenticar("gerente", "senha-gerente", _settings()) == PERFIL_GERENTE


def test_assistente_autentica():
    assert autenticar("assistente", "senha-assistente", _settings()) == PERFIL_ASSISTENTE


def test_senha_errada_falha():
    assert autenticar("gerente", "errada", _settings()) is None
    assert autenticar("assistente", "errada", _settings()) is None


def test_usuario_inexistente_falha():
    assert autenticar("ninguem", "x", _settings()) is None


def test_assistente_nao_configurado_nao_autentica():
    # Com credenciais de assistente vazias, ninguém entra como assistente.
    s = _settings(assistente=False)
    assert autenticar("", "", s) is None
    assert autenticar("assistente", "senha-assistente", s) is None
