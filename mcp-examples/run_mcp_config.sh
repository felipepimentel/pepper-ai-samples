#!/bin/bash
# MCP Runner Launcher
# Este script inicia o MCP a partir de um arquivo de configuração JSON

# Interromper processos em execução ao sair
trap 'kill $(jobs -p) 2>/dev/null' EXIT

# Configurar saída colorida
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # Sem cor

echo -e "${BLUE}=======================================${NC}"
echo -e "${BLUE}       MCP JSON Configuration Launcher       ${NC}"
echo -e "${BLUE}=======================================${NC}"

# Verificar se Python está disponível
if ! command -v python &> /dev/null; then
    echo -e "${RED}Erro: Python não está instalado${NC}"
    exit 1
fi

# Verificar se o script existe
SCRIPT_PATH="$(dirname "$0")/mcp_runner.py"
if [ ! -f "$SCRIPT_PATH" ]; then
    echo -e "${RED}Erro: Script MCP Runner não encontrado em $SCRIPT_PATH${NC}"
    exit 1
fi

# Verificar se o arquivo de configuração existe
CONFIG_PATH="$(dirname "$0")/mcp.json"
if [ ! -f "$CONFIG_PATH" ]; then
    echo -e "${RED}Erro: Arquivo de configuração não encontrado em $CONFIG_PATH${NC}"
    exit 1
fi

# Garantir que o diretório pai esteja no PYTHONPATH
export PYTHONPATH="$(dirname $(dirname "$0")):$PYTHONPATH"

echo -e "${GREEN}Iniciando MCP com configuração JSON...${NC}"
echo -e "${YELLOW}Pressione Ctrl+C para sair${NC}"
echo ""

# Executar o script
python "$SCRIPT_PATH" "$CONFIG_PATH"

# Verificar o código de saída
STATUS=$?
if [ $STATUS -eq 0 ]; then
    echo -e "${GREEN}MCP finalizado com sucesso${NC}"
elif [ $STATUS -eq 130 ]; then
    echo -e "${YELLOW}MCP foi interrompido pelo usuário${NC}"
else
    echo -e "${RED}MCP finalizado com erro, código $STATUS${NC}"
fi

echo -e "${BLUE}=======================================${NC}"
echo "Obrigado por usar o MCP Runner!"
echo -e "${BLUE}=======================================${NC}" 