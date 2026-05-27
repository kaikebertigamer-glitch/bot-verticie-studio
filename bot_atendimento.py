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
FB_ACCESS_TOKEN   = os.getenv("FB_ACCESS_TOKEN", "")
FB_AD_ACCOUNT_ID  = os.getenv("FB_AD_ACCOUNT_ID", "")  # formato: act_XXXXXXXXX
FB_BASE           = "https://graph.facebook.com/v21.0"

MODEL = "claude-opus-4-7"

# ── System prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """# IDENTIDADE E MENTALIDADE

Você é o assistente oficial da Vértice Studio no WhatsApp — mas pensa e age como o próprio dono da empresa, com a mentalidade de Flávio Augusto: direto, confiante, focado em valor e em fechamento.

Flávio Augusto ensina: "Não existe cliente que não quer, existe cliente que ainda não viu o valor." Sua missão é fazer o cliente enxergar o valor antes de pensar no preço.

Você é um VENDEDOR-DONO. Não é atendente, não é robô. É alguém que acredita 100% no que a Vértice entrega e fala com a autoridade de quem já transformou negócios.

---

# FILOSOFIA DE VENDAS (MENTALIDADE FLÁVIO AUGUSTO)

1. GERAÇÃO DE VALOR PRIMEIRO — Antes de vender qualquer coisa, mostre o que o cliente está perdendo sem a solução. "O custo de não agir é maior que o custo de contratar."

2. DONO DO PROBLEMA — Assuma o problema do cliente como seu. "Eu entendo exatamente o que você está passando. Isso é solucionável."

3. PERGUNTAS INTELIGENTES — Faça perguntas que levam o cliente a perceber a própria dor. Não empurre — conduza.

4. URGÊNCIA REAL — Crie senso de urgência baseado em oportunidade perdida, não em pressão. "Enquanto você pensa, um concorrente já está no ar com isso."

5. FECHAMENTO DIRETO — Quando chegar a hora, peça a reunião ou o próximo passo com confiança. Sem rodeios. "Bora marcar uma call de 20 minutos ainda essa semana?"

6. OBJEÇÃO = OPORTUNIDADE — Toda objeção é uma pergunta disfarçada. "Tá caro" = "Ainda não vi o valor." Reforce o ROI, não reduza o preço.

7. PENSE COMO EMPRESÁRIO — Você quer o crescimento do cliente tanto quanto o seu. A Vértice não vende serviço, vende resultado.

---

# TOM DE VOZ

- Humano, direto e sem frescura — como um sócio falando, não um vendedor pedindo
- Mensagens CURTAS no WhatsApp. Máximo 3-4 linhas por mensagem
- Emojis estratégicos: 🚀 💡 🎯 🤝 ✅ (sem exagero)
- Zero formalidade: nada de "Prezado", "Compreendo", "Destarte"
- Se precisar explicar algo longo, quebre em 2-3 mensagens menores

---

# INFORMAÇÕES DA EMPRESA

- Nome: Vértice Studio
- O que faz: Agência de automação com IA, marketing digital e inovação para negócios
- Instagram (portfólio): @vertice_studio2.0
- Sem site oficial — direcione sempre para o Instagram

---

# FLUXO DE ATENDIMENTO

1. RECEPÇÃO — Cumprimente com energia e pergunte o nome e o negócio da pessoa
2. DIAGNÓSTICO — 1 pergunta por vez para entender a dor principal do negócio
3. ESPELHO DA DOR — Repita a dor com suas palavras para o cliente sentir que foi entendido
4. GANCHO DE VALOR — Mostre brevemente como a Vértice resolve exatamente isso
5. CALL TO ACTION — Convide para a reunião com confiança e duas opções de horário
6. AGENDAMENTO — Use a ferramenta agendar_reuniao quando o cliente confirmar data/hora

---

# FERRAMENTAS DISPONÍVEIS

Use as ferramentas nos momentos certos, sem avisar o cliente:

- agendar_reuniao: quando cliente confirmar data e hora da reunião
- qualificar_lead: use após entender o nicho e a dor — classifique o lead para a equipe
- gerar_proposta: quando o cliente pedir valores ou proposta — gere um texto personalizado e envie
- detectar_intencao: use quando a mensagem for ambígua — detecte o que o cliente realmente quer
- registrar_perfil: use quando souber nicho, orçamento ou dor principal do cliente
- escalar_humano: use quando a conversa exigir negociação avançada ou cliente VIP

---

# REGRAS

- Nunca prometa preços ou prazos fixos — isso é definido na reunião
- Perguntas complexas: "Ótima pergunta! A resposta mais precisa pra isso a gente cobre na call. Quando você tem 20 minutos essa semana?"
- Sempre responda no idioma do cliente (prioridade: português do Brasil)
- Após agendar, sempre confirme data e hora ao cliente"""

# ── Ferramentas do agente ─────────────────────────────────────────────────────
TOOLS = [
    {
        "name": "agendar_reuniao",
        "description": "Salva uma reunião confirmada no sistema da Vértice Studio. Use somente quando o cliente confirmar nome, data e horário.",
        "input_schema": {
            "type": "object",
            "properties": {
                "nome_cliente": {"type": "string", "description": "Nome do cliente"},
                "data": {"type": "string", "description": "Data no formato YYYY-MM-DD"},
                "horario": {"type": "string", "description": "Horário no formato HH:MM"},
                "notas": {"type": "string", "description": "Resumo do nicho e dores do cliente"}
            },
            "required": ["nome_cliente", "data", "horario"]
        }
    },
    {
        "name": "qualificar_lead",
        "description": "Classifica o lead com base na conversa. Use após entender o nicho e a dor do cliente. Registra o score para a equipe de vendas.",
        "input_schema": {
            "type": "object",
            "properties": {
                "nome_cliente": {"type": "string", "description": "Nome do cliente"},
                "score": {"type": "string", "enum": ["quente", "morno", "frio"], "description": "Temperatura do lead"},
                "nicho": {"type": "string", "description": "Segmento de mercado do cliente"},
                "dor_principal": {"type": "string", "description": "Principal problema que o cliente quer resolver"},
                "orcamento_estimado": {"type": "string", "description": "Estimativa de orçamento se mencionado, senão 'não informado'"},
                "observacoes": {"type": "string", "description": "Observações relevantes sobre o lead"}
            },
            "required": ["nome_cliente", "score", "nicho", "dor_principal"]
        }
    },
    {
        "name": "gerar_proposta",
        "description": "Gera uma proposta personalizada baseada no perfil do cliente e envia no WhatsApp. Use quando o cliente pedir valores ou proposta.",
        "input_schema": {
            "type": "object",
            "properties": {
                "nome_cliente": {"type": "string", "description": "Nome do cliente"},
                "nicho": {"type": "string", "description": "Segmento de mercado"},
                "dor_principal": {"type": "string", "description": "Problema principal a resolver"},
                "solucoes_sugeridas": {"type": "string", "description": "Serviços da Vértice relevantes para o caso"},
                "telefone": {"type": "string", "description": "Telefone do cliente para enviar a proposta"}
            },
            "required": ["nome_cliente", "nicho", "dor_principal", "solucoes_sugeridas", "telefone"]
        }
    },
    {
        "name": "detectar_intencao",
        "description": "Detecta a intenção real do cliente quando a mensagem for ambígua. Ajuda o agente a escolher a melhor abordagem.",
        "input_schema": {
            "type": "object",
            "properties": {
                "mensagem": {"type": "string", "description": "Mensagem do cliente a ser analisada"},
                "intencao": {"type": "string", "enum": ["preco", "portfolio", "reuniao", "suporte", "parceria", "curiosidade", "outro"], "description": "Intenção detectada"},
                "confianca": {"type": "string", "enum": ["alta", "media", "baixa"], "description": "Nível de confiança na detecção"}
            },
            "required": ["mensagem", "intencao", "confianca"]
        }
    },
    {
        "name": "registrar_perfil",
        "description": "Salva o perfil completo do cliente para contextualizar futuras interações e passar para a equipe.",
        "input_schema": {
            "type": "object",
            "properties": {
                "nome_cliente": {"type": "string"},
                "telefone": {"type": "string"},
                "nicho": {"type": "string"},
                "empresa": {"type": "string", "description": "Nome da empresa se informado"},
                "dor_principal": {"type": "string"},
                "orcamento": {"type": "string"},
                "urgencia": {"type": "string", "enum": ["imediata", "curto_prazo", "longo_prazo", "explorando"]}
            },
            "required": ["nome_cliente", "telefone", "nicho", "dor_principal"]
        }
    },
    {
        "name": "escalar_humano",
        "description": "Sinaliza que a conversa precisa de atendimento humano — cliente VIP, negociação complexa ou situação sensível.",
        "input_schema": {
            "type": "object",
            "properties": {
                "nome_cliente": {"type": "string"},
                "telefone": {"type": "string"},
                "motivo": {"type": "string", "description": "Por que precisa de atendimento humano"},
                "urgencia": {"type": "string", "enum": ["alta", "media", "baixa"]}
            },
            "required": ["nome_cliente", "telefone", "motivo", "urgencia"]
        }
    }
]

# ── Armazenamento de dados ────────────────────────────────────────────────────
LEADS_FILE    = os.getenv("LEADS_FILE", "leads.json")
PERFIS_FILE   = os.getenv("PERFIS_FILE", "perfis.json")
ESCALAS_FILE  = os.getenv("ESCALAS_FILE", "escalas.json")

def _carregar_json(path: str) -> list:
    if not os.path.exists(path): return []
    try:
        with open(path, "r", encoding="utf-8") as f: return json.load(f)
    except Exception: return []

def _salvar_json(path: str, dados: list) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

def processar_qualificacao(dados: dict) -> dict:
    leads = _carregar_json(LEADS_FILE)
    registro = {"id": str(uuid.uuid4()), **dados, "criado_em": str(__import__("datetime").datetime.now())}
    leads.append(registro)
    _salvar_json(LEADS_FILE, leads)
    print(f"🎯 Lead qualificado: {dados.get('nome_cliente')} | {dados.get('score').upper()}")
    return {"sucesso": True, "score": dados.get("score"), "mensagem": f"Lead {dados.get('nome_cliente')} classificado como {dados.get('score')}"}

def processar_proposta(dados: dict) -> dict:
    client_interno = anthropic.Anthropic(api_key=API_KEY)
    msg = client_interno.messages.create(
        model=MODEL,
        max_tokens=800,
        system="Você é um copywriter especialista em propostas comerciais para agências digitais. Escreva propostas curtas, diretas e persuasivas no estilo WhatsApp — sem tabelas, sem jargões. Máximo 15 linhas.",
        messages=[{"role": "user", "content": f"Crie uma proposta personalizada para:\nCliente: {dados['nome_cliente']}\nNicho: {dados['nicho']}\nDor: {dados['dor_principal']}\nSoluções: {dados['solucoes_sugeridas']}\n\nA proposta deve ter: abertura com espelho da dor, solução específica da Vértice, resultado esperado, e CTA para fechar reunião."}]
    )
    texto_proposta = msg.content[0].text
    enviar_whatsapp(dados["telefone"], texto_proposta)
    return {"sucesso": True, "mensagem": "Proposta enviada via WhatsApp", "proposta": texto_proposta}

def processar_perfil(dados: dict) -> dict:
    perfis = _carregar_json(PERFIS_FILE)
    registro = {"id": str(uuid.uuid4()), **dados, "criado_em": str(__import__("datetime").datetime.now())}
    perfis.append(registro)
    _salvar_json(PERFIS_FILE, perfis)
    print(f"👤 Perfil registrado: {dados.get('nome_cliente')}")
    return {"sucesso": True, "mensagem": f"Perfil de {dados.get('nome_cliente')} salvo"}

def processar_escala(dados: dict) -> dict:
    escalas = _carregar_json(ESCALAS_FILE)
    registro = {"id": str(uuid.uuid4()), **dados, "criado_em": str(__import__("datetime").datetime.now())}
    escalas.append(registro)
    _salvar_json(ESCALAS_FILE, escalas)
    print(f"🚨 ESCALA HUMANO: {dados.get('nome_cliente')} | {dados.get('urgencia').upper()} | {dados.get('motivo')}")
    return {"sucesso": True, "mensagem": f"Conversa de {dados.get('nome_cliente')} escalada para atendimento humano"}

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
                inp = b.input
                if b.name == "agendar_reuniao":
                    resultado = processar_agendamento(
                        inp.get("nome_cliente", ""), inp.get("data", ""),
                        inp.get("horario", ""), inp.get("notas", "")
                    )
                elif b.name == "qualificar_lead":
                    resultado = processar_qualificacao(inp)
                elif b.name == "gerar_proposta":
                    resultado = processar_proposta(inp)
                elif b.name == "detectar_intencao":
                    print(f"🔍 Intenção detectada: {inp.get('intencao')} (confiança: {inp.get('confianca')})")
                    resultado = {"intencao": inp.get("intencao"), "confianca": inp.get("confianca")}
                elif b.name == "registrar_perfil":
                    resultado = processar_perfil(inp)
                elif b.name == "escalar_humano":
                    resultado = processar_escala(inp)
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

# ── Gerador de Prompts ────────────────────────────────────────────────────────
PROMPT_ENGINEER_SYSTEM = """Você é o melhor prompt engineer do mundo para geração de vídeos com IA e copy para anúncios.
Você estudou cada detalhe dos modelos Runway Gen-4, Google Veo 3 e das melhores técnicas de copywriting para Facebook/Instagram Ads.

Suas especialidades:
- Runway Gen-4: cinematografia, movimentos de câmera, descrições de cenas físicas e realistas, timing
- Google Veo 3: narrativa visual, transições, qualidade cinematográfica 4K, áudio diegético
- Copy de Anúncio: hook de 3 segundos, dor, solução, prova social, CTA irresistível

Você sempre pensa em anúncios que PARAM O SCROLL, geram DESEJO e CONVERTEM."""

class GerarPromptRequest(BaseModel):
    objetivo: str
    nicho: str = ""
    publico: str = ""

@app.post("/gerar-prompt")
async def gerar_prompt(body: GerarPromptRequest):
    client = anthropic.Anthropic(api_key=API_KEY)
    contexto = body.objetivo
    if body.nicho:
        contexto += f" | Nicho: {body.nicho}"
    if body.publico:
        contexto += f" | Público: {body.publico}"

    msg = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        system=PROMPT_ENGINEER_SYSTEM,
        messages=[{
            "role": "user",
            "content": f"""Gere 3 prompts otimizados para este anúncio:
OBJETIVO: {contexto}

Retorne APENAS JSON válido neste formato:
{{
  "runway": "prompt completo otimizado para Runway Gen-4 em inglês, 2-4 frases descrevendo a cena, câmera, iluminação e movimento",
  "veo3": "prompt completo otimizado para Google Veo 3 em inglês, cinematográfico, com áudio ambiente sugerido, 3-5 frases",
  "copy": "copy completo em português para o anúncio: hook de 3s / problema / solução / prova social / CTA. Use quebras de linha entre cada parte.",
  "dica_runway": "dica específica de 1 frase para maximizar esse prompt no Runway",
  "dica_veo3": "dica específica de 1 frase para maximizar esse prompt no Veo 3",
  "dica_copy": "dica específica de 1 frase sobre o ângulo psicológico usado"
}}"""
        }]
    )

    raw = msg.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        return json.loads(raw.strip())
    except Exception:
        return {"erro": "Falha ao parsear resposta", "raw": raw}

# ── Facebook Ads ──────────────────────────────────────────────────────────────
@app.get("/facebook/status")
async def facebook_status():
    return {
        "configurado": bool(FB_ACCESS_TOKEN and FB_AD_ACCOUNT_ID),
        "tem_token": bool(FB_ACCESS_TOKEN),
        "tem_conta": bool(FB_AD_ACCOUNT_ID),
    }

@app.get("/facebook/overview")
async def facebook_overview(periodo: str = "last_30d"):
    if not FB_ACCESS_TOKEN or not FB_AD_ACCOUNT_ID:
        raise HTTPException(400, "Facebook não configurado. Defina FB_ACCESS_TOKEN e FB_AD_ACCOUNT_ID no Railway.")
    r = requests.get(f"{FB_BASE}/{FB_AD_ACCOUNT_ID}/insights", params={
        "fields": "spend,impressions,clicks,ctr,cpc,reach,actions,action_values",
        "date_preset": periodo,
        "access_token": FB_ACCESS_TOKEN,
    }, timeout=15)
    if not r.ok:
        raise HTTPException(r.status_code, r.json().get("error", {}).get("message", "Erro Facebook API"))
    data = r.json().get("data", [])
    return data[0] if data else {}

@app.get("/facebook/campanhas")
async def facebook_campanhas(periodo: str = "last_30d"):
    if not FB_ACCESS_TOKEN or not FB_AD_ACCOUNT_ID:
        raise HTTPException(400, "Facebook não configurado.")
    r = requests.get(f"{FB_BASE}/{FB_AD_ACCOUNT_ID}/campaigns", params={
        "fields": "name,status,objective,daily_budget,lifetime_budget,budget_remaining,start_time,stop_time",
        "access_token": FB_ACCESS_TOKEN,
        "limit": 25,
    }, timeout=15)
    if not r.ok:
        raise HTTPException(r.status_code, r.json().get("error", {}).get("message", "Erro Facebook API"))
    campanhas = r.json().get("data", [])
    for camp in campanhas:
        try:
            ins = requests.get(f"{FB_BASE}/{camp['id']}/insights", params={
                "fields": "spend,impressions,clicks,ctr,cpc,reach,actions",
                "date_preset": periodo,
                "access_token": FB_ACCESS_TOKEN,
            }, timeout=10)
            camp["insights"] = ins.json().get("data", [{}])[0] if ins.ok else {}
        except Exception:
            camp["insights"] = {}
    return campanhas

@app.get("/facebook/adsets/{campaign_id}")
async def facebook_adsets(campaign_id: str, periodo: str = "last_30d"):
    if not FB_ACCESS_TOKEN:
        raise HTTPException(400, "Facebook não configurado.")
    r = requests.get(f"{FB_BASE}/{campaign_id}/adsets", params={
        "fields": "name,status,daily_budget,targeting",
        "access_token": FB_ACCESS_TOKEN,
        "limit": 20,
    }, timeout=15)
    if not r.ok:
        raise HTTPException(r.status_code, "Erro ao buscar conjuntos de anúncios")
    adsets = r.json().get("data", [])
    for ads in adsets:
        try:
            ins = requests.get(f"{FB_BASE}/{ads['id']}/insights", params={
                "fields": "spend,impressions,clicks,ctr,cpc",
                "date_preset": periodo,
                "access_token": FB_ACCESS_TOKEN,
            }, timeout=10)
            ads["insights"] = ins.json().get("data", [{}])[0] if ins.ok else {}
        except Exception:
            ads["insights"] = {}
    return adsets

# ── Facebook Ads — IA Skills ───────────────────────────────────────────────────
_SKILL_SISTEMAS = {
    "analisar": """Você é um analista sênior de Facebook Ads com 10 anos de experiência gerindo contas de alto volume.
Analise os dados fornecidos e entregue:
1. PANORAMA GERAL — avaliação objetiva do desempenho da conta
2. DESTAQUES POSITIVOS — campanhas e métricas que estão acima do esperado
3. PONTOS DE ATENÇÃO — campanhas problemáticas com diagnóstico do motivo
4. MÉTRICAS CRÍTICAS — CTR abaixo de 1%, CPC acima da média, alcance estagnado
5. TOP 3 INSIGHTS ACIONÁVEIS — o que fazer nos próximos 7 dias

Use os números reais dos dados. Seja direto, específico e sem enrolação.
Responda em português do Brasil.""",

    "otimizar": """Você é um especialista em otimização de budget de Facebook Ads, focado em maximizar ROAS.
Com base nos dados fornecidos entregue:
1. DIAGNÓSTICO DE VERBA — onde o dinheiro está sendo bem e mal utilizado
2. CORTES RECOMENDADOS — campanhas para pausar ou reduzir budget (com % sugerida)
3. AUMENTOS RECOMENDADOS — campanhas para escalar (com % sugerida e motivo)
4. REDISTRIBUIÇÃO PROPOSTA — tabela mostrando antes/depois do budget por campanha
5. IMPACTO ESTIMADO — projeção de melhoria em cliques/conversões com as mudanças

Seja específico com números e porcentagens. Justifique cada decisão com dados.
Responda em português do Brasil.""",

    "copy": """Você é o melhor copywriter de Facebook Ads do Brasil, especialista em copy de resposta direta.
Com base nos dados das campanhas fornecidas, entregue:
1. PADRÃO DAS MELHORES CAMPANHAS — o que têm em comum as de maior CTR
2. 3 HEADLINES (máx 40 chars cada) — diretos, com benefício claro ou curiosidade
3. 3 TEXTOS PRINCIPAIS (primary text) — hook forte, dor, solução, prova, CTA
4. 2 DESCRIÇÕES (máx 25 chars cada) — complementam o headline
5. CTAs RECOMENDADOS — qual botão usar para cada objetivo

Use gatilhos: urgência, escassez, prova social, benefício específico, medo de perder.
Se não houver campanhas suficientes, crie copy baseado no nicho/objetivo identificado.
Responda em português do Brasil.""",

    "diagnostico": """Você é um auditor express de campanhas de Facebook Ads. Seja rápido, visual e objetivo.
Entregue o diagnóstico em formato de dashboard textual:

🏥 STATUS GERAL: [🟢 Saudável / 🟡 Atenção necessária / 🔴 Crítico — ação urgente]

🚨 ALERTAS CRÍTICOS (ação nas próximas 24h):
— liste cada problema grave

⚠️ AVISOS (resolver essa semana):
— liste cada ponto de melhoria

✅ O QUE ESTÁ FUNCIONANDO:
— liste os pontos positivos

📋 PLANO DE 48H — 3 ações prioritárias com responsável e prazo:
1.
2.
3.

Seja direto. Cada item em uma linha. Emojis para facilitar leitura visual.
Responda em português do Brasil.""",
}

class FbAgenteRequest(BaseModel):
    skill: str
    campanhas: list = []
    overview: dict = {}

@app.post("/facebook/agente")
async def facebook_agente(body: FbAgenteRequest):
    if body.skill not in _SKILL_SISTEMAS:
        raise HTTPException(400, "Skill inválida")
    client = anthropic.Anthropic(api_key=API_KEY)
    dados_str = json.dumps({"overview": body.overview, "campanhas": body.campanhas}, ensure_ascii=False, indent=2)
    msg = client.messages.create(
        model=MODEL,
        max_tokens=1800,
        system=_SKILL_SISTEMAS[body.skill],
        messages=[{"role": "user", "content": f"Analise estes dados da conta de Facebook Ads:\n\n{dados_str}"}],
    )
    return {"resultado": msg.content[0].text, "skill": body.skill}

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
