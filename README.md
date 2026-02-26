# BNP API - Servidor MCP para o Banco Nacional de Precedentes

Servidor [MCP](https://modelcontextprotocol.io) (Model Context Protocol) que fornece acesso ao **Banco Nacional de Precedentes** (BNP/PAGEA) do Conselho Nacional de Justica (CNJ).

Permite buscar precedentes vinculantes de todos os tribunais brasileiros diretamente a partir do Claude Desktop ou Claude Code.

## O que e o BNP?

O **Banco Nacional de Precedentes** (BNP) e mantido pelo CNJ atraves da Plataforma de Gestao de Precedentes (PAGEA). Ele centraliza:

- **Repercussao Geral** (STF) - Vinculante erga omnes
- **Recursos Repetitivos** (STJ) - Vinculante
- **Sumulas Vinculantes** (STF) - Vinculante
- **Sumulas** (STF/STJ) - Altamente persuasivo
- **IRDR** - Incidente de Resolucao de Demandas Repetitivas
- **IAC** - Incidente de Assuncao de Competencia
- **PUIL** - Pedido de Uniformizacao de Interpretacao de Lei

A API e **publica** e nao exige autenticacao.

## Ferramentas Disponiveis

### `buscar_precedentes`

Busca precedentes e retorna dados estruturados em XML.

| Parametro | Tipo | Default | Descricao |
|-----------|------|---------|-----------|
| `busca` | string | (obrigatorio) | Query com sintaxe BNP |
| `orgaos` | string | `"STF,STJ"` | Orgaos separados por virgula |
| `tipos` | string | `"RG,RR,SV,SUM"` | Tipos de precedente |
| `max_resultados` | int | `10` | Maximo de resultados (1-50) |

### `gerar_relatorio_precedentes`

Busca precedentes e gera relatorio formatado em Markdown. Use quando precisar apresentar resultados ao usuario.

Mesmos parametros de `buscar_precedentes`.

### `listar_tipos_precedentes`

Lista todos os tipos de precedentes disponiveis com seus codigos.

## Instalacao Rapida (automatica)

### Windows (PowerShell)

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://raw.githubusercontent.com/georgemarmelstein/bnp-api/main/install.ps1 | iex"
```

### macOS/Linux

```bash
curl -fsSL https://raw.githubusercontent.com/georgemarmelstein/bnp-api/main/install.sh | bash
```

Os scripts fazem tudo automaticamente: verificam/instalam o `uv`, adicionam o servidor ao `claude_desktop_config.json` (preservando servidores existentes) e orientam a reiniciar o Claude Desktop.

## Instalacao Manual

### Pre-requisito

Instale o [uv](https://docs.astral.sh/uv/getting-started/installation/) (gerenciador de pacotes Python):

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Claude Desktop

1. Abra o Claude Desktop
2. Va em **Settings > Developer > Edit Config**
3. Adicione a configuracao abaixo ao arquivo `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "bnp-api": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/georgemarmelstein/bnp-api.git", "bnp-api"]
    }
  }
}
```

4. Feche completamente e reinicie o Claude Desktop

> **Nota:** Quando o pacote estiver publicado no PyPI, a configuracao simplifica para:
> ```json
> {
>   "mcpServers": {
>     "bnp-api": {
>       "command": "uvx",
>       "args": ["bnp-api"]
>     }
>   }
> }
> ```

**Localizacao do arquivo de configuracao:**
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

### Claude Code

Via CLI (recomendado):

```bash
claude mcp add bnp-api -- uvx --from git+https://github.com/georgemarmelstein/bnp-api.git bnp-api
```

Ou adicione manualmente ao `settings.json` do Claude Code:

```json
{
  "mcpServers": {
    "bnp-api": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/georgemarmelstein/bnp-api.git", "bnp-api"]
    }
  }
}
```

Para verificar se o servidor foi adicionado:

```bash
claude mcp list
```

### Claude Web (claude.ai)

O Claude Web suporta apenas servidores MCP **remotos** (HTTP/SSE) via **Settings > Connectors**. Este servidor opera localmente via stdio e nao e compativel diretamente com o Claude Web. Para uso no Claude Web, seria necessario hospedar o servidor com transporte HTTP/SSE.

### Desenvolvimento Local

```bash
git clone https://github.com/georgemarmelstein/bnp-api.git
cd bnp-api
uv run bnp-api
```

Para usar no Claude Desktop a partir do clone local:

```json
{
  "mcpServers": {
    "bnp-api": {
      "command": "uv",
      "args": ["--directory", "/caminho/para/bnp-api", "run", "bnp-api"]
    }
  }
}
```

### Instalacao via Agente com Acesso a Terminal

Se voce esta usando um assistente de IA com acesso a terminal (PowerShell, bash, etc.) e quer que ele instale este servidor automaticamente, estas sao as instrucoes precisas.

**Windows (PowerShell):**

```powershell
# 1. Verificar se uv esta instalado
uv --version

# Se nao estiver, instalar:
irm https://astral.sh/uv/install.ps1 | iex

# 2. Ler config existente, fazer merge, salvar
$configPath = "$env:APPDATA\Claude\claude_desktop_config.json"
$config = if (Test-Path $configPath) { Get-Content $configPath -Raw | ConvertFrom-Json } else { [PSCustomObject]@{} }
if (-not $config.mcpServers) { $config | Add-Member -NotePropertyName "mcpServers" -NotePropertyValue ([PSCustomObject]@{}) }
$config.mcpServers | Add-Member -NotePropertyName "bnp-api" -NotePropertyValue ([PSCustomObject]@{
    command = "uvx"
    args = @("--from", "git+https://github.com/georgemarmelstein/bnp-api.git", "bnp-api")
}) -Force
$config | ConvertTo-Json -Depth 10 | Set-Content $configPath -Encoding UTF8

# 3. Informar que precisa reiniciar o Claude Desktop
```

**macOS/Linux (bash):**

```bash
# 1. Verificar se uv esta instalado
uv --version || curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Ler config existente, fazer merge, salvar
CONFIG_PATH="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
# Linux: CONFIG_PATH="${XDG_CONFIG_HOME:-$HOME/.config}/Claude/claude_desktop_config.json"
mkdir -p "$(dirname "$CONFIG_PATH")"
[ -f "$CONFIG_PATH" ] || echo '{}' > "$CONFIG_PATH"

python3 -c "
import json, os
path = os.path.expanduser('$CONFIG_PATH')
with open(path) as f: config = json.load(f)
config.setdefault('mcpServers', {})
config['mcpServers']['bnp-api'] = {
    'command': 'uvx',
    'args': ['--from', 'git+https://github.com/georgemarmelstein/bnp-api.git', 'bnp-api']
}
with open(path, 'w') as f: json.dump(config, f, indent=2)
"

# 3. Informar que precisa reiniciar o Claude Desktop
```

**Pontos criticos para o agente:**
- O `claude_desktop_config.json` pode ja ter outros servidores MCP. **Nunca sobrescreva** o arquivo inteiro — faca merge no campo `mcpServers`.
- Apos modificar o arquivo, o usuario precisa **fechar e reiniciar** o Claude Desktop para que o novo servidor seja carregado.
- O servidor comunica via **stdio** (stdin/stdout). Nao e necessario abrir portas ou configurar rede.

## Guia de Pesquisa

### Sintaxe de Busca

O BNP usa uma sintaxe propria, **diferente** de outros sistemas juridicos (CJF, JULIA, etc.).

| Operador | Descricao | Exemplo |
|----------|-----------|---------|
| `+termo` | Palavra **obrigatoria** (AND) | `+pensao +morte` |
| `-termo` | Palavra **excluida** (NOT) | `+servidor -militar` |
| `"frase"` | Expressao **exata** | `"pensao por morte"` |
| `termo` | Busca simples | `aposentadoria` |

**Operadores que NAO funcionam no BNP:**
- `E`, `OU`, `NAO` (sao da sintaxe CJF)
- `AND`, `OR`, `NOT` (sao da sintaxe em ingles)
- `ADJ`, `PROX` (sao da sintaxe JULIA/CJF)

### Estrategia de Busca

Siga estes passos para obter os melhores resultados:

1. **Verifique se existe tema conhecido**: Se souber o numero do tema (ex: Tema 1066), busque diretamente: `"tema 1066"`
2. **Identifique o instituto juridico central**: Nao a pergunta inteira, mas o conceito juridico
3. **Use termos tecnicos**: Evite linguagem coloquial
4. **Adicione `+` para termos obrigatorios**: Isso filtra resultados irrelevantes
5. **Use `-` para excluir**: Remove contextos indesejados
6. **Maximo 4-5 termos significativos**: Queries longas prejudicam os resultados

### Estrategia Progressiva (do especifico ao geral)

Faca ate 3 buscas antes de concluir que nao ha precedentes:

**Busca 1 - Direta (se numero conhecido):**
```
"tema 1066"
+sumula +111 +STJ
```

**Busca 2 - Instituto juridico especifico:**
```
+aposentadoria +especial +ruido +EPI
+ICMS +"base de calculo" +PIS +COFINS
```

**Busca 3 - Mais ampla (reduzir termos):**
```
+aposentadoria +especial +EPI
+ICMS +"base de calculo"
```

**Busca 4 - Generica (ultimo recurso):**
```
+previdenciario +aposentadoria
+tributario +ICMS
```

### Exemplos de Transformacao

| Pergunta do usuario | Query BNP |
|---------------------|-----------|
| Pensao por morte para companheiro homoafetivo | `"pensao por morte" +homoafetivo` |
| Aposentadoria especial com uso de EPI | `+"aposentadoria" +"especial" +EPI` |
| Servidor pode acumular aposentadorias? | `+acumulacao +aposentadoria +servidor -militar` |
| Qual o tema do STF sobre teto previdenciario? | `"tema 1066"` |
| ICMS na base de calculo do PIS/COFINS | `+ICMS +"base de calculo" +PIS +COFINS` |
| PERSE e CADASTUR | `+perse +cadastur +beneficio` |
| Prescricao no TCU | `+prescricao +TCU +ressarcimento` |

### Termos Tecnicos

Quando a pergunta usar linguagem coloquial, traduza para termos tecnicos:

| Linguagem coloquial | Termo tecnico para busca |
|---------------------|--------------------------|
| aposentar por doenca | `aposentadoria por invalidez` |
| auxilio do INSS | `beneficio previdenciario` |
| pensao da viuva | `pensao por morte` |
| dinheiro para deficiente | `BPC`, `LOAS`, `beneficio assistencial` |
| tempo de roca | `atividade rural`, `segurado especial` |
| revisar aposentadoria | `revisao de beneficio` |
| cortar beneficio | `cessacao`, `cancelamento` |

### Mapeamento por Materia

Referencia rapida de termos sugeridos por area juridica:

| Materia | Termos sugeridos |
|---------|------------------|
| Aposentadoria especial | `+aposentadoria +especial`, `+atividade +especial +EPI` |
| BPC/LOAS | `+BPC +LOAS`, `+beneficio +assistencial +miserabilidade` |
| Pensao por morte | `+"pensao" +"morte" +dependente +qualidade` |
| Auxilio-doenca | `+auxilio +doenca +incapacidade` |
| ICMS base de calculo | `+ICMS +"base de calculo"`, `+exclusao +ICMS +PIS +COFINS` |
| Honorarios sucumbenciais | `+honorarios +fazenda +sucumbencia` |
| Juros e correcao | `+juros +correcao +monetaria +fazenda` |
| Servidor publico | `+servidor +publico`, `+decadencia +administracao` |
| Prescricao TCU | `+prescricao +TCU +ressarcimento +erario` |
| PERSE/CADASTUR | `+perse +cadastur`, `+setor +eventos +beneficio` |

### Armadilhas Comuns

1. **Busca generica retorna tema diferente**: Busca por "tema 69" pode retornar temas relacionados mas nao o 69. Complemente com termos descritivos.

2. **Multiplos temas aplicaveis**: Um assunto pode ter varios temas. Faca multiplas buscas com variacoes.

3. **Tema pendente de julgamento**: Verifique a situacao (Julgado/Pendente/Afetado). Temas pendentes nao tem tese firmada.

4. **Tema com modulacao**: A tese pode ter efeitos modulados temporalmente. Verifique detalhes.

5. **Tema superado ou revisado**: Entendimentos podem mudar. Verifique data do julgamento.

### Hierarquia de Precedentes

| Prioridade | Tipo | Vinculacao |
|------------|------|------------|
| 1 | RG - Repercussao Geral (STF) | Vinculante erga omnes |
| 2 | RR - Recurso Repetitivo (STJ) | Vinculante |
| 3 | SV - Sumula Vinculante (STF) | Vinculante |
| 4 | SUM - Sumula (STF/STJ) | Altamente persuasivo |
| 5 | IRDR/IAC | Persuasivo regional |

### Situacoes dos Precedentes

| Situacao | Significado |
|----------|-------------|
| Julgado | Tese firmada e aplicavel |
| Pendente | Ainda nao ha tese - processos podem estar sobrestados |
| Afetado | Em julgamento pelo tribunal |
| Sobrestado | Aguardando julgamento de outro tema |

## Tipos de Precedentes

| Codigo | Descricao |
|--------|-----------|
| RG | Repercussao Geral (STF) |
| RR | Recurso Repetitivo (STJ) |
| SV | Sumula Vinculante |
| SUM | Sumula |
| IRDR | Incidente de Resolucao de Demandas Repetitivas |
| IAC | Incidente de Assuncao de Competencia |
| PUIL | Pedido de Uniformizacao de Interpretacao de Lei |

## Orgaos Disponiveis

- **STF** - Supremo Tribunal Federal
- **STJ** - Superior Tribunal de Justica
- **TST** - Tribunal Superior do Trabalho
- **TSE** - Tribunal Superior Eleitoral
- **STM** - Superior Tribunal Militar
- **TRF1 a TRF6** - Tribunais Regionais Federais
- **TJs** - Tribunais de Justica estaduais

## API Fonte

- **Endpoint**: `POST https://pangeabnp.pdpj.jus.br/api/v1/precedentes`
- **Fonte**: PAGEA - Plataforma de Gestao de Precedentes do CNJ
- **Autenticacao**: Nenhuma (API publica)

## Dependencias

- Python >= 3.10
- [mcp](https://pypi.org/project/mcp/) >= 1.0.0
- [requests](https://pypi.org/project/requests/) >= 2.28.0
- [tenacity](https://pypi.org/project/tenacity/) >= 8.0.0

## Licenca

MIT
