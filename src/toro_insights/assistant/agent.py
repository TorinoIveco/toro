"""Agente consultor (Google Gemini) com function calling sobre dados reais."""

from __future__ import annotations

from google import genai
from google.genai import types

from toro_insights.assistant.context import construir_digest
from toro_insights.assistant.tools import FERRAMENTAS
from toro_insights.config.settings import get_settings

SYSTEM_PROMPT = """\
Você é um consultor sênior de Marketing e Comercial de uma concessionária de \
veículos e caminhões IVECO (rede Torino, atuação em MT e MS). Seu papel é ajudar \
o Gerente de Marketing a tomar decisões: sugerir campanhas, ideias de ações, onde \
investir verba e onde focar o time comercial.

REGRAS:
- Baseie-se SOMENTE nos dados fornecidos no contexto e nas ferramentas. Nunca invente números.
- Se faltar um dado, use as ferramentas para buscá-lo; se ainda assim não houver, diga claramente.
- A regra de venda é: oportunidade com Fase "Ganho e Entregue". Conversão = vendas / leads.
- Não há dados pessoais disponíveis (LGPD) — trabalhe só com agregados.
- Responda em português, objetivo e acionável. Cite os números que embasam a recomendação.
- Ao PROPOR UMA CAMPANHA, estruture: Objetivo · Público-alvo (segmento/cidade/gama) · \
Oferta/Mensagem · Canais · Métrica de sucesso · Por que (dado que sustenta).
"""


def _to_contents(historico: list[dict]) -> list[dict]:
    """Converte histórico [{role, text}] para o formato do Gemini (user/model)."""
    contents = []
    for h in historico:
        papel = "model" if h["role"] == "assistant" else "user"
        contents.append({"role": papel, "parts": [{"text": h["text"]}]})
    return contents


def responder(historico: list[dict]) -> str:
    """Gera a resposta do consultor para o histórico de conversa."""
    settings = get_settings()
    if not settings.gemini_api_key:
        return "⚠️ Configure a `GEMINI_API_KEY` no .env para ativar o assistente."

    client = genai.Client(api_key=settings.gemini_api_key)
    system = SYSTEM_PROMPT + "\n\n## DADOS ATUAIS\n" + construir_digest()
    config = types.GenerateContentConfig(
        system_instruction=system,
        tools=FERRAMENTAS,
        temperature=0.4,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(maximum_remote_calls=6),
    )
    resp = client.models.generate_content(
        model=settings.gemini_model,
        contents=_to_contents(historico),
        config=config,
    )
    return resp.text or "(sem resposta)"
