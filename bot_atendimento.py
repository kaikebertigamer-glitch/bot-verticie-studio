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
CLIENTES_FILE = os.getenv("CLIENTES_FILE", "clientes.json")
CONTEUDO_FILE = os.getenv("CONTEUDO_FILE", "conteudo.json")
CONV_FILE     = os.getenv("CONV_FILE", "conversas.json")
OWNER_PHONE   = os.getenv("OWNER_PHONE", "")

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
    if OWNER_PHONE:
        urgencia = dados.get("urgencia", "").upper()
        emoji = "🔴" if urgencia == "ALTA" else "🟡" if urgencia == "MEDIA" else "🟢"
        alerta = (f"{emoji} *LEAD PARA ATENDIMENTO HUMANO*\n\n"
                  f"👤 *{dados.get('nome_cliente')}*\n"
                  f"📞 {dados.get('telefone')}\n"
                  f"⚡ Urgência: {urgencia}\n"
                  f"📝 {dados.get('motivo')}\n\n"
                  f"Responda o quanto antes! 🚀")
        enviar_whatsapp(OWNER_PHONE, alerta)
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

# ── CRM de Leads ─────────────────────────────────────────────────────────────
import datetime as _dt

class LeadUpdate(BaseModel):
    estagio: Optional[str] = None
    score: Optional[str] = None
    notas: Optional[str] = None
    telefone: Optional[str] = None

@app.get("/leads")
async def listar_leads(score: Optional[str] = None, estagio: Optional[str] = None):
    leads = _carregar_json(LEADS_FILE)
    if score: leads = [l for l in leads if l.get("score") == score]
    if estagio: leads = [l for l in leads if l.get("estagio", "novo") == estagio]
    return sorted(leads, key=lambda l: l.get("criado_em", ""), reverse=True)

@app.put("/leads/{lead_id}")
async def atualizar_lead(lead_id: str, body: LeadUpdate):
    leads = _carregar_json(LEADS_FILE)
    for l in leads:
        if l["id"] == lead_id:
            if body.estagio is not None: l["estagio"] = body.estagio
            if body.score is not None: l["score"] = body.score
            if body.notas is not None: l["notas"] = body.notas
            if body.telefone is not None: l["telefone"] = body.telefone
            l["atualizado_em"] = str(_dt.datetime.now())
            break
    _salvar_json(LEADS_FILE, leads)
    return {"sucesso": True}

@app.delete("/leads/{lead_id}")
async def deletar_lead(lead_id: str):
    leads = [l for l in _carregar_json(LEADS_FILE) if l["id"] != lead_id]
    _salvar_json(LEADS_FILE, leads)
    return {"sucesso": True}

@app.get("/leads/stats")
async def stats_leads():
    leads = _carregar_json(LEADS_FILE)
    hoje = _dt.date.today().isoformat()
    semana = (_dt.date.today() - _dt.timedelta(days=7)).isoformat()
    return {
        "total": len(leads),
        "quente": sum(1 for l in leads if l.get("score") == "quente"),
        "morno": sum(1 for l in leads if l.get("score") == "morno"),
        "frio": sum(1 for l in leads if l.get("score") == "frio"),
        "esta_semana": sum(1 for l in leads if l.get("criado_em", "")[:10] >= semana),
        "por_estagio": {
            e: sum(1 for l in leads if l.get("estagio", "novo") == e)
            for e in ["novo", "qualificado", "proposta", "reuniao", "fechado", "perdido"]
        }
    }

# ── Clientes Ativos ───────────────────────────────────────────────────────────
class ClienteCreate(BaseModel):
    nome: str
    empresa: Optional[str] = ""
    nicho: Optional[str] = ""
    telefone: Optional[str] = ""
    email: Optional[str] = ""
    plano: Optional[str] = ""
    valor_mensal: Optional[float] = 0
    data_inicio: Optional[str] = ""
    status: Optional[str] = "ativo"
    notas: Optional[str] = ""

class ClienteUpdate(BaseModel):
    nome: Optional[str] = None
    empresa: Optional[str] = None
    nicho: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None
    plano: Optional[str] = None
    valor_mensal: Optional[float] = None
    data_inicio: Optional[str] = None
    status: Optional[str] = None
    notas: Optional[str] = None

@app.get("/clientes-ativos")
async def listar_clientes(status: Optional[str] = None):
    clientes = _carregar_json(CLIENTES_FILE)
    if status: clientes = [c for c in clientes if c.get("status") == status]
    return sorted(clientes, key=lambda c: c.get("nome", ""))

@app.post("/clientes-ativos")
async def criar_cliente(body: ClienteCreate):
    clientes = _carregar_json(CLIENTES_FILE)
    novo = {"id": str(uuid.uuid4()), "criado_em": str(_dt.datetime.now()), **body.dict()}
    clientes.append(novo)
    _salvar_json(CLIENTES_FILE, clientes)
    return novo

@app.put("/clientes-ativos/{cliente_id}")
async def atualizar_cliente(cliente_id: str, body: ClienteUpdate):
    clientes = _carregar_json(CLIENTES_FILE)
    for c in clientes:
        if c["id"] == cliente_id:
            for k, v in body.dict(exclude_none=True).items():
                c[k] = v
            c["atualizado_em"] = str(_dt.datetime.now())
            break
    _salvar_json(CLIENTES_FILE, clientes)
    return {"sucesso": True}

@app.delete("/clientes-ativos/{cliente_id}")
async def deletar_cliente(cliente_id: str):
    clientes = [c for c in _carregar_json(CLIENTES_FILE) if c["id"] != cliente_id]
    _salvar_json(CLIENTES_FILE, clientes)
    return {"sucesso": True}

# ── Calendário de Conteúdo ────────────────────────────────────────────────────
class ConteudoCreate(BaseModel):
    titulo: str
    tipo: Optional[str] = "post"
    data_publicacao: Optional[str] = ""
    status: Optional[str] = "rascunho"
    caption: Optional[str] = ""
    hashtags: Optional[str] = ""
    cliente: Optional[str] = ""
    observacoes: Optional[str] = ""

class ConteudoUpdate(BaseModel):
    titulo: Optional[str] = None
    tipo: Optional[str] = None
    data_publicacao: Optional[str] = None
    status: Optional[str] = None
    caption: Optional[str] = None
    hashtags: Optional[str] = None
    cliente: Optional[str] = None
    observacoes: Optional[str] = None

@app.get("/conteudo")
async def listar_conteudo(status: Optional[str] = None, mes: Optional[str] = None):
    items = _carregar_json(CONTEUDO_FILE)
    if status: items = [i for i in items if i.get("status") == status]
    if mes: items = [i for i in items if i.get("data_publicacao", "")[:7] == mes]
    return sorted(items, key=lambda i: i.get("data_publicacao", ""))

@app.post("/conteudo")
async def criar_conteudo(body: ConteudoCreate):
    items = _carregar_json(CONTEUDO_FILE)
    novo = {"id": str(uuid.uuid4()), "criado_em": str(_dt.datetime.now()), **body.dict()}
    items.append(novo)
    _salvar_json(CONTEUDO_FILE, items)
    return novo

@app.put("/conteudo/{item_id}")
async def atualizar_conteudo(item_id: str, body: ConteudoUpdate):
    items = _carregar_json(CONTEUDO_FILE)
    for i in items:
        if i["id"] == item_id:
            for k, v in body.dict(exclude_none=True).items():
                i[k] = v
            break
    _salvar_json(CONTEUDO_FILE, items)
    return {"sucesso": True}

@app.delete("/conteudo/{item_id}")
async def deletar_conteudo(item_id: str):
    items = [i for i in _carregar_json(CONTEUDO_FILE) if i["id"] != item_id]
    _salvar_json(CONTEUDO_FILE, items)
    return {"sucesso": True}

# ── Follow-up Automático ──────────────────────────────────────────────────────
@app.post("/follow-up")
async def executar_followup():
    leads = _carregar_json(LEADS_FILE)
    limite = (_dt.date.today() - _dt.timedelta(days=3)).isoformat()
    frios = [l for l in leads if l.get("score") in ("morno", "quente")
             and l.get("estagio", "novo") not in ("fechado", "perdido", "reuniao")
             and l.get("criado_em", "")[:10] <= limite
             and l.get("telefone")]
    if not frios:
        return {"enviados": 0, "mensagem": "Nenhum lead elegível para follow-up"}

    client_interno = anthropic.Anthropic(api_key=API_KEY)
    enviados = []
    for lead in frios[:5]:
        msg_obj = client_interno.messages.create(
            model=MODEL, max_tokens=300,
            system="Você é um vendedor da Vértice Studio com a mentalidade de Flávio Augusto. Escreva uma mensagem curta de reativação de WhatsApp (máx 4 linhas) para um lead que não respondeu há alguns dias. Seja direto, humano, sem soar desesperado. Crie senso de oportunidade.",
            messages=[{"role": "user", "content": f"Lead: {lead.get('nome_cliente')} | Nicho: {lead.get('nicho')} | Dor: {lead.get('dor_principal')}"}]
        )
        texto = msg_obj.content[0].text
        enviar_whatsapp(lead["telefone"], texto)
        lead["ultimo_followup"] = str(_dt.datetime.now())
        enviados.append({"lead": lead.get("nome_cliente"), "telefone": lead.get("telefone")})

    _salvar_json(LEADS_FILE, leads)
    return {"enviados": len(enviados), "leads": enviados}

# ── Relatório Semanal ─────────────────────────────────────────────────────────
@app.get("/relatorio-semanal")
async def relatorio_semanal(enviar_whatsapp_owner: bool = False):
    leads = _carregar_json(LEADS_FILE)
    clientes = _carregar_json(CLIENTES_FILE)
    reunioes = carregar_reunioes()
    semana = (_dt.date.today() - _dt.timedelta(days=7)).isoformat()

    leads_semana = [l for l in leads if l.get("criado_em", "")[:10] >= semana]
    reunioes_semana = [r for r in reunioes if r.get("date", "")[:10] >= semana]
    clientes_ativos = [c for c in clientes if c.get("status") == "ativo"]
    mrr = sum(c.get("valor_mensal", 0) for c in clientes_ativos)

    dados = {
        "periodo": f"{semana} a {_dt.date.today().isoformat()}",
        "leads_novos": len(leads_semana),
        "leads_quentes": sum(1 for l in leads_semana if l.get("score") == "quente"),
        "reunioes_agendadas": len(reunioes_semana),
        "clientes_ativos": len(clientes_ativos),
        "mrr": mrr,
        "pipeline": {e: sum(1 for l in leads if l.get("estagio","novo")==e) for e in ["novo","qualificado","proposta","reuniao","fechado"]},
    }

    client_interno = anthropic.Anthropic(api_key=API_KEY)
    msg_obj = client_interno.messages.create(
        model=MODEL, max_tokens=1200,
        system="Você é o analista de negócios da Vértice Studio com mentalidade de Flávio Augusto. Gere um relatório semanal executivo, direto e motivador. Use emojis, seja objetivo, destaque conquistas e aponte o foco da próxima semana.",
        messages=[{"role": "user", "content": f"Dados da semana:\n{json.dumps(dados, ensure_ascii=False, indent=2)}\n\nGere o relatório semanal completo."}]
    )
    relatorio_texto = msg_obj.content[0].text

    if enviar_whatsapp_owner and OWNER_PHONE:
        enviar_whatsapp(OWNER_PHONE, relatorio_texto)

    return {"relatorio": relatorio_texto, "dados": dados}

# ── Endpoints do bot ──────────────────────────────────────────────────────────
class ChatMsg(BaseModel):
    message: str
    session_id: str = "widget"
    history: list = []

CHAT_SYSTEM = """Você é o assistente virtual da Vértice Studio — agência de automação com IA.

Seja direto, amigável e focado em valor. Responda em português brasileiro. Máximo 3 parágrafos curtos.

Sobre a Vértice Studio:
- Automação com IA para negócios: chatbots WhatsApp, gestão de tráfego pago, criativos automatizados
- Atende PMEs que querem crescer mais rápido
- Planos a partir de R$ 1.500/mês
- Para orçamento: convide para uma call gratuita de 20 minutos

Se o visitante perguntar sobre preços, convide para falar com a equipe no WhatsApp: (11) 99999-9999
Nunca prometa preços fixos ou prazos — isso é definido na reunião."""

@app.post("/chat")
async def chat_widget(body: ChatMsg):
    """Endpoint para o widget de chat embeddável."""
    client = anthropic.Anthropic(api_key=API_KEY)
    messages = []
    for m in (body.history or [])[-10:]:
        if isinstance(m, dict) and m.get("role") in ("user", "assistant"):
            messages.append({"role": m["role"], "content": m["content"]})
    if not messages or messages[-1].get("role") != "user":
        messages.append({"role": "user", "content": body.message})
    elif messages[-1].get("content") != body.message:
        messages.append({"role": "user", "content": body.message})
    try:
        r = client.messages.create(
            model=MODEL,
            max_tokens=512,
            system=CHAT_SYSTEM,
            messages=messages,
        )
        reply = r.content[0].text if r.content else "Desculpe, tente novamente."
    except Exception as e:
        reply = "Ops, tive um problema técnico. Fale diretamente no WhatsApp! 💬"
    return {"reply": reply, "session_id": body.session_id}

class PropostaInput(BaseModel):
    nome_cliente: str
    empresa: Optional[str] = ""
    nicho: str
    dor_principal: str
    orcamento: Optional[str] = "a definir"
    servicos: Optional[str] = ""

@app.post("/gerar-proposta-pdf")
async def gerar_proposta_pdf(body: PropostaInput):
    """Gera PDF de proposta comercial com Claude e retorna como download."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.colors import HexColor, white, black
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        import io
        from fastapi.responses import StreamingResponse
    except ImportError:
        raise HTTPException(status_code=500, detail="reportlab não instalado. Execute: pip install reportlab")

    # Gerar conteúdo textual com Claude
    client = anthropic.Anthropic(api_key=API_KEY)
    prompt = f"""Crie uma proposta comercial profissional e persuasiva para:
Cliente: {body.nome_cliente} ({body.empresa})
Nicho: {body.nicho}
Dor principal: {body.dor_principal}
Orçamento: {body.orcamento}
Serviços de interesse: {body.servicos or 'a definir'}

A proposta deve ter:
1. Diagnóstico do negócio (2-3 parágrafos sobre a situação e oportunidade)
2. Nossa solução (serviços específicos para o nicho, com descrição clara)
3. Resultados esperados (KPIs realistas e timeline)
4. Investimento (mencione o orçamento de forma consultiva, nunca como limitação)
5. Próximos passos (CTA para fechar)

Tom: Flávio Augusto — direto, com autoridade, focado em ROI. Seja específico para o nicho {body.nicho}."""

    r = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )
    texto = r.content[0].text

    # Montar PDF
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)

    GOLD = HexColor('#e8c97a')
    DARK = HexColor('#0f1117')
    SLATE = HexColor('#94a3b8')

    styles = getSampleStyleSheet()
    s_title = ParagraphStyle('title', fontSize=22, textColor=GOLD, fontName='Helvetica-Bold',
        spaceAfter=4, alignment=TA_LEFT)
    s_sub = ParagraphStyle('sub', fontSize=10, textColor=SLATE, fontName='Helvetica', spaceAfter=20)
    s_h2 = ParagraphStyle('h2', fontSize=13, textColor=GOLD, fontName='Helvetica-Bold',
        spaceBefore=16, spaceAfter=8)
    s_body = ParagraphStyle('body', fontSize=10, textColor=HexColor('#cbd5e1'),
        fontName='Helvetica', leading=16, spaceAfter=8)
    s_footer = ParagraphStyle('footer', fontSize=8, textColor=SLATE, fontName='Helvetica',
        alignment=TA_CENTER)

    from datetime import date
    story = [
        Paragraph("VÉRTICE STUDIO", s_title),
        Paragraph("Proposta Comercial Exclusiva", s_sub),
        HRFlowable(width="100%", thickness=1, color=GOLD, spaceAfter=16),
        Paragraph(f"Proposta para: <b>{body.nome_cliente}</b> — {body.empresa or body.nicho}", s_body),
        Paragraph(f"Data: {date.today().strftime('%d/%m/%Y')} · Válidade: 15 dias", s_body),
        Spacer(1, 12),
    ]

    # Parse o texto do Claude em seções
    for linha in texto.split('\n'):
        l = linha.strip()
        if not l:
            story.append(Spacer(1, 6))
        elif l.startswith('#') or (l[0].isdigit() and '.' in l[:3]):
            clean = l.lstrip('#0123456789. ').strip()
            story.append(Paragraph(clean, s_h2))
        else:
            story.append(Paragraph(l, s_body))

    story += [
        Spacer(1, 20),
        HRFlowable(width="100%", thickness=1, color=HexColor('#1e293b')),
        Spacer(1, 8),
        Paragraph("Vértice Studio · automação com IA para negócios · verticestudio.com.br", s_footer),
        Paragraph(f"© {date.today().year} Todos os direitos reservados", s_footer),
    ]

    doc.build(story)
    buf.seek(0)
    fname = f"proposta_{body.nome_cliente.replace(' ','_').lower()}.pdf"
    from fastapi.responses import StreamingResponse
    return StreamingResponse(buf, media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'})


# ── E-mail automation ─────────────────────────────────────────────────────────
import smtplib
import email.mime.text
import email.mime.multipart

SMTP_HOST  = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT  = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER  = os.getenv("SMTP_USER", "")
SMTP_PASS  = os.getenv("SMTP_PASS", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USER)

EMAIL_SEQUENCES = {
    "dia1": {
        "assunto": "Você sabia que negócios como o seu estão crescendo 3x mais rápido com IA?",
        "template": """Olá {nome}!

Meu nome é Kaike, fundador da Vértice Studio.

Encontrei seu negócio e acredito que temos algo que pode mudar seus resultados em {nicho}.

A maioria das empresas do seu nicho ainda depende 100% de processo manual para:
→ Responder leads no WhatsApp
→ Criar conteúdo e posts
→ Acompanhar campanhas de tráfego

A Vértice Studio automatiza tudo isso com IA — e nossos clientes têm visto resultados como:
✅ 40% mais leads qualificados em 30 dias
✅ 60% de redução no tempo de atendimento
✅ ROI médio de 3x no primeiro mês

Tenho 20 minutos disponíveis ainda essa semana para te mostrar como isso funcionaria para o seu negócio.

Vale uma conversa?

Att,
Kaike
Fundador, Vértice Studio
"""
    },
    "dia3": {
        "assunto": "Case real: como {nicho} cresceu 47% com automação",
        "template": """Olá {nome},

Ainda estou pensando no potencial do seu negócio.

Semana passada, um dos nossos clientes no segmento de {nicho} compartilhou um dado incrível:

"Em 30 dias com a Vértice, triplicamos o volume de leads qualificados sem aumentar o orçamento de marketing."

A estratégia foi simples:
1. Bot WhatsApp que qualifica leads 24/7
2. Conteúdo automatizado com IA (posts + Reels)
3. Dashboard de controle em tempo real

O resultado? +47% no faturamento em 45 dias.

Posso montar uma análise rápida do seu negócio — sem compromisso — e te mostrar onde estão as oportunidades escondidas.

Responda esse e-mail com "QUERO VER" e eu te envio a análise em 24h.

Kaike
Vértice Studio
"""
    },
    "dia7": {
        "assunto": "Última mensagem — proposta exclusiva para {nome}",
        "template": """Olá {nome},

Sei que você está ocupado — por isso essa é minha última mensagem.

Quero te fazer uma proposta direta:

Marque uma call de 20 minutos com a equipe Vértice Studio.

Se no final você não ver pelo menos 3 formas claras de como podemos aumentar seu faturamento, eu mesmo te digo que não somos a solução certa pra você.

Simples assim.

→ https://wa.me/5512991564645?text=Quero%20a%20análise%20gratuita

Aproveite enquanto temos vagas disponíveis.

Kaike
Vértice Studio
"""
    }
}

class EmailSeqInput(BaseModel):
    nome: str
    email_destino: str
    nicho: str
    sequencia: str = "dia1"  # dia1, dia3, dia7

@app.post("/email/enviar-sequencia")
async def enviar_sequencia_email(body: EmailSeqInput):
    """Envia e-mail de sequência de follow-up para leads frios."""
    if not SMTP_USER or not SMTP_PASS:
        raise HTTPException(status_code=400, detail="SMTP não configurado. Configure SMTP_USER e SMTP_PASS nas variáveis de ambiente.")

    seq = EMAIL_SEQUENCES.get(body.sequencia)
    if not seq:
        raise HTTPException(status_code=400, detail=f"Sequência '{body.sequencia}' não encontrada. Use: dia1, dia3, dia7")

    assunto = seq["assunto"].format(nome=body.nome, nicho=body.nicho)
    corpo = seq["template"].format(nome=body.nome, nicho=body.nicho)

    msg = email.mime.multipart.MIMEMultipart("alternative")
    msg["Subject"] = assunto
    msg["From"]    = f"Vértice Studio <{FROM_EMAIL}>"
    msg["To"]      = body.email_destino

    # Plain text
    msg.attach(email.mime.text.MIMEText(corpo, "plain", "utf-8"))

    # HTML version
    html_corpo = corpo.replace('\n', '<br>').replace('→', '&rarr;')
    html = f"""<!DOCTYPE html><html><body style="background:#080b10;font-family:Arial,sans-serif;color:#cbd5e1;padding:32px;max-width:600px;margin:0 auto">
<div style="background:#0f1117;border:1px solid rgba(255,255,255,.08);border-radius:16px;padding:32px">
<div style="background:linear-gradient(135deg,#e8c97a,#c09642);width:36px;height:36px;clip-path:polygon(50% 0%,100% 100%,68% 100%,50% 55%,32% 100%,0% 100%);margin-bottom:24px"></div>
<div style="color:#94a3b8;font-size:14px;line-height:1.8">{html_corpo}</div>
<hr style="border:none;border-top:1px solid rgba(255,255,255,.06);margin:24px 0">
<p style="color:#334155;font-size:12px;text-align:center">© 2026 Vértice Studio · <a href="https://verticestudio.com.br" style="color:#e8c97a">verticestudio.com.br</a></p>
</div></body></html>"""
    msg.attach(email.mime.text.MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as srv:
            srv.ehlo()
            srv.starttls()
            srv.login(SMTP_USER, SMTP_PASS)
            srv.sendmail(FROM_EMAIL, body.email_destino, msg.as_string())
        return {"status": "enviado", "destinatario": body.email_destino, "sequencia": body.sequencia}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao enviar e-mail: {str(e)}")


@app.post("/email/follow-up-automatico")
async def follow_up_email_automatico():
    """Verifica leads com e-mail no JSON e envia a sequência correta conforme os dias sem contato."""
    from datetime import datetime, timedelta

    leads_data = carregar_json(LEADS_FILE)
    enviados = []
    erros = []

    for lead in leads_data:
        email_lead = lead.get("email", "")
        if not email_lead or "@" not in email_lead:
            continue
        if lead.get("estagio") in ("fechado", "perdido"):
            continue

        ultima = lead.get("ultima_interacao", lead.get("criado_em", ""))
        if not ultima:
            continue
        try:
            dt = datetime.fromisoformat(ultima.replace("Z", "+00:00"))
            dias = (datetime.now(dt.tzinfo) - dt).days
        except Exception:
            continue

        if dias < 1:
            continue
        elif dias <= 2:
            seq = "dia1"
        elif dias <= 5:
            seq = "dia3"
        elif dias <= 10:
            seq = "dia7"
        else:
            continue  # Desistiu

        try:
            await enviar_sequencia_email(EmailSeqInput(
                nome=lead.get("nome", "amigo"),
                email_destino=email_lead,
                nicho=lead.get("nicho", "seu negócio"),
                sequencia=seq
            ))
            enviados.append({"lead": lead.get("nome"), "seq": seq, "email": email_lead})
        except Exception as e:
            erros.append({"lead": lead.get("nome"), "erro": str(e)})

    return {"enviados": len(enviados), "erros": len(erros), "detalhes": enviados}


# ══════════════════════════════════════════════════════════════════════════════
# 1. GERADOR DE CONTRATO PDF
# ══════════════════════════════════════════════════════════════════════════════

class ContratoInput(BaseModel):
    nome_cliente: str
    empresa: Optional[str] = ""
    nicho: str
    plano: str
    valor_mensal: float
    duracao_meses: int = 12
    servicos: str
    data_inicio: Optional[str] = ""

@app.post("/gerar-contrato")
async def gerar_contrato(body: ContratoInput):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.colors import HexColor
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        import io
        from fastapi.responses import StreamingResponse
        from datetime import date, timedelta
    except ImportError:
        raise HTTPException(status_code=500, detail="reportlab não instalado")

    client = anthropic.Anthropic(api_key=API_KEY)
    hoje = date.today()
    fim = hoje + timedelta(days=30 * body.duracao_meses)

    clausulas_resp = client.messages.create(
        model=MODEL, max_tokens=1800,
        messages=[{"role": "user", "content": f"""Gere as cláusulas de um contrato de prestação de serviços de marketing digital e automação com IA entre:

CONTRATANTE: {body.nome_cliente} ({body.empresa or body.nicho})
CONTRATADA: Vértice Studio
SERVIÇOS: {body.servicos}
PLANO: {body.plano}
VALOR: R$ {body.valor_mensal:.2f}/mês
DURAÇÃO: {body.duracao_meses} meses ({hoje.strftime('%d/%m/%Y')} a {fim.strftime('%d/%m/%Y')})

Escreva de 6 a 8 cláusulas numeradas e objetivas cobrindo: objeto do contrato, obrigações das partes, forma de pagamento, prazo e renovação, confidencialidade, rescisão, propriedade intelectual e foro. Tom formal e jurídico."""}]
    )
    clausulas = clausulas_resp.content[0].text

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        rightMargin=2.5*cm, leftMargin=2.5*cm, topMargin=2*cm, bottomMargin=2*cm)

    GOLD = HexColor('#e8c97a'); DARK = HexColor('#0f1117'); SLATE = HexColor('#94a3b8')

    s_tit = ParagraphStyle('tit', fontSize=18, textColor=GOLD, fontName='Helvetica-Bold', spaceAfter=4, alignment=TA_CENTER)
    s_sub = ParagraphStyle('sub', fontSize=10, textColor=SLATE, fontName='Helvetica', spaceAfter=20, alignment=TA_CENTER)
    s_label = ParagraphStyle('label', fontSize=9, textColor=SLATE, fontName='Helvetica', spaceAfter=2)
    s_val = ParagraphStyle('val', fontSize=11, textColor=HexColor('#ffffff'), fontName='Helvetica-Bold', spaceAfter=12)
    s_h2 = ParagraphStyle('h2', fontSize=12, textColor=GOLD, fontName='Helvetica-Bold', spaceBefore=14, spaceAfter=6)
    s_body = ParagraphStyle('body', fontSize=10, textColor=HexColor('#cbd5e1'), fontName='Helvetica', leading=16, spaceAfter=8)
    s_footer = ParagraphStyle('foot', fontSize=8, textColor=SLATE, fontName='Helvetica', alignment=TA_CENTER)

    story = [
        Paragraph("VÉRTICE STUDIO", s_tit),
        Paragraph("Contrato de Prestação de Serviços", s_sub),
        HRFlowable(width="100%", thickness=1, color=GOLD, spaceAfter=20),
    ]

    dados_tabela = [
        ["Contratante", body.nome_cliente + (f" / {body.empresa}" if body.empresa else "")],
        ["Contratada", "Vértice Studio"],
        ["Nicho / Segmento", body.nicho],
        ["Plano contratado", body.plano],
        ["Valor mensal", f"R$ {body.valor_mensal:,.2f}".replace(",","X").replace(".",",").replace("X",".")],
        ["Duração", f"{body.duracao_meses} meses"],
        ["Início", body.data_inicio or hoje.strftime('%d/%m/%Y')],
        ["Término", fim.strftime('%d/%m/%Y')],
    ]
    t = Table(dados_tabela, colWidths=[4.5*cm, 12*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), HexColor('#1a1e2a')),
        ('TEXTCOLOR', (0,0), (0,-1), HexColor('#e8c97a')),
        ('TEXTCOLOR', (1,0), (1,-1), HexColor('#cbd5e1')),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [HexColor('#0f1117'), HexColor('#131720')]),
        ('GRID', (0,0), (-1,-1), 0.5, HexColor('#1e293b')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 20))
    story.append(Paragraph("SERVIÇOS INCLUÍDOS", s_h2))
    story.append(Paragraph(body.servicos, s_body))
    story.append(Spacer(1, 8))
    story.append(Paragraph("CLÁUSULAS CONTRATUAIS", s_h2))

    for linha in clausulas.split('\n'):
        l = linha.strip()
        if not l:
            story.append(Spacer(1, 4))
        elif l[:2].replace('.','').isdigit():
            story.append(Paragraph(l, s_h2))
        else:
            story.append(Paragraph(l, s_body))

    story.append(Spacer(1, 30))
    assinaturas = [
        ["_______________________________", "_______________________________"],
        [body.nome_cliente, "Vértice Studio"],
        ["Contratante", "Contratada"],
    ]
    ta = Table(assinaturas, colWidths=[8*cm, 8*cm])
    ta.setStyle(TableStyle([
        ('TEXTCOLOR', (0,0), (-1,-1), HexColor('#94a3b8')),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(ta)
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=HexColor('#1e293b')))
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"Vértice Studio · verticestudio.com.br · Gerado em {hoje.strftime('%d/%m/%Y')}", s_footer))

    doc.build(story)
    buf.seek(0)
    fname = f"contrato_{body.nome_cliente.replace(' ','_').lower()}.pdf"
    from fastapi.responses import StreamingResponse
    return StreamingResponse(buf, media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'})


# ══════════════════════════════════════════════════════════════════════════════
# 2. ONBOARDING AUTOMÁTICO
# ══════════════════════════════════════════════════════════════════════════════

ONBOARDING_TASKS = [
    "Reunião de kickoff agendada",
    "Acesso ao portal do cliente enviado",
    "Briefing completo preenchido",
    "Configuração do bot WhatsApp",
    "Primeiros criativos aprovados",
    "Campanha no ar",
    "Primeiro relatório enviado",
]

@app.post("/onboarding/{cliente_id}")
async def iniciar_onboarding(cliente_id: str):
    clientes = _carregar_json(CLIENTES_FILE)
    cliente = next((c for c in clientes if c.get("id") == cliente_id), None)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    nome = cliente.get("nome", "")
    nicho = cliente.get("nicho", "seu negócio")
    plano = cliente.get("plano", "")
    telefone = cliente.get("telefone", "")

    # Gera mensagem de boas-vindas personalizada com Claude
    ai = anthropic.Anthropic(api_key=API_KEY)
    bv = ai.messages.create(
        model=MODEL, max_tokens=300,
        messages=[{"role": "user", "content": f"""Crie uma mensagem de boas-vindas para WhatsApp para o novo cliente da Vértice Studio:

Nome: {nome}
Nicho: {nicho}
Plano: {plano}

Máximo 4 linhas. Tom de sócio animado, não de atendente. Mencione que a jornada começa agora e que em breve entraremos em contato para o kickoff. Inclua emojis estratégicos."""}]
    )
    msg_bv = bv.content[0].text

    # Envia WhatsApp se tiver telefone
    wpp_enviado = False
    if telefone:
        try:
            enviar_whatsapp(telefone, msg_bv)
            wpp_enviado = True
        except Exception:
            pass

    # Cria registro de onboarding no JSON de tarefas
    escalas = _carregar_json("escalas.json")
    onboarding_entry = {
        "id": str(uuid.uuid4()),
        "tipo": "onboarding",
        "cliente_id": cliente_id,
        "cliente_nome": nome,
        "criado_em": __import__('datetime').datetime.now().isoformat(),
        "tasks": [{"task": t, "done": False} for t in ONBOARDING_TASKS],
        "mensagem_bv": msg_bv,
    }
    escalas.append(onboarding_entry)
    _salvar_json("escalas.json", escalas)

    return {
        "status": "onboarding_iniciado",
        "cliente": nome,
        "whatsapp_enviado": wpp_enviado,
        "mensagem": msg_bv,
        "tasks": ONBOARDING_TASKS,
    }

@app.get("/onboarding/{cliente_id}")
async def ver_onboarding(cliente_id: str):
    escalas = _carregar_json("escalas.json")
    ob = next((e for e in reversed(escalas) if e.get("tipo") == "onboarding" and e.get("cliente_id") == cliente_id), None)
    if not ob:
        return {"status": "nao_iniciado", "tasks": []}
    return ob

@app.patch("/onboarding/{cliente_id}/task/{task_idx}")
async def check_onboarding_task(cliente_id: str, task_idx: int):
    escalas = _carregar_json("escalas.json")
    for e in reversed(escalas):
        if e.get("tipo") == "onboarding" and e.get("cliente_id") == cliente_id:
            if 0 <= task_idx < len(e.get("tasks", [])):
                e["tasks"][task_idx]["done"] = not e["tasks"][task_idx]["done"]
            _salvar_json("escalas.json", escalas)
            return e
    raise HTTPException(status_code=404, detail="Onboarding não encontrado")


# ══════════════════════════════════════════════════════════════════════════════
# 4. SCORE DE SAÚDE DO CLIENTE
# ══════════════════════════════════════════════════════════════════════════════

def _calcular_score(cliente: dict, reunioes: list) -> dict:
    from datetime import datetime, timedelta
    score = 50
    fatores = []

    # Fator 1: última reunião
    reunioes_cliente = [r for r in reunioes if body_match(r, cliente.get("nome", ""))]
    if reunioes_cliente:
        ultima = max(reunioes_cliente, key=lambda r: r.get("data", ""))
        try:
            dt = datetime.strptime(ultima["data"], "%Y-%m-%d")
            dias = (datetime.now() - dt).days
            if dias <= 15:   score += 25; fatores.append(("reunião recente", +25))
            elif dias <= 30: score += 15; fatores.append(("reunião no mês", +15))
            elif dias <= 60: score += 0;  fatores.append(("reunião há 2 meses", 0))
            else:            score -= 20; fatores.append(("sem reunião há 60+ dias", -20))
        except Exception:
            pass
    else:
        score -= 10
        fatores.append(("sem reuniões registradas", -10))

    # Fator 2: tempo de contrato
    data_inicio = cliente.get("data_inicio", "")
    if data_inicio:
        try:
            partes = data_inicio.split("/")
            dt_ini = datetime(int(partes[2]), int(partes[1]), int(partes[0]))
            meses = ((datetime.now() - dt_ini).days) // 30
            if meses >= 6:   score += 20; fatores.append((f"{meses}m de contrato", +20))
            elif meses >= 3: score += 10; fatores.append((f"{meses}m de contrato", +10))
            elif meses <= 1: score -= 5;  fatores.append(("cliente novo", -5))
        except Exception:
            pass

    # Fator 3: plano
    plano = cliente.get("plano", "")
    if plano in ("Premium", "Personalizado"): score += 10; fatores.append(("plano premium", +10))
    elif plano == "Básico":                   score -= 5;  fatores.append(("plano básico", -5))

    score = max(0, min(100, score))
    if score >= 70:   nivel = "saudavel"
    elif score >= 45: nivel = "atencao"
    else:             nivel = "risco"

    return {"score": score, "nivel": nivel, "fatores": fatores}

def body_match(reuniao: dict, nome_cliente: str) -> bool:
    nome_lower = nome_cliente.lower()
    return (nome_lower in reuniao.get("nome_cliente", "").lower() or
            nome_lower in reuniao.get("notas", "").lower())

@app.get("/saude-clientes")
async def saude_clientes():
    clientes = _carregar_json(CLIENTES_FILE)
    reunioes = _carregar_json(REUNIOES_FILE)
    ativos = [c for c in clientes if c.get("status") == "ativo"]
    resultado = []
    for c in ativos:
        saude = _calcular_score(c, reunioes)
        resultado.append({
            "id": c.get("id"),
            "nome": c.get("nome"),
            "empresa": c.get("empresa", ""),
            "plano": c.get("plano", ""),
            "valor_mensal": c.get("valor_mensal", 0),
            **saude,
        })
    resultado.sort(key=lambda x: x["score"])
    return resultado


# ══════════════════════════════════════════════════════════════════════════════
# 5. PUBLICAÇÃO AUTOMÁTICA NO INSTAGRAM
# ══════════════════════════════════════════════════════════════════════════════

IG_USER_ID     = os.getenv("IG_USER_ID", "")
IG_BASE        = "https://graph.facebook.com/v21.0"

class PublicarIGInput(BaseModel):
    conteudo_id: str
    image_url: str          # URL pública da imagem
    caption: Optional[str] = ""

@app.post("/publicar-instagram")
async def publicar_instagram(body: PublicarIGInput):
    if not IG_USER_ID or not FB_ACCESS_TOKEN:
        raise HTTPException(status_code=400, detail="IG_USER_ID ou FB_ACCESS_TOKEN não configurados nas variáveis de ambiente Railway")

    # 1. Criar container de mídia
    r1 = requests.post(
        f"{IG_BASE}/{IG_USER_ID}/media",
        params={
            "image_url": body.image_url,
            "caption": body.caption,
            "access_token": FB_ACCESS_TOKEN,
        }
    )
    if not r1.ok:
        raise HTTPException(status_code=502, detail=f"Erro ao criar container IG: {r1.text}")
    creation_id = r1.json().get("id")

    # 2. Publicar
    r2 = requests.post(
        f"{IG_BASE}/{IG_USER_ID}/media_publish",
        params={"creation_id": creation_id, "access_token": FB_ACCESS_TOKEN}
    )
    if not r2.ok:
        raise HTTPException(status_code=502, detail=f"Erro ao publicar no IG: {r2.text}")

    ig_post_id = r2.json().get("id")

    # Atualiza status no conteudo.json
    conteudo = _carregar_json(CONTEUDO_FILE)
    for item in conteudo:
        if item.get("id") == body.conteudo_id:
            item["status"] = "publicado"
            item["ig_post_id"] = ig_post_id
            from datetime import datetime
            item["publicado_em"] = datetime.now().isoformat()
            break
    _salvar_json(CONTEUDO_FILE, conteudo)

    return {"status": "publicado", "ig_post_id": ig_post_id, "conteudo_id": body.conteudo_id}


# ══════════════════════════════════════════════════════════════════════════════
# 7. DASHBOARD PÚBLICO DE RESULTADOS DO CLIENTE
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/resultados-cliente/{token}")
async def resultados_cliente(token: str):
    """Retorna métricas públicas do cliente pelo token (= ID do cliente)."""
    clientes = _carregar_json(CLIENTES_FILE)
    cliente = next((c for c in clientes if c.get("id") == token), None)
    if not cliente or cliente.get("status") != "ativo":
        raise HTTPException(status_code=404, detail="Cliente não encontrado ou inativo")

    reunioes = _carregar_json(REUNIOES_FILE)
    conteudo = _carregar_json(CONTEUDO_FILE)
    leads_data = _carregar_json(LEADS_FILE)

    from datetime import datetime
    agora = datetime.now()
    mes_atual = agora.month
    ano_atual = agora.year

    reunioes_mes = len([r for r in reunioes
        if body_match(r, cliente.get("nome", ""))
        and r.get("data", "")[:7] == f"{ano_atual}-{mes_atual:02d}"])

    posts_publicados = len([c for c in conteudo if c.get("status") == "publicado"])
    posts_agendados = len([c for c in conteudo if c.get("status") == "agendado"])

    leads_mes = len([l for l in leads_data
        if l.get("criado_em", "")[:7] == f"{ano_atual}-{mes_atual:02d}"])
    leads_quentes = len([l for l in leads_data if l.get("score") == "quente"])

    saude = _calcular_score(cliente, reunioes)

    return {
        "cliente": {
            "nome": cliente.get("nome"),
            "empresa": cliente.get("empresa", ""),
            "nicho": cliente.get("nicho", ""),
            "plano": cliente.get("plano"),
            "data_inicio": cliente.get("data_inicio", ""),
        },
        "mes": f"{mes_atual:02d}/{ano_atual}",
        "metricas": {
            "reunioes_mes": reunioes_mes,
            "posts_publicados": posts_publicados,
            "posts_agendados": posts_agendados,
            "leads_mes": leads_mes,
            "leads_quentes": leads_quentes,
            "score_saude": saude["score"],
            "nivel_saude": saude["nivel"],
        },
        "valor_mensal": cliente.get("valor_mensal", 0),
    }


# ══════════════════════════════════════════════════════════════════════════════
# 8. DETECTOR DE CHURN
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/detector-churn")
async def detector_churn():
    clientes = _carregar_json(CLIENTES_FILE)
    reunioes = _carregar_json(REUNIOES_FILE)
    ativos = [c for c in clientes if c.get("status") == "ativo"]

    em_risco = []
    atencao = []
    saudaveis = []

    for c in ativos:
        saude = _calcular_score(c, reunioes)
        entry = {
            "id": c.get("id"),
            "nome": c.get("nome"),
            "empresa": c.get("empresa", ""),
            "plano": c.get("plano", ""),
            "valor_mensal": c.get("valor_mensal", 0),
            "score": saude["score"],
            "nivel": saude["nivel"],
            "fatores": saude["fatores"],
            "data_inicio": c.get("data_inicio", ""),
        }
        if saude["nivel"] == "risco":
            em_risco.append(entry)
        elif saude["nivel"] == "atencao":
            atencao.append(entry)
        else:
            saudaveis.append(entry)

    mrr_risco = sum(c["valor_mensal"] for c in em_risco)

    # Gera insight com Claude se houver clientes em risco
    insight = ""
    if em_risco:
        nomes = ", ".join(c["nome"] for c in em_risco[:3])
        ai = anthropic.Anthropic(api_key=API_KEY)
        r = ai.messages.create(
            model=MODEL, max_tokens=200,
            messages=[{"role": "user", "content": f"""Em 2-3 linhas diretas, sugira ações prioritárias para reter estes clientes em risco de churn na Vértice Studio:
{nomes}
Score médio: {sum(c['score'] for c in em_risco)//len(em_risco) if em_risco else 0}/100
MRR em risco: R$ {mrr_risco:.0f}
Fale como dono da agência, não como consultor."""}]
        )
        insight = r.content[0].text

    return {
        "resumo": {
            "total_ativos": len(ativos),
            "em_risco": len(em_risco),
            "atencao": len(atencao),
            "saudaveis": len(saudaveis),
            "mrr_em_risco": mrr_risco,
        },
        "insight_ia": insight,
        "clientes_risco": em_risco,
        "clientes_atencao": atencao,
        "clientes_saudaveis": saudaveis,
    }


# ── Histórico de conversas ────────────────────────────────────────────────────

@app.get("/conversas")
async def listar_conversas(q: str = ""):
    convs = _carregar_json(CONV_FILE)
    convs.sort(key=lambda c: c.get("ultima_atividade", ""), reverse=True)
    if q:
        q_low = q.lower()
        convs = [c for c in convs if q_low in c.get("nome","").lower() or q_low in c.get("telefone","")]
    return [{"telefone": c["telefone"], "nome": c.get("nome",""), "ultima_atividade": c.get("ultima_atividade",""),
             "total_mensagens": len(c.get("mensagens",[])), "ultima_msg": c["mensagens"][-1]["text"][:80] if c.get("mensagens") else ""}
            for c in convs]

@app.get("/conversas/{telefone}")
async def ver_conversa(telefone: str):
    convs = _carregar_json(CONV_FILE)
    conv = next((c for c in convs if c.get("telefone") == telefone), None)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")
    return conv

@app.delete("/conversas/{telefone}")
async def deletar_conversa(telefone: str):
    convs = _carregar_json(CONV_FILE)
    convs = [c for c in convs if c.get("telefone") != telefone]
    _salvar_json(CONV_FILE, convs)
    return {"status": "deletado"}


# ── Backup automático ─────────────────────────────────────────────────────────

@app.get("/backup")
async def fazer_backup():
    """Retorna um ZIP com todos os JSONs de dados — para download/backup manual."""
    import io, zipfile
    from datetime import datetime
    from fastapi.responses import StreamingResponse

    buf = io.BytesIO()
    arquivos = [LEADS_FILE, CLIENTES_FILE, CONTEUDO_FILE, CONV_FILE,
                REUNIOES_FILE, PERFIS_FILE, "escalas.json"]
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for arq in arquivos:
            if os.path.exists(arq):
                zf.write(arq, os.path.basename(arq))
            else:
                zf.writestr(os.path.basename(arq), "[]")
    buf.seek(0)
    fname = f"vertice_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    return StreamingResponse(buf, media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'})


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

    # Salva conversa no histórico
    from datetime import datetime
    convs = _carregar_json(CONV_FILE)
    # Encontra conversa existente do telefone ou cria nova
    conv = next((c for c in convs if c.get("telefone") == telefone), None)
    if not conv:
        conv = {"telefone": telefone, "nome": "", "mensagens": [], "ultima_atividade": ""}
        convs.append(conv)
    # Tenta pegar nome do lead se existir
    if not conv.get("nome"):
        leads = _carregar_json(LEADS_FILE)
        lead = next((l for l in leads if l.get("telefone") == telefone), None)
        if lead: conv["nome"] = lead.get("nome", "")
    now = datetime.now().isoformat()
    conv["mensagens"].append({"role": "user", "text": mensagem, "ts": now})
    conv["mensagens"].append({"role": "bot", "text": resposta, "ts": now})
    conv["ultima_atividade"] = now
    # Limita a 200 mensagens por conversa
    if len(conv["mensagens"]) > 200:
        conv["mensagens"] = conv["mensagens"][-200:]
    _salvar_json(CONV_FILE, convs)

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
