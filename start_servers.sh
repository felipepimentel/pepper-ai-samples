#!/bin/bash

# Define o diretório base
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Adiciona o diretório base ao PYTHONPATH
export PYTHONPATH="$BASE_DIR:$PYTHONPATH"

# Inicia o servidor de clima na porta 8000
cd "$BASE_DIR" && python servers/weather_server.py --port 8000 &
WEATHER_PID=$!

# Inicia o servidor de busca na porta 8001
cd "$BASE_DIR" && python servers/search_server.py --port 8001 &
SEARCH_PID=$!

# Inicia o servidor de integração na porta 8002
cd "$BASE_DIR" && python servers/integration_server.py --port 8002 &
INTEGRATION_PID=$!

# Aguarda um pouco para os servidores iniciarem
sleep 2

# Verifica se os servidores estão rodando
if ps -p $WEATHER_PID > /dev/null
then
   echo "Servidor de clima rodando (PID: $WEATHER_PID)"
else
   echo "Erro ao iniciar servidor de clima"
fi

if ps -p $SEARCH_PID > /dev/null
then
   echo "Servidor de busca rodando (PID: $SEARCH_PID)"
else
   echo "Erro ao iniciar servidor de busca"
fi

if ps -p $INTEGRATION_PID > /dev/null
then
   echo "Servidor de integração rodando (PID: $INTEGRATION_PID)"
else
   echo "Erro ao iniciar servidor de integração"
fi

# Salva os PIDs em um arquivo
echo "$WEATHER_PID $SEARCH_PID $INTEGRATION_PID" > server_pids.txt

echo "Servidores iniciados. Use stop_servers.sh para parar."