@echo off
setlocal

REM 
set "C:\Users\jonat\Downloads\PESSOAL\Sistema-Queto\src\agents\environment_organizational_agents\Behavioral_analysis_agent.py"

REM
cd \d "C:\Users\jonat\Downloads\PESSOAL\Sistema-Queto\src\agents\environment_organizational_agents\"

REM Executa o script Python
REM A opção 'start /b' executa o script em segundo plano
start /b python "%PYTHON_SCRIPT%"

endlocal