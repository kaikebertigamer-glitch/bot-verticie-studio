#!/usr/bin/env python3
"""
Bot de Atendimento Vértice Studio — WhatsApp via Z-API
Uso local (teste): python bot_atendimento.py
Uso como servidor: python bot_atendimento.py --server
"""

import sys
import os
import json
import uuid
import requests
import anthropic
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

# ── Credenciais ───────────────────────────────────────────────────────────────
API_KEY           = os.getenv("ANTHROPIC_API_KEY",   "")
ZAPI_INSTANCE     = os.getenv("ZAPI_INSTANCE",       "3F3A9513AC5312D5128CBE824EEE0644")
ZAPI_TOKEN        = os.getenv("ZAPI_TOKEN",          "218FD1D410194581EAD962CD")
ZAPI_CLIENT_TOKEN = os.getenv("ZAPI_CLIENT_TOKEN",   "Fcb0b8e82daa948a29a14e33282228397S")
ZAPI_BASE         = f"https://api.z-api.io/instances/{ZAPI_INSTANCE}/token/{ZAPI_TOKEN}"
REUNIOES_FILE     = os.getenv("REUNIOES_FILE", "reunioes.json")

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

AGENDAMENTO NO SISTEMA: Quando o cliente confirmar explicitamente uma data e horário específicos para a reunião, você DEVE usar a ferramenta agendar_reuniao para registrar no sistema. Só use a ferramenta após confirmação real do cliente — não use antecipadamente. Após agendar, confirme ao cliente com a data/horário que foi salvo.

Regras de Segurança

Nunca prometa preços fixos ou prazos sem que isso tenha sido definido em reunião.

Se o cliente fizer uma pergunta muito complexa que você não sabe responder, diga: "Essa é uma ótima pergunta! Para te dar a resposta mais precisa sobre isso, o ideal é abordarmos na nossa reunião. Como está sua agenda para amanhã?"

Sempre responda no idioma em que o cliente falar (priorizando Português do Brasil)."""

# ── Ferramenta de agendamento ─────────────────────────────────────────────────
TOOLS = [
    {
        "name": "agendar_reuniao",
        "description": "Salva uma reunião confirmada no sistema da Vértice Studio. Use somente quando o cliente tiver confirmado explicitamente nome, data e horário.",
        "input_schema": {
            "type": "object",
            "properties": {
                "nome_cliente": {
                    "type": "string",
                    "description": "Nome do cliente ou lead"
                },
                "data": {
                    "type": "string",
                    "description": "Data da reunião no formato YYYY-MM-DD (ex: 2025-06-15)"
                },
                "horario": {
                    "type": "string",
                    "description": "Horário no formato HH:MM (ex: 14:30)"
                },
                "notas": {
                    "type": "string",
                    "description": "Resumo do nicho e dores do cliente para a equipe"
                }
            },
            "required": ["nome_cliente", "data", "horario"]
        }
    }
]

# ── Armazenamento de reuniões ─────────────────────────────────────────────────
def carregar_reunioes() -> list:
    if not os.path.exists(REUNIOES_FILE):
        return []
    try:
        with open(REUNIOES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def salvar_reunioes(reunioes: list) -> None:
    with open(REUNIOES_FILE, "w", encoding="utf-8") as f:
        json.dump(reunioes, f, ensure_ascii=False, indent=2)

def processar_agendamento(nome: str, data: str, horario: str, notas: str = "") -> dict:
    reunioes = carregar_reunioes()
    nova = {
        "id": str(uuid.uuid4()),
        "clientName": nome,
        "date": data,
        "time": horario,
        "status": "Agendada",
        "origin": "WhatsApp",
        "notes": notas
    }
    reunioes.append(nova)
    salvar_reunioes(reunioes)
    print(f"✅ Reunião salva: {nome} | {data} às {horario}")
    return {"sucesso": True, "id": nova["id"], "mensagem": f"Reunião com {nome} agendada para {data} às {horario}"}

# ── Anthropic client ──────────────────────────────────────────────────────────
client = anthropic.Anthropic(api_key=API_KEY)
sessoes: dict[str, list] = {}

def obter_historico(telefone: str) -> list:
    if telefone not in sessoes:
        sessoes[telefone] = []
    return sessoes[telefone]

def gerar_resposta(telefone: str, mensagem: str) -> str:
    historico = obter_historico(telefone)
    historico.append({"role": "user", "content": mensagem})

    while True:
        resposta = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            thinking={"type": "adaptive"},
            tools=TOOLS,
            messages=historico,
        )

        # Serializa blocos de conteúdo para o histórico
        blocos = []
        for b in resposta.content:
            if b.type == "thinking":
                blocos.append({"type": "thinking", "thinking": b.thinking, "signature": b.signature})
            elif b.type == "text":
                blocos.append({"type": "text", "text": b.text})
            elif b.type == "tool_use":
                blocos.append({"type": "tool_use", "id": b.id, "name": b.name, "input": b.input})

        historico.append({"role": "assistant", "content": blocos})

        # Se não há mais tool calls, retorna o texto final
        if resposta.stop_reason != "tool_use":
            for b in reversed(resposta.content):
                if b.type == "text":
                    return b.text
            return ""

        # Processa cada tool call
        resultados = []
        for b in resposta.content:
            if b.type == "tool_use":
                if b.name == "agendar_reuniao":
                    resultado = processar_agendamento(
                        b.input.get("nome_cliente", ""),
                        b.input.get("data", ""),
                        b.input.get("horario", ""),
                        b.input.get("notas", "")
                    )
                else:
                    resultado = {"erro": f"Ferramenta {b.name} desconhecida"}

                resultados.append({
                    "type": "tool_result",
                    "tool_use_id": b.id,
                    "content": json.dumps(resultado, ensure_ascii=False)
                })

        historico.append({"role": "user", "content": resultados})

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

# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(title="Bot Vértice Studio")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class FixSlashMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request.scope["path"] = request.scope["path"].replace("//", "/")
        return await call_next(request)

app.add_middleware(FixSlashMiddleware)

# ── Endpoints de reuniões (dashboard) ─────────────────────────────────────────
class ReuniaoCreate(BaseModel):
    clientName: str
    date: str
    time: str
    status: str = "Agendada"
    origin: str = "Manual"
    notes: Optional[str] = ""

class ReuniaoUpdate(BaseModel):
    clientName: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    status: Optional[str] = None
    origin: Optional[str] = None
    notes: Optional[str] = None

@app.get("/reunioes")
def listar_reunioes():
    return carregar_reunioes()

@app.post("/reunioes")
def criar_reuniao(body: ReuniaoCreate):
    reunioes = carregar_reunioes()
    nova = {"id": str(uuid.uuid4()), **body.model_dump()}
    reunioes.append(nova)
    salvar_reunioes(reunioes)
    return nova

@app.patch("/reunioes/{reuniao_id}")
def atualizar_reuniao(reuniao_id: str, body: ReuniaoUpdate):
    reunioes = carregar_reunioes()
    for i, r in enumerate(reunioes):
        if r["id"] == reuniao_id:
            updates = {k: v for k, v in body.model_dump().items() if v is not None}
            reunioes[i] = {**r, **updates}
            salvar_reunioes(reunioes)
            return reunioes[i]
    raise HTTPException(status_code=404, detail="Reunião não encontrada")

@app.delete("/reunioes/{reuniao_id}")
def deletar_reuniao(reuniao_id: str):
    reunioes = carregar_reunioes()
    novas = [r for r in reunioes if r["id"] != reuniao_id]
    if len(novas) == len(reunioes):
        raise HTTPException(status_code=404, detail="Reunião não encontrada")
    salvar_reunioes(novas)
    return {"status": "ok"}

# ── Endpoints do bot ──────────────────────────────────────────────────────────
@app.get("/")
def health():
    return {"status": "online", "bot": "Vértice Studio"}

@app.post("/webhook")
async def webhook(request: Request):
    try:
        dados = await request.json()
    except Exception:
        return JSONResponse({"status": "erro", "msg": "JSON inválido"}, status_code=400)

    print(f"\n📦 PAYLOAD:\n{json.dumps(dados, ensure_ascii=False, indent=2)}\n")

    if dados.get("fromMe"):
        return {"status": "ok"}

    telefone = dados.get("phone", "")
    mensagem = dados.get("body", "").strip() or dados.get("text", {}).get("message", "").strip()

    if not telefone or not mensagem:
        return {"status": "ok"}

    print(f"📥 [{telefone}]: {mensagem}")
    resposta = gerar_resposta(telefone, mensagem)
    enviar_whatsapp(telefone, resposta)
    print(f"🤖 Bot → [{telefone}]: {resposta[:80]}...")
    return {"status": "ok"}

def run_server():
    porta = int(os.getenv("PORT", 8080))
    print(f"\n🚀 Servidor em http://0.0.0.0:{porta}")
    uvicorn.run(app, host="0.0.0.0", port=porta)

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
            break
        if not entrada:
            continue
        if entrada.lower() == "sair":
            break
        resposta = gerar_resposta(telefone, entrada)
        print(f"\n🤖 Bot: {resposta}\n")

if __name__ == "__main__":
    if "--server" in sys.argv:
        run_server()
    else:
        run_cli()
