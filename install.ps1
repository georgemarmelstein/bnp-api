# install.ps1 - Instalacao automatica do MCP BNP-API no Claude Desktop (Windows)
#
# Uso:
#   powershell -ExecutionPolicy ByPass -File install.ps1
#
# O que faz:
#   1. Verifica se uv esta instalado (instala se necessario)
#   2. Adiciona o servidor bnp-api ao claude_desktop_config.json
#   3. Preserva servidores MCP ja configurados

$ErrorActionPreference = "Stop"

$REPO_URL = "git+https://github.com/georgemarmelstein/bnp-api.git"
$SERVER_NAME = "bnp-api"
$CONFIG_PATH = "$env:APPDATA\Claude\claude_desktop_config.json"

# 1. Verificar/instalar uv
Write-Host "[1/3] Verificando uv..." -ForegroundColor Cyan
$uvPath = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uvPath) {
    Write-Host "  uv nao encontrado. Instalando..." -ForegroundColor Yellow
    irm https://astral.sh/uv/install.ps1 | iex
    # Recarregar PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    $uvPath = Get-Command uv -ErrorAction SilentlyContinue
    if (-not $uvPath) {
        Write-Host "[ERRO] Falha ao instalar uv. Instale manualmente: https://docs.astral.sh/uv/" -ForegroundColor Red
        exit 1
    }
    Write-Host "  uv instalado com sucesso." -ForegroundColor Green
} else {
    Write-Host "  uv encontrado: $($uvPath.Source)" -ForegroundColor Green
}

# 2. Ler ou criar config
Write-Host "[2/3] Configurando Claude Desktop..." -ForegroundColor Cyan

$configDir = Split-Path $CONFIG_PATH -Parent
if (-not (Test-Path $configDir)) {
    New-Item -ItemType Directory -Path $configDir -Force | Out-Null
    Write-Host "  Diretorio criado: $configDir" -ForegroundColor Yellow
}

if (Test-Path $CONFIG_PATH) {
    $configText = Get-Content $CONFIG_PATH -Raw -Encoding UTF8
    try {
        $config = $configText | ConvertFrom-Json
    } catch {
        Write-Host "[ERRO] claude_desktop_config.json tem JSON invalido. Corrija manualmente." -ForegroundColor Red
        Write-Host "  Caminho: $CONFIG_PATH" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "  Config existente carregada." -ForegroundColor Green
} else {
    $config = [PSCustomObject]@{}
    Write-Host "  Criando nova config." -ForegroundColor Yellow
}

# 3. Adicionar/atualizar servidor BNP
if (-not $config.mcpServers) {
    $config | Add-Member -NotePropertyName "mcpServers" -NotePropertyValue ([PSCustomObject]@{})
}

$serverConfig = [PSCustomObject]@{
    command = "uvx"
    args = @("--from", $REPO_URL, $SERVER_NAME)
}

if ($config.mcpServers.PSObject.Properties.Name -contains $SERVER_NAME) {
    Write-Host "  Servidor '$SERVER_NAME' ja existe. Atualizando..." -ForegroundColor Yellow
    $config.mcpServers.$SERVER_NAME = $serverConfig
} else {
    $config.mcpServers | Add-Member -NotePropertyName $SERVER_NAME -NotePropertyValue $serverConfig
    Write-Host "  Servidor '$SERVER_NAME' adicionado." -ForegroundColor Green
}

# Salvar (UTF-8 SEM BOM - critico para o Claude Desktop)
$jsonOutput = $config | ConvertTo-Json -Depth 10
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($CONFIG_PATH, $jsonOutput, $utf8NoBom)
Write-Host "  Config salva em: $CONFIG_PATH" -ForegroundColor Green

# 4. Resultado
Write-Host ""
Write-Host "[3/3] Instalacao concluida!" -ForegroundColor Green
Write-Host ""
Write-Host "  Proximo passo: Feche e reinicie o Claude Desktop." -ForegroundColor Cyan
Write-Host ""
Write-Host "  Servidores MCP configurados:" -ForegroundColor Cyan
foreach ($name in $config.mcpServers.PSObject.Properties.Name) {
    Write-Host "    - $name" -ForegroundColor White
}
