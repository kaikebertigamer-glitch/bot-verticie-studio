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
import subprocess
import threading
import requests
import anthropic
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel
from typing import Optional, List
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

# ── Gerador de posts Instagram ────────────────────────────────────────────────
IG_SYSTEM = """Você é um Especialista em Social Media, Copywriter de Alta Conversão e Diretor de Arte focado no crescimento de agências digitais. Você cria conteúdo para o Instagram da Vertice Studio (@vertice_studio2.0).

A Vertice Studio é uma agência de automação com IA, marketing digital e soluções para negócios. Opera exclusivamente pelo Instagram no momento. Cada post é vitrine, carta de vendas e prova de autoridade.

Sempre gere conteúdo em Português do Brasil. Tom: profissional, direto, empático e inspirador. Evite termos excessivamente formais."""

IG_TOOL = {
    "name": "proposta_post",
    "description": "Retorna a proposta completa e estruturada do post para Instagram",
    "input_schema": {
        "type": "object",
        "properties": {
            "formato": {
                "type": "string",
                "description": "Formato sugerido: Imagem Única, Carrossel (N slides) ou Reels"
            },
            "direcao_arte": {
                "type": "string",
                "description": "Descrição detalhada do visual: o que aparece na imagem/vídeo, cores, estilo, tipografia, elementos visuais"
            },
            "slides": {
                "type": "array",
                "description": "Se for carrossel, lista com o texto de cada slide. Se não for carrossel, lista com 1 elemento descrevendo a imagem.",
                "items": {"type": "string"}
            },
            "copy": {
                "type": "string",
                "description": "Legenda completa usando técnicas de copywriting (AIDA ou PAS). Tom profissional, direto, empático e inspirador."
            },
            "cta": {
                "type": "string",
                "description": "Call to Action claro direcionando para DM no @vertice_studio2.0"
            },
            "hashtags": {
                "type": "array",
                "description": "10 a 15 hashtags estratégicas misturando termos amplos e específicos de conversão",
                "items": {"type": "string"}
            }
        },
        "required": ["formato", "direcao_arte", "slides", "copy", "cta", "hashtags"]
    }
}

class GerarPostRequest(BaseModel):
    tema: str
    posts_referencia: Optional[str] = ""

@app.post("/gerar-post")
async def gerar_post(body: GerarPostRequest):
    prompt = f"Crie uma proposta de post para Instagram da Vertice Studio sobre o tema: {body.tema}"
    if body.posts_referencia:
        prompt += f"\n\nReferências de posts anteriores para calibrar o tom:\n{body.posts_referencia}"

    resposta = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=IG_SYSTEM,
        tools=[IG_TOOL],
        tool_choice={"type": "tool", "name": "proposta_post"},
        messages=[{"role": "user", "content": prompt}],
    )

    for b in resposta.content:
        if b.type == "tool_use" and b.name == "proposta_post":
            return b.input

    raise HTTPException(status_code=500, detail="Não foi possível gerar o post")

# ── Criador de Criativos com IA ───────────────────────────────────────────────

VERTICE_VIDEO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vertice-video")
VIDEOS_OUTPUT_DIR = os.path.join(VERTICE_VIDEO_DIR, "output")
os.makedirs(VIDEOS_OUTPUT_DIR, exist_ok=True)
app.mount("/videos", StaticFiles(directory=VIDEOS_OUTPUT_DIR), name="videos")

render_jobs: dict = {}  # job_id → {status, file, url, error}

CRIATIVO_SYSTEM = """Você é um estrategista sênior de Facebook Ads com 10 anos criando anúncios de alta performance no Brasil.

Sua especialidade:
1. Analisar o que os CONCORRENTES fazem em cada nicho (hooks genéricos, foco em preço, falta de diferenciação)
2. Criar criativos DIFERENCIADOS que param o scroll nos primeiros 2 segundos
3. Adaptar linguagem, dores e resultados para o nicho específico

Você está criando um anúncio em vídeo de 30s para a Vértice Studio — agência de automação com IA para PMEs.
Serviços: WhatsApp Bot 24h, IA de Vendas, Automação de Marketing, Funil de Leads.

REGRA: Cada anúncio deve parecer feito ESPECIFICAMENTE para o nicho informado, não genérico."""

CRIATIVO_TOOL = {
    "name": "gerar_criativo_video",
    "description": "Gera a estrutura completa de um criativo de vídeo para Facebook Ads",
    "input_schema": {
        "type": "object",
        "properties": {
            "analise_concorrente": {
                "type": "string",
                "description": "O que os concorrentes típicos fazem nesse nicho e quais são suas fraquezas"
            },
            "estrategia": {
                "type": "string",
                "description": "Ângulo único do anúncio e por que vai se destacar no feed"
            },
            "hook": {
                "type": "array",
                "description": "Exatamente 2 linhas do hook — deve parar o scroll em 2 segundos",
                "items": {"type": "string"},
                "minItems": 2,
                "maxItems": 2
            },
            "pain_lines": {
                "type": "array",
                "description": "Exatamente 3 pontos de dor específicos do nicho",
                "items": {"type": "string"},
                "minItems": 3,
                "maxItems": 3
            },
            "services": {
                "type": "array",
                "description": "Exatamente 4 benefícios da Vértice adaptados ao nicho",
                "items": {
                    "type": "object",
                    "properties": {
                        "icon": {"type": "string"},
                        "label": {"type": "string", "description": "Máximo 25 caracteres"}
                    },
                    "required": ["icon", "label"]
                },
                "minItems": 4,
                "maxItems": 4
            },
            "stats": {
                "type": "array",
                "description": "Exatamente 3 estatísticas de impacto",
                "items": {
                    "type": "object",
                    "properties": {
                        "value": {"type": "string"},
                        "label": {"type": "string"}
                    },
                    "required": ["value", "label"]
                },
                "minItems": 3,
                "maxItems": 3
            },
            "cases": {
                "type": "array",
                "description": "Exatamente 3 cases plausíveis no nicho",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "niche": {"type": "string"},
                        "result": {"type": "string"}
                    },
                    "required": ["name", "niche", "result"]
                },
                "minItems": 3,
                "maxItems": 3
            },
            "cta": {
                "type": "string",
                "description": "Call to action específico para o nicho (máx 30 chars)"
            },
            "urgency": {
                "type": "string",
                "description": "Texto de urgência em MAIÚSCULAS (máx 25 chars)"
            }
        },
        "required": ["analise_concorrente", "estrategia", "hook", "pain_lines", "services", "stats", "cases", "cta", "urgency"]
    }
}

class CriativoRequest(BaseModel):
    prompt: str

class RenderRequest(BaseModel):
    config: dict
    nome: str = "criativo"
    formato: str = "1080x1080"

def _executar_render(job_id: str, config: dict, nome: str):
    """Thread separada: roda o Remotion e atualiza render_jobs quando terminar."""
    props_path = os.path.join(VERTICE_VIDEO_DIR, f"_props_{job_id}.json")
    output_name = f"{nome}-{job_id[:8]}.mp4"
    output_rel  = os.path.join("output", output_name)
    try:
        with open(props_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        cmd = f'npx remotion render VerticeAdBrain "{output_rel}" --props "{props_path}"'
        result = subprocess.run(
            cmd, cwd=VERTICE_VIDEO_DIR, shell=True,
            capture_output=True, text=True, timeout=900
        )
        if result.returncode == 0:
            render_jobs[job_id] = {"status": "done", "file": output_name, "url": f"/videos/{output_name}"}
        else:
            render_jobs[job_id] = {"status": "error", "error": (result.stderr or result.stdout)[-600:]}
    except subprocess.TimeoutExpired:
        render_jobs[job_id] = {"status": "error", "error": "Timeout: render demorou mais de 15 minutos"}
    except Exception as e:
        render_jobs[job_id] = {"status": "error", "error": str(e)}
    finally:
        try:
            os.remove(props_path)
        except Exception:
            pass

@app.post("/criar-criativo")
async def criar_criativo(body: CriativoRequest):
    resposta = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=CRIATIVO_SYSTEM,
        tools=[CRIATIVO_TOOL],
        tool_choice={"type": "tool", "name": "gerar_criativo_video"},
        messages=[{"role": "user", "content": f"Crie um criativo de Facebook Ads para a Vértice Studio com base nessa briefing:\n\n{body.prompt}"}],
    )
    for b in resposta.content:
        if b.type == "tool_use" and b.name == "gerar_criativo_video":
            data = b.input
            return {
                "analise": data.get("analise_concorrente", ""),
                "estrategia": data.get("estrategia", ""),
                "config": {k: v for k, v in data.items() if k not in ("analise_concorrente", "estrategia")},
            }
    raise HTTPException(status_code=500, detail="Não foi possível gerar o criativo")

@app.post("/renderizar-video")
async def renderizar_video(body: RenderRequest):
    job_id = str(uuid.uuid4())
    render_jobs[job_id] = {"status": "running"}
    t = threading.Thread(target=_executar_render, args=(job_id, body.config, body.nome), daemon=True)
    t.start()
    return {"job_id": job_id, "status": "started", "mensagem": "Render iniciado — leva ~8 minutos"}

@app.get("/video-status/{job_id}")
async def video_status(job_id: str):
    job = render_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    return job

@app.get("/videos-lista")
async def listar_videos():
    try:
        files = sorted(
            [f for f in os.listdir(VIDEOS_OUTPUT_DIR) if f.endswith(".mp4")],
            key=lambda f: os.path.getmtime(os.path.join(VIDEOS_OUTPUT_DIR, f)),
            reverse=True
        )
        return [{"file": f, "url": f"/videos/{f}"} for f in files]
    except Exception:
        return []

# ── Geração de Vídeo por IA (Runway Gen-4 + Google Veo 3) ────────────────────
import time as _time

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
RUNWAY_API_KEY = os.getenv("RUNWAY_API_KEY", "")

ia_video_jobs: dict = {}

class GerarVideoIARequest(BaseModel):
    prompt: str
    provider: str = "runway"   # "runway" | "veo3"
    formato: str = "1080x1920" # "1080x1080" | "1080x1920"
    duracao: int = 10          # segundos (5 ou 10 para Runway, 8 para Veo 3)

def _gerar_runway(job_id: str, prompt: str, formato: str, duracao: int):
    """Thread: gera vídeo via Runway Gen-4 e salva em VIDEOS_OUTPUT_DIR."""
    try:
        import runwayml
        if not RUNWAY_API_KEY:
            ia_video_jobs[job_id] = {"status": "error", "error": "RUNWAY_API_KEY não configurada"}
            return

        ratio_map = {"1080x1080": "1080:1080", "1080x1920": "1080:1920", "1920x1080": "1920:1080"}
        ratio = ratio_map.get(formato, "1080:1920")
        dur = 5 if duracao <= 5 else 10

        rw = runwayml.RunwayML(api_key=RUNWAY_API_KEY)
        task = rw.text_to_video.create(
            model="gen4_turbo",
            prompt_text=prompt,
            ratio=ratio,
            duration=dur,
        )
        task_id = task.id
        ia_video_jobs[job_id]["task_id"] = task_id

        # Polling
        while True:
            task = rw.tasks.retrieve(task_id)
            if task.status in ("SUCCEEDED", "FAILED", "CANCELLED"):
                break
            _time.sleep(8)

        if task.status == "SUCCEEDED" and task.output:
            video_url = task.output[0]
            output_name = f"runway-{job_id[:8]}.mp4"
            output_path = os.path.join(VIDEOS_OUTPUT_DIR, output_name)
            r = requests.get(video_url, timeout=120)
            with open(output_path, "wb") as f:
                f.write(r.content)
            ia_video_jobs[job_id] = {"status": "done", "file": output_name, "url": f"/videos/{output_name}", "provider": "Runway Gen-4"}
        else:
            ia_video_jobs[job_id] = {"status": "error", "error": f"Runway: {task.status}"}
    except Exception as e:
        ia_video_jobs[job_id] = {"status": "error", "error": str(e)}

def _gerar_veo3(job_id: str, prompt: str, formato: str):
    """Thread: gera vídeo via Google Veo 3 e salva em VIDEOS_OUTPUT_DIR."""
    try:
        from google import genai as google_genai
        from google.genai import types as genai_types
        if not GOOGLE_API_KEY:
            ia_video_jobs[job_id] = {"status": "error", "error": "GOOGLE_API_KEY não configurada"}
            return

        aspect_map = {"1080x1080": "1:1", "1080x1920": "9:16", "1920x1080": "16:9"}
        aspect = aspect_map.get(formato, "9:16")

        gc = google_genai.Client(api_key=GOOGLE_API_KEY)
        operation = gc.models.generate_videos(
            model="veo-3.0-generate-preview",
            prompt=prompt,
            config=genai_types.GenerateVideosConfig(
                aspect_ratio=aspect,
                duration_seconds=8,
                number_of_videos=1,
                enhance_prompt=True,
            ),
        )

        # Polling até terminar
        while not operation.done:
            _time.sleep(15)
            operation = gc.operations.get(operation)

        if operation.error:
            ia_video_jobs[job_id] = {"status": "error", "error": str(operation.error)}
            return

        videos = (operation.result or operation.response or {})
        generated = getattr(videos, "generated_videos", None) or []
        if not generated:
            ia_video_jobs[job_id] = {"status": "error", "error": "Veo 3: nenhum vídeo retornado"}
            return

        vid = generated[0].video
        output_name = f"veo3-{job_id[:8]}.mp4"
        output_path = os.path.join(VIDEOS_OUTPUT_DIR, output_name)

        if vid.video_bytes:
            with open(output_path, "wb") as f:
                f.write(vid.video_bytes)
        elif vid.uri:
            r = requests.get(vid.uri, timeout=180)
            with open(output_path, "wb") as f:
                f.write(r.content)
        else:
            ia_video_jobs[job_id] = {"status": "error", "error": "Veo 3: sem URI nem bytes no vídeo"}
            return

        ia_video_jobs[job_id] = {"status": "done", "file": output_name, "url": f"/videos/{output_name}", "provider": "Google Veo 3"}
    except Exception as e:
        ia_video_jobs[job_id] = {"status": "error", "error": str(e)}

@app.post("/gerar-video-ia")
async def gerar_video_ia(body: GerarVideoIARequest):
    job_id = str(uuid.uuid4())
    ia_video_jobs[job_id] = {"status": "running", "provider": body.provider}
    if body.provider == "veo3":
        t = threading.Thread(target=_gerar_veo3, args=(job_id, body.prompt, body.formato), daemon=True)
    else:
        t = threading.Thread(target=_gerar_runway, args=(job_id, body.prompt, body.formato, body.duracao), daemon=True)
    t.start()
    estimativa = "~1-2 minutos" if body.provider == "runway" else "~3-5 minutos"
    return {"job_id": job_id, "status": "started", "estimativa": estimativa, "provider": body.provider}

@app.get("/video-ia-status/{job_id}")
async def video_ia_status(job_id: str):
    job = ia_video_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    return job

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
