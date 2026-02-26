"""
MCP Server: BNP API - Banco Nacional de Precedentes (PAGEA/CNJ)

Servidor MCP que fornece acesso ao Banco Nacional de Precedentes do CNJ,
permitindo buscar precedentes vinculantes de todos os tribunais brasileiros.

Endpoint: POST https://pangeabnp.pdpj.jus.br/api/v1/precedentes
API publica do CNJ/PAGEA (sem autenticacao).
"""

from mcp.server.fastmcp import FastMCP
import requests
from typing import List
from dataclasses import dataclass, field
from datetime import datetime
from tenacity import retry, wait_exponential, stop_after_attempt

# ============================================================
# SERVIDOR MCP
# ============================================================

mcp = FastMCP("bnp-api")

# ============================================================
# CONFIGURACAO
# ============================================================

BNP_API_URL = "https://pangeabnp.pdpj.jus.br/api/v1/precedentes"

TIPOS_PRECEDENTES = {
    "RG": "Repercussao Geral",
    "RR": "Recurso Repetitivo",
    "SV": "Sumula Vinculante",
    "SUM": "Sumula",
    "IRDR": "Incidente de Resolucao de Demandas Repetitivas",
    "IAC": "Incidente de Assuncao de Competencia",
    "PUIL": "Pedido de Uniformizacao de Interpretacao de Lei",
}


# ============================================================
# FUNCOES AUXILIARES
# ============================================================


@dataclass
class ResultadoPrecedente:
    """Resultado padronizado de busca de precedente."""

    conteudo: str
    fonte: str
    tipo: str = ""
    orgao: str = ""
    numero: str = ""
    situacao: str = ""
    data: str = ""
    metadata: dict = field(default_factory=dict)


def _escape_xml(text: str) -> str:
    """Escapa caracteres especiais para XML."""
    if not text:
        return ""
    text = str(text)
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    text = text.replace("'", "&apos;")
    return text


def _truncar_por_tokens(texto: str, max_tokens: int = 5000) -> str:
    """Trunca texto por numero aproximado de tokens (~4 chars/token em portugues)."""
    if not texto:
        return ""

    max_chars = max_tokens * 4

    if len(texto) <= max_chars:
        return texto.strip()

    texto_truncado = texto[:max_chars]
    ultimo_ponto = texto_truncado.rfind(".")
    if ultimo_ponto > max_chars * 0.8:
        texto_truncado = texto_truncado[: ultimo_ponto + 1]

    return texto_truncado.strip() + " [...]"


def _formatar_resultados_xml(
    resultados: List[ResultadoPrecedente], tag_raiz: str = "precedentes_bnp"
) -> str:
    """Formata resultados em XML estruturado."""
    if not resultados:
        return f"<{tag_raiz}>\n<mensagem>Nenhum resultado encontrado.</mensagem>\n</{tag_raiz}>"

    linhas = [f'<{tag_raiz} total="{len(resultados)}">']

    for i, r in enumerate(resultados, 1):
        linhas.append(f'  <item indice="{i}">')

        if r.tipo:
            linhas.append(f"    <tipo>{_escape_xml(r.tipo)}</tipo>")
        if r.numero:
            linhas.append(f"    <numero>{_escape_xml(r.numero)}</numero>")
        if r.orgao:
            linhas.append(f"    <orgao>{_escape_xml(r.orgao)}</orgao>")
        if r.situacao:
            linhas.append(f"    <situacao>{_escape_xml(r.situacao)}</situacao>")
        if r.data:
            linhas.append(f"    <data>{_escape_xml(r.data)}</data>")

        linhas.append("    <conteudo>")
        linhas.append(f"      {_escape_xml(r.conteudo)}")
        linhas.append("    </conteudo>")

        if r.fonte:
            linhas.append(f"    <fonte>{_escape_xml(r.fonte)}</fonte>")

        linhas.append("  </item>")

    linhas.append(f"</{tag_raiz}>")
    return "\n".join(linhas)


# ============================================================
# CLIENTE DA API
# ============================================================


class BNPApi:
    """Cliente da API do BNP com retry automatico."""

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
    )
    def buscar(self, filtro: dict) -> dict:
        """Executa busca com retry automatico."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

        response = requests.post(
            BNP_API_URL, json={"filtro": filtro}, headers=headers, timeout=30
        )
        response.raise_for_status()
        return response.json()


_api = BNPApi()


def _montar_filtro(
    busca: str, orgaos: str, tipos: str, max_resultados: int
) -> dict:
    """Monta o filtro de busca para a API do BNP."""
    lista_orgaos = [o.strip().upper() for o in orgaos.split(",") if o.strip()]
    lista_tipos = [t.strip().upper() for t in tipos.split(",") if t.strip()]

    return {
        "buscaGeral": busca,
        "todasPalavras": "",
        "quaisquerPalavras": "",
        "semPalavras": "",
        "trechoExato": "",
        "atualizacaoDesde": "",
        "atualizacaoAte": "",
        "cancelados": False,
        "ordenacao": "Text",
        "nr": "",
        "pagina": 1,
        "tamanhoPagina": min(max_resultados, 50),
        "orgaos": lista_orgaos,
        "tipos": lista_tipos,
    }


def _extrair_resultados(data: dict) -> List[ResultadoPrecedente]:
    """Converte resposta da API em lista de ResultadoPrecedente."""
    resultados: List[ResultadoPrecedente] = []

    for r in data.get("resultados", []):
        conteudo_partes = []

        questao = r.get("questao", "")
        if questao:
            conteudo_partes.append(f"QUESTAO JURIDICA: {questao}")

        tese = r.get("tese", "")
        if tese:
            conteudo_partes.append(f"TESE: {tese}")

        paradigmas = r.get("processosParadigma", [])
        if paradigmas:
            procs = [
                p.get("numero", "") for p in paradigmas if p.get("numero")
            ]
            if procs:
                conteudo_partes.append(
                    f"PROCESSOS PARADIGMA: {', '.join(procs)}"
                )

        conteudo = "\n\n".join(conteudo_partes)
        conteudo = _truncar_por_tokens(conteudo, max_tokens=2000)

        fonte = ""
        if paradigmas and paradigmas[0].get("link"):
            fonte = paradigmas[0]["link"]

        resultado = ResultadoPrecedente(
            conteudo=conteudo,
            fonte=fonte,
            tipo=TIPOS_PRECEDENTES.get(r.get("tipo"), r.get("tipo", "")),
            orgao=r.get("orgao", ""),
            numero=f"{r.get('tipo', '')} {r.get('nr', '')}",
            situacao=r.get("situacao", ""),
            data=r.get("ultimaAtualizacao", ""),
        )
        resultados.append(resultado)

    return resultados


# ============================================================
# TOOLS
# ============================================================


@mcp.tool()
def buscar_precedentes(
    busca: str,
    orgaos: str = "STF,STJ",
    tipos: str = "RG,RR,SV,SUM",
    max_resultados: int = 10,
) -> str:
    """
    Busca precedentes vinculantes no Banco Nacional de Precedentes (BNP/PAGEA).
    Retorna Repercussao Geral, Recursos Repetitivos, Sumulas Vinculantes e IRDRs.

    IMPORTANTE - SINTAXE DO BNP:
    O BNP usa sintaxe DIFERENTE dos outros sistemas. NAO use "E", "OU", "NAO" como operadores.

    OPERADORES ACEITOS:
    +termo  = Palavra OBRIGATORIA (equivale a AND)
    -termo  = Palavra EXCLUIDA (equivale a NOT)
    "frase" = Expressao EXATA entre aspas

    ESTRATEGIA DE BUSCA - SIGA ESTES PASSOS:
    1. Verifique se existe TEMA VINCULANTE conhecido (ex: Tema 1066, Tema 709)
       Se sim, busque diretamente: "tema 1066"
    2. Identifique o INSTITUTO JURIDICO central (nao a pergunta inteira)
    3. Use termos TECNICOS, nao linguagem coloquial
    4. Adicione + para termos obrigatorios
    5. Use - para excluir contextos indesejados

    EXEMPLOS DE TRANSFORMACAO (pergunta -> query):
    - "Pensao por morte para companheiro homoafetivo"
      Ruim:  pensao por morte para companheiro homoafetivo
      Boa:   +"pensao" +"morte" +homoafetivo
      Melhor: "pensao por morte" +homoafetivo

    - "Aposentadoria especial com uso de EPI"
      Ruim:  aposentadoria especial com uso de EPI neutraliza
      Boa:   +"aposentadoria" +"especial" +EPI

    - "Servidor pode acumular aposentadorias?"
      Ruim:  servidor pode acumular aposentadorias
      Boa:   +acumulacao +aposentadoria +servidor -militar

    - "Qual o tema do STF sobre teto previdenciario?"
      Direta: "tema 1066"
      Alternativa: +teto +previdenciario +"revisao"

    TERMOS TECNICOS - USE EM VEZ DE LINGUAGEM COLOQUIAL:
    aposentar por doenca       -> aposentadoria por invalidez
    auxilio do INSS            -> beneficio previdenciario
    pensao da viuva            -> pensao por morte
    dinheiro para deficiente   -> BPC, LOAS, beneficio assistencial
    tempo de roca              -> atividade rural, segurado especial
    revisar aposentadoria      -> revisao de beneficio
    cortar beneficio           -> cessacao, cancelamento

    O QUE EVITAR:
    - Operadores E, OU, NAO (nao funcionam nesta base)
    - Frases completas como query
    - Artigos e preposicoes (de, para, o, a, com)
    - Queries muito longas (max 4-5 termos significativos)

    Args:
        busca: Query com sintaxe BNP (+termo, -termo, "frase").
               NAO passe perguntas diretas. Use a estrategia acima.
        orgaos: Orgaos separados por virgula. Default: "STF,STJ"
                Opcoes: STF, STJ, TST, TSE, STM, TRFs, TJs
        tipos: Tipos de precedente. Default: "RG,RR,SV,SUM"
               RG=Repercussao Geral, RR=Repetitivo, SV=Sumula Vinculante,
               SUM=Sumula, IRDR=Demandas Repetitivas, IAC=Assuncao Competencia
        max_resultados: Maximo de resultados (1-50). Default: 10

    Returns:
        XML estruturado com precedentes: numero, tese, questao juridica, situacao
    """
    filtro = _montar_filtro(busca, orgaos, tipos, max_resultados)

    try:
        data = _api.buscar(filtro)
        resultados = _extrair_resultados(data)
        xml_resultado = _formatar_resultados_xml(resultados, "precedentes_bnp")

        meta = f'<!-- Busca: "{busca}" | Total: {data.get("total", len(resultados))} | Orgaos: {orgaos} -->\n'
        return meta + xml_resultado

    except requests.exceptions.RequestException as e:
        return f"<erro>Falha na comunicacao com BNP: {str(e)}</erro>"
    except Exception as e:
        return f"<erro>Erro inesperado: {str(e)}</erro>"


@mcp.tool()
def gerar_relatorio_precedentes(
    busca: str,
    orgaos: str = "STF,STJ",
    tipos: str = "RG,RR,SV,SUM",
    max_resultados: int = 10,
) -> str:
    """
    Busca precedentes e gera relatorio formatado em Markdown.

    USE ESTA TOOL quando precisar de um relatorio para apresentar ao usuario.
    Para analise programatica, prefira buscar_precedentes que retorna XML.

    A sintaxe de busca e a MESMA de buscar_precedentes:
    - +termo para obrigatorio
    - -termo para excluir
    - "frase" para expressao exata

    Args:
        busca: Query com sintaxe BNP. Veja buscar_precedentes para detalhes.
        orgaos: Orgaos separados por virgula. Default: "STF,STJ"
        tipos: Tipos de precedente. Default: "RG,RR,SV,SUM"
        max_resultados: Maximo de resultados. Default: 10

    Returns:
        Relatorio formatado em Markdown
    """
    filtro = _montar_filtro(busca, orgaos, tipos, max_resultados)

    try:
        data = _api.buscar(filtro)
        precedentes = data.get("resultados", [])
        data_hora = datetime.now().strftime("%d/%m/%Y %H:%M")

        linhas = [
            "# Relatorio de Analise de Precedentes",
            "",
            f"**Busca realizada:** `{busca}`",
            f"**Data/Hora:** {data_hora}",
            f"**Total de resultados:** {data.get('total', len(precedentes))} (exibindo {len(precedentes)})",
            "",
            "---",
            "",
        ]

        if not precedentes:
            linhas.append(
                "*Nenhum precedente encontrado para os termos de busca.*"
            )
            return "\n".join(linhas)

        for i, p in enumerate(precedentes, 1):
            tipo = p.get("tipo", "")
            tipo_desc = TIPOS_PRECEDENTES.get(tipo, tipo)

            linhas.extend(
                [
                    f"## {i}. {tipo} {p.get('nr', '')} ({p.get('orgao', '')})",
                    "",
                    f"**Tipo:** {tipo_desc}",
                    f"**Situacao:** {p.get('situacao', '')}",
                    f"**Ultima atualizacao:** {p.get('ultimaAtualizacao', '')}",
                    "",
                ]
            )

            if p.get("questao"):
                linhas.extend(
                    [
                        "### Questao Juridica",
                        "",
                        f"> {p['questao']}",
                        "",
                    ]
                )

            if p.get("tese"):
                linhas.extend(
                    [
                        "### Tese/Entendimento",
                        "",
                        f"> {p['tese']}",
                        "",
                    ]
                )

            paradigmas = p.get("processosParadigma", [])
            if paradigmas:
                linhas.extend(["### Processos Paradigma", ""])
                for proc in paradigmas:
                    if proc.get("link"):
                        linhas.append(
                            f"- [{proc.get('numero', 'Link')}]({proc['link']})"
                        )
                    else:
                        linhas.append(f"- {proc.get('numero', '')}")
                linhas.append("")

            linhas.extend(["---", ""])

        # Tabela de conferencia
        linhas.extend(
            [
                "## Metadados para Conferencia",
                "",
                "| # | Tipo | Numero | Orgao | Situacao |",
                "|---|------|--------|-------|----------|",
            ]
        )

        for i, p in enumerate(precedentes, 1):
            linhas.append(
                f"| {i} | {p.get('tipo', '')} | {p.get('nr', '')} | {p.get('orgao', '')} | {p.get('situacao', '')} |"
            )

        linhas.extend(
            [
                "",
                "---",
                "",
                f"*Relatorio gerado via MCP BNP-API em {data_hora}*",
            ]
        )

        return "\n".join(linhas)

    except requests.exceptions.RequestException as e:
        return f"**Erro na busca:** {str(e)}"
    except Exception as e:
        return f"**Erro inesperado:** {str(e)}"


@mcp.tool()
def listar_tipos_precedentes() -> str:
    """
    Lista todos os tipos de precedentes disponiveis para busca no BNP.

    Returns:
        XML com codigo e descricao de cada tipo
    """
    linhas = ["<tipos_precedentes>"]
    for codigo, descricao in TIPOS_PRECEDENTES.items():
        linhas.append(f'  <tipo codigo="{codigo}">{descricao}</tipo>')
    linhas.append("</tipos_precedentes>")

    return "\n".join(linhas)
