#!/bin/bash
# install.sh - Instalacao automatica do MCP BNP-API no Claude Desktop (macOS/Linux)
#
# Uso:
#   curl -fsSL https://raw.githubusercontent.com/georgemarmelstein/bnp-api/main/install.sh | bash
#   # ou
#   bash install.sh
#
# O que faz:
#   1. Verifica se uv esta instalado (instala se necessario)
#   2. Adiciona o servidor bnp-api ao claude_desktop_config.json
#   3. Preserva servidores MCP ja configurados

set -e

REPO_URL="git+https://github.com/georgemarmelstein/bnp-api.git"
SERVER_NAME="bnp-api"

# Detectar SO e caminho da config
if [[ "$OSTYPE" == "darwin"* ]]; then
    CONFIG_PATH="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
elif [[ "$OSTYPE" == "linux"* ]]; then
    CONFIG_PATH="${XDG_CONFIG_HOME:-$HOME/.config}/Claude/claude_desktop_config.json"
else
    echo "[ERRO] Sistema nao suportado: $OSTYPE"
    echo "  Use install.ps1 para Windows."
    exit 1
fi

# 1. Verificar/instalar uv
echo "[1/3] Verificando uv..."
if ! command -v uv &> /dev/null; then
    echo "  uv nao encontrado. Instalando..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    if ! command -v uv &> /dev/null; then
        echo "[ERRO] Falha ao instalar uv. Instale manualmente: https://docs.astral.sh/uv/"
        exit 1
    fi
    echo "  uv instalado com sucesso."
else
    echo "  uv encontrado: $(which uv)"
fi

# 2. Ler ou criar config
echo "[2/3] Configurando Claude Desktop..."

CONFIG_DIR=$(dirname "$CONFIG_PATH")
mkdir -p "$CONFIG_DIR"

if [ -f "$CONFIG_PATH" ]; then
    # Verificar se o JSON e valido
    if ! python3 -c "import json; json.load(open('$CONFIG_PATH'))" 2>/dev/null; then
        echo "[ERRO] claude_desktop_config.json tem JSON invalido. Corrija manualmente."
        echo "  Caminho: $CONFIG_PATH"
        exit 1
    fi
    echo "  Config existente carregada."
else
    echo '{}' > "$CONFIG_PATH"
    echo "  Criando nova config."
fi

# 3. Adicionar servidor via Python (merge seguro)
python3 -c "
import json

config_path = '''$CONFIG_PATH'''
with open(config_path, 'r') as f:
    config = json.load(f)

if 'mcpServers' not in config:
    config['mcpServers'] = {}

action = 'Atualizado' if '$SERVER_NAME' in config['mcpServers'] else 'Adicionado'

config['mcpServers']['$SERVER_NAME'] = {
    'command': 'uvx',
    'args': ['--from', '$REPO_URL', '$SERVER_NAME']
}

with open(config_path, 'w') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print(f'  Servidor $SERVER_NAME {action.lower()}.')
print(f'  Config salva em: {config_path}')
print()
print('  Servidores MCP configurados:')
for name in config['mcpServers']:
    print(f'    - {name}')
"

# 4. Resultado
echo ""
echo "[3/3] Instalacao concluida!"
echo ""
echo "  Proximo passo: Feche e reinicie o Claude Desktop."
