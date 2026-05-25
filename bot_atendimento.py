#!/usr/bin/env python3
"""
Bot de Atendimento Vértice Studio — WhatsApp via Z-API
Uso local (teste): python bot_atendimento.py
Uso como servidor: python bot_atendimento.py --server
"""

import sys
import os
import json
import requests
import anthropic
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import uvicorn

# ── Credenciais ───────────────────────────────────────────────────────────────
API_KEY           = os.getenv("ANTHROPIC_API_KEY",   "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")
ZAPI_INSTANCE     = os.getenv("ZAPI_INSTANCE",       "3F3A9513AC5312D5128CBE824EEE0644")
ZAPI_TOKEN        = os.getenv("ZAPI_TOKEN",          "218FD1D410194581EAD962CD")
ZAPI_CLIENT_TOKEN = os.getenv("ZAPI_CLIENT_TOKEN",   "Fcb0b8e82daa948a29a14e33282228397S")
ZAPI_BASE         = f"https://api.z-api.io/instances/{ZAPI_INSTANCE}/token/{ZAPI_TOKEN}"

# ── Modelo ────────────────────────────────────────────────────────────────────
MODEL = "claude-opus-4-7"

# ── System prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """Identidade e Papel
Você é o assistente de atendimento oficial da Vertice Studio no WhatsApp. Seu objetivo é recepcionar potenciais clientes, tirar dúvidas iniciais de forma extremamente humana e natural, e, o mais rápido possível, conduzir a conversa para o agendamento de uma reunião de alinhamento com a equipe.

Tom de Voz e Personalidade

Humano e Empático: Você não fala como um robô. Use uma linguagem leve, cordial e direta, típica de uma conversa de negócios descontraída no WhatsApp no Brasil (ex: "Olá! Tudo bem?", "Entendi perfeitamente", "Bora marcar um papo?").

Conciso: Mensagens curtas. Ninguém gosta de ler blocos de texto gigantes no WhatsApp. Se precisar explicar algo complexo, divida em duas ou três mensagens curtas.

Uso de Emojis: Use emojis de forma estratégica para dar vida ao texto, mas sem exageros (🚀, 🤝, 💡, 👇, 😊).

Proibido: Nunca use termos excessivamente formais (ex: "Prezado", "Compreendo", "Destarte") e evite jargões técnicos confusos a menos que o cliente os utilize primeiro.

Informações da Empresa

Nome: Vertice Studio.

O que faz: Agência focada em soluções digitais, marketing e inovação para negócios.

Portfólio/Links: Não possuímos site. Para ver nossos trabalhos e conhecer mais sobre a agência, você deve sempre direcionar o cliente para o nosso Instagram: @vertice_studio2.0.

Fluxo de Atendimento e Agendamento

Recepção: Cumprimente de forma amigável, pergunte o nome da pessoa (se já não souber) e como a Vertice pode ajudar o negócio dela a crescer.

Sondagem Rápida: Faça no máximo UMA pergunta por vez para entender o nicho do cliente ou qual o principal desafio dele hoje.

O Gancho (Call to Action): Assim que entender a dor do cliente, valide-a e sugira a reunião. Exemplo: "Legal, [Nome]! Nós conseguimos te ajudar com isso. O ideal agora seria a gente bater um papo rápido de 15 a 20 minutinhos em uma call para eu entender melhor seu cenário e te mostrar como a Vertice atua."

Marcação: Ofereça duas opções de horários próximos ou pergunte a preferência do cliente (ex: "Você prefere na parte da manhã ou da tarde?").

Regras de Segurança

Nunca prometa preços fixos ou prazos sem que isso tenha sido definido em reunião.

Se o cliente fizer uma pergunta muito complexa que você não sabe responder, diga: "Essa é uma ótima pergunta! Para te dar a resposta mais precisa sobre isso, o ideal é abordarmos na nossa reunião. Como está sua agenda para amanhã?"

Sempre responda no idioma em que o cliente falar (priorizando Português do Brasil)."""

# ── Anthropic client ──────────────────────────────────────────────────────────
client = anthropic.Anthropic(api_key=API_KEY)

# Histórico por número de telefone (sessões separadas por usuário)
sessoes: dict[str, list[dict]] = {}

def obter_historico(telefone: str) -> list[dict]:
    if telefone not in sessoes:
        sessoes[telefone] = []
    return sessoes[telefone]

def gerar_resposta(telefone: str, mensagem: str) -> str:
    historico = obter_historico(telefone)
    historico.append({"role": "user", "content": mensagem})

    resposta = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        thinking={"type": "adaptive"},
        messages=historico,
    )

    texto = resposta.content[-1].text
    historico.append({"role": "assistant", "content": texto})
    return texto

# ── Z-API: enviar mensagem ────────────────────────────────────────────────────
def enviar_whatsapp(telefone: str, mensagem: str) -> None:
    url = f"{ZAPI_BASE}/send-text"
    payload = {"phone": telefone, "message": mensagem}
    headers = {"Content-Type": "application/json", "Client-Token": ZAPI_CLIENT_TOKEN}
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f"📤 Z-API status: {r.status_code} | resposta: {r.text[:200]}")
    except Exception as e:
        print(f"❌ Erro ao enviar mensagem: {e}")

# ── Servidor webhook (modo --server) ──────────────────────────────────────────
app = FastAPI(title="Bot Vértice Studio")

class FixSlashMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request.scope["path"] = request.scope["path"].replace("//", "/")
        return await call_next(request)

app.add_middleware(FixSlashMiddleware)

@app.get("/")
def health():
    return {"status": "online", "bot": "Vértice Studio"}

@app.post("/webhook")
async def webhook(request: Request):
    try:
        dados = await request.json()
    except Exception:
        return JSONResponse({"status": "erro", "msg": "JSON inválido"}, status_code=400)

    # Log completo para debug
    print(f"\n📦 PAYLOAD RECEBIDO:\n{json.dumps(dados, ensure_ascii=False, indent=2)}\n")

    # Ignora mensagens enviadas pelo próprio bot
    if dados.get("fromMe"):
        print("⏭ Ignorado: mensagem própria")
        return {"status": "ok"}

    telefone = dados.get("phone", "")
    mensagem = dados.get("body", "").strip() or dados.get("text", {}).get("message", "").strip()

    if not telefone or not mensagem:
        print(f"⚠ Sem telefone ou mensagem. phone={telefone!r} body={dados.get('body')!r}")
        return {"status": "ok"}

    print(f"📥 [{telefone}]: {mensagem}")

    resposta = gerar_resposta(telefone, mensagem)
    enviar_whatsapp(telefone, resposta)

    print(f"🤖 Bot → [{telefone}]: {resposta[:80]}...")
    return {"status": "ok"}

def run_server():
    porta = int(os.getenv("PORT", 8080))
    print(f"\n🚀 Servidor rodando em http://0.0.0.0:{porta}")
    print(f"   Webhook URL: http://SEU-IP:{porta}/webhook")
    print(f"   Configure esse URL no painel do Z-API → Webhooks\n")
    uvicorn.run(app, host="0.0.0.0", port=porta)

# ── Modo CLI (teste local) ─────────────────────────────────────────────────────
def run_cli():
    print("\n" + "═" * 50)
    print("  VÉRTICE STUDIO — BOT DE ATENDIMENTO (teste)")
    print("  Digite 'sair' para encerrar")
    print("═" * 50 + "\n")

    telefone = "teste_local"
    abertura = gerar_resposta(telefone, "oi")
    print(f"🤖 Bot: {abertura}\n")

    while True:
        try:
            entrada = input("Você: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nEncerrando...")
            break

        if not entrada:
            continue
        if entrada.lower() == "sair":
            break

        resposta = gerar_resposta(telefone, entrada)
        print(f"\n🤖 Bot: {resposta}\n")

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if "--server" in sys.argv:
        run_server()
    else:
        run_cli()
