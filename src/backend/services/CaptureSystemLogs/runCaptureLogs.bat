@echo off
setlocal

REM Define o caminho completo para o seu script Python
set PYTHON_SCRIPT="C:\Users\jonat\Downloads\PESSOAL\Sistema-Queto\src\backend\services\CaptureSystemLogs\CaptureSystemLogs.py"

REM Garante que o diretório de trabalho é o do script para encontrar o arquivo de logs
cd /d "C:\Users\jonat\Downloads\PESSOAL\Sistema-Queto\src\backend\services\CaptureSystemLogs\"

REM Executa o script Python
REM A opção 'start /b' executa o script em segundo plano
start /b python "%PYTHON_SCRIPT%"

endlocal