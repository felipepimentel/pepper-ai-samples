#!/bin/bash

# Ativar ambiente virtual se existir
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Executar o servidor no modo stdio
python servers/weather_server.py --stdio --debug 