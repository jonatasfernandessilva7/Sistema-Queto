#!/bin/bash

# Define o caminho para o diretório do script
# Use `readlink -f` para obter o caminho completo, tornando o script mais robusto
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"

# Define o caminho completo para o script Python
PYTHON_SCRIPT="$SCRIPT_DIR/coletor_de_logs.py"

# Redireciona a saída para um arquivo de log, útil para depuração
# Executa o script Python usando python3
python3 "$PYTHON_SCRIPT" >> "$SCRIPT_DIR/iniciar_coleta.log" 2>&1