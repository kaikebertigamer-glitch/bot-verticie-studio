#!/usr/bin/env python3
"""
Agente de Inteligência de Mercado — Vértice Studio
Relatório diário de Copywriting, Growth Marketing e Psicologia da Conversão.
"""

import anthropic
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# ── ReportLab (PDF) ──────────────────────────────────────────────────────────
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.colors import HexColor, white
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table,
        TableStyle, HRFlowable, KeepTogether,
    )
    from reportlab.lib.units import cm
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT
    PDF_OK = True
except ImportError:
    PDF_OK = False
    print("⚠  ReportLab não instalado — saída será Markdown. Execute: pip install reportlab")

# ── Config ───────────────────────────────────────────────────────────────────
NICHE   = os.getenv("NICHE",  "automação de marketing, IA aplicada e SaaS para negócios regionais brasileiros")
OUT_DIR = Path(os.getenv("OUTPUT_DIR", "./relatorios"))
DATE_PT = datetime.now().strftime("%d de %B de %Y")
DATE_F  = datetime.now().strftime("%Y-%m-%d")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Brand palette
C_NAVY   = HexColor("#0a0f1e") if PDF_OK else None
C_GOLD   = HexColor("#c09642") if PDF_OK else None
C_SILVER = HexColor("#d4dce6") if PDF_OK else None
C_LGRAY  = HexColor("#f3f3f3") if PDF_OK else None
C_DGRAY  = HexColor("#2a2a2a") if PDF_OK else None
C_WHITE  = white if PDF_OK else None

# ── Anthropic client ─────────────────────────────────────────────────────────
client = anthropic.Anthropic()
MODEL  = "claude-opus-4-7"

# ── System prompt (será cacheado) ─────────────────────────────────────────────
SYSTEM_PROMPT = f"""Você é um Agente de Inteligência de Mercado especialista em Growth Marketing, \
Copywriting de Alta Conversão e Psicologia do Consumidor, com foco total no mercado digital brasileiro.

NICHO PRIMÁRIO: {NICHE}

COMPETÊNCIAS CORE:
• Engenharia reversa de copys de alta performance (Meta Ads, Google Ads, landing pages, e-mails, VSLs)
• Identificação de gatilhos mentais e vieses cognitivos de conversão
• Análise de tendências emergentes no mercado digital BR (infoprodutos, e-commerce, SaaS, agências)
• Geração de variações de copy aplicáveis imediatamente com base em evidências

FRAMEWORK DE ANÁLISE (aplique sempre):
1. ÂNGULO DE ATAQUE — qual dor/desejo primário a copy explora no primeiro segundo
2. MECANISMO ÚNICO — por que a solução parece exclusiva ou inacessível sem o produto
3. PROMESSA DE TRANSFORMAÇÃO — antes → depois, com especificidade numérica quando possível
4. GATILHOS PSICOLÓGICOS — escassez, urgência, autoridade, prova social, reciprocidade, curiosity gap
5. ARQUITETURA DA CTA — onde aparece, linguagem usada, quebras de objeção embutidas
6. SCORE DE CONVERSÃO — sua avaliação crítica do potencial persuasivo (1–10)

FORMATO DE OUTPUT:
Documentos estruturados, analíticos e profissionais. Apenas blocos textuais com títulos e listas \
— sem markdown decorativo interativo, sem elementos que não renderizem em PDF. Linguagem direta, \
crítica e estratégica. Sem floreios. Densidade de informação alta.

DATA DE HOJE: {DATE_PT}
"""

# ── Tool definitions ──────────────────────────────────────────────────────────
TOOLS: list[dict] = [
    {
        "name": "coletar_panorama_mercado",
        "description": (
            "Coleta e sintetiza dados sobre tendências de copy e comportamento de mercado "
            "nas últimas 24h para o nicho especificado. Retorna panorama geral, tom dominante, "
            "gatilhos em alta e formatos performando melhor."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "nicho": {"type": "string"},
                "tom_predominante": {"type": "string", "description": "Tom de voz dominante observado (urgente, aspiracional, medo, autoridade...)"},
                "formatos_em_alta": {"type": "array", "items": {"type": "string"}},
                "gatilhos_mais_usados": {"type": "array", "items": {"type": "string"}},
                "resumo_executivo": {"type": "string", "description": "Síntese de 3-4 frases do estado do mercado hoje"},
                "nivel_saturacao": {"type": "string", "enum": ["baixo", "medio", "alto", "critico"]},
                "oportunidades_identificadas": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["nicho", "tom_predominante", "formatos_em_alta", "gatilhos_mais_usados",
                         "resumo_executivo", "nivel_saturacao", "oportunidades_identificadas"]
        }
    },
    {
        "name": "engenharia_reversa_copy",
        "description": (
            "Desestrutura completamente uma copy de destaque do mercado, expondo toda a "
            "arquitetura persuasiva, gatilhos, ângulo de ataque e potencial de conversão."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "identificador":        {"type": "string", "description": "Nome/título identificador da copy"},
                "formato":              {"type": "string", "enum": ["anuncio_meta", "anuncio_google", "landing_page", "email_marketing", "post_organico", "video_ad_script", "whatsapp_copy"]},
                "segmento":             {"type": "string"},
                "headline_original":    {"type": "string", "description": "Headline ou abertura exata ou aproximada"},
                "angulo_principal":     {"type": "string"},
                "problema_agitado":     {"type": "string", "description": "Como a dor do cliente foi explorada"},
                "mecanismo_unico":      {"type": "string", "description": "O que torna a solução parecer nova/exclusiva"},
                "gatilhos_usados":      {"type": "array", "items": {"type": "string"}},
                "cta_e_objeccoes":      {"type": "string", "description": "CTA e como as objeções foram quebradas"},
                "score_persuasao":      {"type": "integer", "minimum": 1, "maximum": 10},
                "ponto_mais_forte":     {"type": "string"},
                "ponto_mais_fraco":     {"type": "string"},
                "licao_aplicavel":      {"type": "string", "description": "O que podemos roubar e aplicar imediatamente"}
            },
            "required": ["identificador", "formato", "segmento", "headline_original",
                         "angulo_principal", "problema_agitado", "mecanismo_unico",
                         "gatilhos_usados", "cta_e_objeccoes", "score_persuasao",
                         "ponto_mais_forte", "ponto_mais_fraco", "licao_aplicavel"]
        }
    },
    {
        "name": "mapear_padroes_psicologicos",
        "description": (
            "Identifica, nomeia e documenta os padrões psicológicos e vieses cognitivos "
            "que os concorrentes e referências estão explorando com maior sucesso."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "padroes": {
                    "type": "array",
                    "description": "Lista de padrões identificados nesta análise",
                    "items": {
                        "type": "object",
                        "properties": {
                            "nome":           {"type": "string"},
                            "categoria":      {"type": "string", "enum": ["vies_cognitivo", "gatilho_emocional", "principio_persuasao", "padrao_narrativo", "frame_linguistico"]},
                            "descricao":      {"type": "string"},
                            "frequencia":     {"type": "string", "enum": ["dominante", "crescente", "nicho", "declinando"]},
                            "eficacia":       {"type": "string", "enum": ["comprovada", "emergente", "especulativa"]},
                            "exemplo_real":   {"type": "string"},
                            "como_aplicar":   {"type": "string"}
                        }
                    }
                },
                "meta_padrao": {"type": "string", "description": "O padrão macro que unifica todos os outros neste ciclo de mercado"}
            },
            "required": ["padroes", "meta_padrao"]
        }
    },
    {
        "name": "gerar_variações_copy",
        "description": (
            "Cria variações de copy práticas e aplicáveis baseadas nos achados do dia, "
            "calibradas para o nicho de automação com IA e serviços digitais."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "variacoes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "titulo":             {"type": "string"},
                            "formato":            {"type": "string"},
                            "copy_texto":         {"type": "string"},
                            "angulo":             {"type": "string"},
                            "gatilho_central":    {"type": "string"},
                            "publico":            {"type": "string"},
                            "canal":              {"type": "string"},
                            "por_que_vai_converter": {"type": "string"}
                        }
                    }
                }
            },
            "required": ["variacoes"]
        }
    }
]

# ── Tool executor ─────────────────────────────────────────────────────────────
def execute_tool(name: str, inp: dict[str, Any]) -> str:
    """Executa a ferramenta e retorna resultado serializado."""
    # Para este agente, as ferramentas são analíticas — Claude preenche os dados
    # com base no seu conhecimento de mercado. Aqui validamos e enriquecemos.
    if name == "coletar_panorama_mercado":
        inp.setdefault("timestamp", DATE_PT)
        return json.dumps({"status": "ok", "dados": inp, "fonte": "análise proprietária Claude Opus 4.7"}, ensure_ascii=False)

    if name == "engenharia_reversa_copy":
        inp.setdefault("data_analise", DATE_PT)
        return json.dumps({"status": "ok", "analise": inp}, ensure_ascii=False)

    if name == "mapear_padroes_psicologicos":
        return json.dumps({"status": "ok", "mapeamento": inp, "total_padroes": len(inp.get("padroes", []))}, ensure_ascii=False)

    if name == "gerar_variações_copy":
        return json.dumps({"status": "ok", "variacoes": inp, "total": len(inp.get("variacoes", []))}, ensure_ascii=False)

    return json.dumps({"status": "erro", "mensagem": f"Ferramenta '{name}' não reconhecida"})


# ── Agent loop (coleta dados via tools) ───────────────────────────────────────
def run_agent_loop() -> dict[str, Any]:
    """
    Executa o loop de agente para coletar dados estruturados via tools.
    Retorna dicionário com todos os dados coletados.
    """
    print("🔍  Fase 1 — Coletando inteligência de mercado via tools...")

    messages: list[dict] = [
        {
            "role": "user",
            "content": (
                f"Execute a análise completa do mercado de {NICHE} hoje, {DATE_PT}.\n\n"
                "Siga esta sequência obrigatória:\n"
                "1. Use `coletar_panorama_mercado` para mapear as tendências gerais de hoje.\n"
                "2. Use `engenharia_reversa_copy` de 3 a 5 vezes — escolha copys distintas e "
                "de destaque circulando no mercado (anúncios, landing pages, e-mails). "
                "Escolha formatos variados: pelo menos 1 anuncio_meta, 1 landing_page, 1 email_marketing.\n"
                "3. Use `mapear_padroes_psicologicos` para documentar os padrões recorrentes.\n"
                "4. Use `gerar_variações_copy` com 4-6 variações práticas para nossos serviços "
                "(automação de atendimento com IA, marketing de resposta direta, gestão de tráfego).\n\n"
                "Baseie-se em seu conhecimento profundo do mercado digital brasileiro de 2024-2025. "
                "Seja específico, crítico e estratégico."
            )
        }
    ]

    collected: dict[str, Any] = {
        "panorama": None,
        "copys_analisadas": [],
        "padroes": None,
        "variacoes": None,
    }

    iteration = 0
    MAX_ITER  = 12

    while iteration < MAX_ITER:
        iteration += 1
        print(f"   ↳  Iteração {iteration}...")

        response = client.messages.create(
            model=MODEL,
            max_tokens=8192,
            thinking={"type": "adaptive"},
            output_config={"effort": "high"},
            system=[{
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }],
            tools=TOOLS,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            break

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue

                print(f"      🔧  {block.name}()")
                result = execute_tool(block.name, block.input)
                data   = json.loads(result)

                # Armazena nos dados coletados
                if block.name == "coletar_panorama_mercado":
                    collected["panorama"] = data.get("dados")
                elif block.name == "engenharia_reversa_copy":
                    collected["copys_analisadas"].append(data.get("analise"))
                elif block.name == "mapear_padroes_psicologicos":
                    collected["padroes"] = data.get("mapeamento")
                elif block.name == "gerar_variações_copy":
                    collected["variacoes"] = data.get("variacoes")

                tool_results.append({
                    "type":        "tool_result",
                    "tool_use_id": block.id,
                    "content":     result,
                })

            messages.append({"role": "user", "content": tool_results})

    print(f"   ✓  Coleta finalizada — {len(collected['copys_analisadas'])} copys analisadas.")
    return collected


# ── Narrative generator (streaming) ──────────────────────────────────────────
def generate_narrative(data: dict[str, Any]) -> str:
    """Gera o relatório narrativo completo via streaming."""
    print("✍️   Fase 2 — Gerando relatório narrativo (streaming)...")

    prompt = (
        f"Com base nos dados de inteligência coletados abaixo, escreva o RELATÓRIO DIÁRIO DE "
        f"INTELIGÊNCIA DE MERCADO completo para {DATE_PT}.\n\n"
        f"DADOS COLETADOS:\n{json.dumps(data, ensure_ascii=False, indent=2)}\n\n"
        "ESTRUTURA OBRIGATÓRIA DO RELATÓRIO:\n\n"
        "──────────────────────────────────────────────────────────────────\n"
        "RELATÓRIO DE INTELIGÊNCIA DE COPYWRITING\n"
        f"Vértice Studio · {DATE_PT} · Nicho: {NICHE}\n"
        "──────────────────────────────────────────────────────────────────\n\n"
        "1. PANORAMA GERAL DO DIA\n"
        "   Analise o estado do mercado nas últimas 24 horas: tendências observadas, "
        "tom de voz predominante, gatilhos mais usados, formatos em alta e nível de saturação. "
        "Contextualize o momento do mercado em 3-4 parágrafos analíticos e densos.\n\n"
        "2. ANÁLISE DE ENGENHARIA REVERSA\n"
        "   Para cada copy analisada, estruture em subseção com:\n"
        "   2.1 [Nome da Copy] — [Formato] — Score: X/10\n"
        "   · GANCHO/HYPE: headline e ângulo de abertura\n"
        "   · PROBLEMA/AGITAÇÃO: como a dor foi explorada\n"
        "   · OFERTA E MECANISMO ÚNICO: a solução e o que a torna exclusiva\n"
        "   · CTA E QUEBRA DE OBJEÇÕES: como fecham e removem resistência\n"
        "   · LIÇÃO APLICÁVEL: o que extraímos para uso imediato\n\n"
        "3. MÁXIMOS INSIGHTS E PADRÕES PSICOLÓGICOS\n"
        "   Documente cada padrão identificado com nome técnico, categoria, descrição, "
        "frequência, eficácia, exemplo real e modo de aplicação. "
        "Encerre com o META-PADRÃO que unifica todos.\n\n"
        "4. SUGESTÕES DE APLICAÇÃO IMEDIATA\n"
        "   Para cada variação de copy gerada, apresente: formato, texto completo, ângulo, "
        "gatilho central, público-alvo, canal recomendado e justificativa de conversão.\n\n"
        "5. RECOMENDAÇÃO ESTRATÉGICA DO DIA\n"
        "   Parágrafo único de 5-7 linhas com a principal ação estratégica a tomar "
        "hoje com base em todos os achados. Seja específico, direto e acionável.\n\n"
        "Use linguagem técnica, crítica e estratégica. Densidade máxima de insights. "
        "Sem floreios nem padding. Este relatório é para uso interno de uma agência de marketing."
    )

    full_text = ""
    sys.stdout.write("   ")

    with client.messages.stream(
        model=MODEL,
        max_tokens=16000,
        system=[{
            "type": "text",
            "text": SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"},
        }],
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            full_text += text
            sys.stdout.write(".")
            sys.stdout.flush()

    print(f"\n   ✓  Relatório gerado — {len(full_text):,} caracteres.")
    return full_text


# ── PDF generator ─────────────────────────────────────────────────────────────
def build_pdf(narrative: str, data: dict[str, Any], path: Path) -> None:
    """Gera o PDF profissional com a marca Vértice Studio."""
    if not PDF_OK:
        print("⚠  ReportLab indisponível — pulando geração de PDF.")
        return

    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm,  bottomMargin=2*cm,
    )

    W, H = A4
    styles = getSampleStyleSheet()

    # ── Custom styles ──
    s_cover_title = ParagraphStyle("CoverTitle",
        fontName="Helvetica-Bold", fontSize=28,
        textColor=C_SILVER, leading=36,
        alignment=TA_CENTER, spaceAfter=6)
    s_cover_sub = ParagraphStyle("CoverSub",
        fontName="Helvetica", fontSize=13,
        textColor=C_GOLD, leading=18,
        alignment=TA_CENTER, spaceAfter=4)
    s_cover_date = ParagraphStyle("CoverDate",
        fontName="Helvetica", fontSize=11,
        textColor=HexColor("#888888"), alignment=TA_CENTER)
    s_section = ParagraphStyle("Section",
        fontName="Helvetica-Bold", fontSize=15,
        textColor=C_GOLD, spaceBefore=20, spaceAfter=8, leading=20)
    s_subsection = ParagraphStyle("Subsection",
        fontName="Helvetica-Bold", fontSize=12,
        textColor=C_SILVER if C_SILVER else HexColor("#cccccc"),
        spaceBefore=12, spaceAfter=6, leading=16)
    s_body = ParagraphStyle("Body",
        fontName="Helvetica", fontSize=10,
        textColor=C_DGRAY, leading=15,
        alignment=TA_JUSTIFY, spaceAfter=6)
    s_bullet = ParagraphStyle("Bullet",
        fontName="Helvetica", fontSize=10,
        textColor=C_DGRAY, leading=14,
        leftIndent=14, spaceAfter=3,
        bulletIndent=4, bulletText="·")
    s_label = ParagraphStyle("Label",
        fontName="Helvetica-Bold", fontSize=10,
        textColor=C_NAVY, leading=14)
    s_footer = ParagraphStyle("Footer",
        fontName="Helvetica", fontSize=8,
        textColor=HexColor("#aaaaaa"), alignment=TA_CENTER)

    story: list = []

    # ── Cover page ───────────────────────────────────────────────────────────
    story.append(Spacer(1, 3*cm))

    # Logo-like header table
    cover_header = Table(
        [["VÉRTICE STUDIO"]],
        colWidths=[W - 4*cm],
    )
    cover_header.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), C_NAVY),
        ("TEXTCOLOR",     (0,0), (-1,-1), C_GOLD),
        ("FONTNAME",      (0,0), (-1,-1), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 22),
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
        ("TOPPADDING",    (0,0), (-1,-1), 16),
        ("BOTTOMPADDING", (0,0), (-1,-1), 16),
        ("LEFTPADDING",   (0,0), (-1,-1), 20),
        ("RIGHTPADDING",  (0,0), (-1,-1), 20),
    ]))
    story.append(cover_header)
    story.append(Spacer(1, 0.6*cm))
    story.append(HRFlowable(width="100%", thickness=2, color=C_GOLD, spaceAfter=20))

    story.append(Paragraph("RELATÓRIO DE INTELIGÊNCIA", s_cover_title))
    story.append(Paragraph("Copywriting · Growth Marketing · Psicologia da Conversão", s_cover_sub))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(DATE_PT, s_cover_date))
    story.append(Paragraph(f"Nicho: {NICHE}", s_cover_date))

    story.append(Spacer(1, 2*cm))

    # Summary table
    copys_n   = len(data.get("copys_analisadas") or [])
    padroes_n = len((data.get("padroes") or {}).get("padroes") or [])
    vars_n    = len((data.get("variacoes") or {}).get("variacoes") or [])

    summary_data = [
        ["COPYS ANALISADAS", "PADRÕES MAPEADOS", "VARIAÇÕES GERADAS"],
        [str(copys_n),        str(padroes_n),      str(vars_n)],
    ]
    t_summary = Table(summary_data, colWidths=[(W - 4*cm) / 3] * 3)
    t_summary.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), C_NAVY),
        ("TEXTCOLOR",     (0,0), (-1,0), C_GOLD),
        ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,0), 9),
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
        ("TOPPADDING",    (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 10),
        ("BACKGROUND",    (0,1), (-1,1), C_LGRAY),
        ("TEXTCOLOR",     (0,1), (-1,1), C_NAVY),
        ("FONTNAME",      (0,1), (-1,1), "Helvetica-Bold"),
        ("FONTSIZE",      (0,1), (-1,1), 22),
        ("GRID",          (0,0), (-1,-1), 0.5, HexColor("#dddddd")),
    ]))
    story.append(t_summary)
    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=C_GOLD))
    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph(
        "Documento gerado automaticamente pelo Agente de IA da Vértice Studio. "
        "Uso interno — confidencial.",
        s_footer,
    ))

    story.append(Spacer(1, 3*cm))  # page break visual

    # ── Parse narrative into sections ─────────────────────────────────────────
    def render_section(title: str, content: str) -> None:
        story.append(HRFlowable(width="100%", thickness=1.5, color=C_GOLD, spaceBefore=10, spaceAfter=4))
        story.append(Paragraph(title, s_section))
        for line in content.strip().split("\n"):
            line = line.strip()
            if not line:
                story.append(Spacer(1, 0.2*cm))
                continue
            if line.startswith(("2.", "3.", "4.", "5.")):
                continue  # skip the sub-numbering lines themselves
            if any(line.startswith(p) for p in ("·", "–", "-", "•", "*")):
                text = line.lstrip("·–-•* ").strip()
                story.append(Paragraph(text, s_bullet))
            elif line.isupper() or (len(line) < 80 and line.endswith(":")):
                story.append(Paragraph(line, s_subsection))
            elif line.startswith("2.") or line.startswith("  2."):
                story.append(Paragraph(line, s_subsection))
            else:
                story.append(Paragraph(line, s_body))

    # Split narrative by main sections
    sections: list[tuple[str, str]] = []
    current_title = "RELATÓRIO"
    current_body  = ""
    section_markers = ["1.", "2.", "3.", "4.", "5."]

    for raw_line in narrative.split("\n"):
        line = raw_line.strip()
        is_section = any(
            line.startswith(m) and len(line) > 5
            for m in section_markers
        )
        if is_section and current_body.strip():
            sections.append((current_title, current_body))
            current_title = line
            current_body  = ""
        else:
            current_body += raw_line + "\n"

    if current_body.strip():
        sections.append((current_title, current_body))

    for sec_title, sec_body in sections:
        render_section(sec_title, sec_body)

    # ── Footer data tables ────────────────────────────────────────────────────
    if data.get("copys_analisadas"):
        story.append(HRFlowable(width="100%", thickness=1.5, color=C_GOLD, spaceBefore=20, spaceAfter=4))
        story.append(Paragraph("SCORECARD — COPYS ANALISADAS", s_section))

        rows = [["Copy", "Formato", "Segmento", "Score"]]
        for c in (data["copys_analisadas"] or []):
            if not c:
                continue
            rows.append([
                str(c.get("identificador", "—"))[:45],
                str(c.get("formato", "—")),
                str(c.get("segmento", "—"))[:30],
                f"{c.get('score_persuasao', '?')}/10",
            ])

        if len(rows) > 1:
            col_w = [(W - 4*cm) * x for x in [0.40, 0.22, 0.26, 0.12]]
            t_score = Table(rows, colWidths=col_w, repeatRows=1)
            t_score.setStyle(TableStyle([
                ("BACKGROUND",    (0,0), (-1,0), C_NAVY),
                ("TEXTCOLOR",     (0,0), (-1,0), C_GOLD),
                ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
                ("FONTSIZE",      (0,0), (-1,-1), 9),
                ("ALIGN",         (3,0), (3,-1), "CENTER"),
                ("ROWBACKGROUNDS",(0,1), (-1,-1), [C_WHITE, C_LGRAY]),
                ("GRID",          (0,0), (-1,-1), 0.3, HexColor("#cccccc")),
                ("TOPPADDING",    (0,0), (-1,-1), 6),
                ("BOTTOMPADDING", (0,0), (-1,-1), 6),
                ("LEFTPADDING",   (0,0), (-1,-1), 8),
                ("FONTNAME",      (0,1), (-1,-1), "Helvetica"),
            ]))
            story.append(t_score)

    # ── Final footer ──────────────────────────────────────────────────────────
    story.append(Spacer(1, 1.5*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=C_GOLD))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        f"Vértice Studio — Relatório de Inteligência — {DATE_PT} · Gerado por IA (Claude Opus 4.7) · Confidencial",
        s_footer,
    ))

    doc.build(story)
    print(f"   ✓  PDF salvo: {path}")


# ── Markdown fallback ─────────────────────────────────────────────────────────
def save_markdown(narrative: str, data: dict[str, Any], path: Path) -> None:
    header = (
        f"# Relatório de Inteligência de Copywriting\n\n"
        f"**Vértice Studio** · {DATE_PT} · Nicho: {NICHE}\n\n"
        f"---\n\n"
        f"**Copys analisadas:** {len(data.get('copys_analisadas') or [])} | "
        f"**Padrões mapeados:** {len((data.get('padroes') or {}).get('padroes') or [])} | "
        f"**Variações geradas:** {len((data.get('variacoes') or {}).get('variacoes') or [])}\n\n"
        f"---\n\n"
    )
    path.write_text(header + narrative, encoding="utf-8")
    print(f"   ✓  Markdown salvo: {path}")


# ── Save raw JSON ─────────────────────────────────────────────────────────────
def save_json(data: dict[str, Any], path: Path) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"   ✓  JSON salvo: {path}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    print("\n" + "═" * 60)
    print("  VÉRTICE STUDIO — AGENTE DE INTELIGÊNCIA DE MERCADO")
    print(f"  {DATE_PT}")
    print("═" * 60 + "\n")

    # ── Fase 1: coleta estruturada via tools ──────────────────────────────────
    raw_data = run_agent_loop()
    save_json(raw_data, OUT_DIR / f"{DATE_F}_dados_brutos.json")

    # ── Fase 2: narrativa via streaming ───────────────────────────────────────
    narrative = generate_narrative(raw_data)

    # ── Fase 3: persistência ──────────────────────────────────────────────────
    print("💾  Fase 3 — Salvando arquivos...")

    md_path  = OUT_DIR / f"{DATE_F}_relatorio.md"
    pdf_path = OUT_DIR / f"{DATE_F}_relatorio.pdf"

    save_markdown(narrative, raw_data, md_path)

    if PDF_OK:
        build_pdf(narrative, raw_data, pdf_path)
        final = pdf_path
    else:
        final = md_path

    print(f"\n{'═' * 60}")
    print(f"  ✅  RELATÓRIO PRONTO → {final}")
    print(f"{'═' * 60}\n")


if __name__ == "__main__":
    main()
