import platform
import subprocess
import os
import psutil
from datetime import datetime

# Definindo o nome do arquivo de logs
LOG_FILENAME = "coleta_de_logs_sistema.log"

def get_process_list():
    """Retorna uma lista de processos com nome e tempo de criação."""
    processos = []
    for proc in psutil.process_iter(['pid', 'name', 'create_time', 'username']):
        try:
            pinfo = proc.info
            processos.append({
                'nome': pinfo['name'],
                'usuario': pinfo['username'],
                'inicio': datetime.fromtimestamp(pinfo['create_time']).strftime("%Y-%m-%d %H:%M:%S")
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return processos

def write_log(message):
    """Escreve a mensagem no arquivo de log com timestamp."""
    with open(LOG_FILENAME, "a") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")

def coletar_logs_windows():
    """
    Coleta logs de logon/logoff do Windows e lista de aplicações.
    Usa o comando wevtutil para exportar os logs.
    """
    write_log("--- Iniciando coleta de logs no Windows ---")
    
    try:
        # Coleta de logs de Segurança (logon e logoff)
        # O comando wevtutil query-events é ideal para isso
        # Filtramos por ID de Evento: 4624 (logon) e 4634 (logoff)
        command = 'wevtutil query-events "Security" /q:"*[System[(EventID=4624 or EventID=4634)]]"'
        process = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8')
        
        if process.returncode == 0:
            write_log("Logs de Logon/Logoff (Visualizador de Eventos - Segurança):")
            write_log(process.stdout)
        else:
            write_log(f"Erro ao coletar logs de segurança: {process.stderr}")

        # Coleta de aplicações ativas
        write_log("--- Aplicações e Processos Ativos ---")
        processos = get_process_list()
        
        # Filtra e lista apenas aplicações comuns, evitando processos do sistema
        aplicacoes_relevantes = [
            p for p in processos if any(app.lower() in p['nome'].lower() 
                                        for app in ['chrome', 'firefox', 'edge', 'word', 'excel', 
                                                    'powerpnt', 'outlook', 'spotify', 'code', 'explorer', 'notepad'])
        ]
        
        if aplicacoes_relevantes:
            for p in aplicacoes_relevantes:
                write_log(f"Aplicação: {p['nome']} | Usuário: {p['usuario']} | Início: {p['inicio']}")
        else:
            write_log("Nenhuma aplicação relevante encontrada.")
            
    except Exception as e:
        write_log(f"Erro inesperado durante a coleta de logs do Windows: {e}")
    finally:
        write_log("--- Coleta de logs no Windows finalizada ---\n")

def coletar_logs_linux():
    """
    Coleta logs de autenticação do Linux e lista de aplicações.
    Usa os comandos 'grep' para logs e 'psutil' para processos.
    """
    write_log("--- Iniciando coleta de logs no Linux ---")
    
    try:
        # Define o caminho do arquivo de log de autenticação
        auth_log = "/var/log/auth.log"
        if not os.path.exists(auth_log):
            auth_log = "/var/log/secure"
            
        if os.path.exists(auth_log):
            write_log("Logs de Autenticação (Login/Logout):")
            # Usa 'grep' para encontrar eventos de 'session opened' ou 'session closed'
            command = f"grep -E 'session opened|session closed' {auth_log} | tail -n 50"
            process = subprocess.run(command, shell=True, capture_output=True, text=True, check=True, encoding='utf-8')
            write_log(process.stdout)
        else:
            write_log("Arquivo de log de autenticação não encontrado. Verifique /var/log/auth.log ou /var/log/secure.")

        # Coleta de aplicações ativas
        write_log("--- Aplicações e Processos Ativos ---")
        processos = get_process_list()
        
        # Filtra e lista apenas aplicações comuns (excluindo processos do sistema)
        aplicacoes_relevantes = [
            p for p in processos if any(app.lower() in p['nome'].lower() 
                                        for app in ['chrome', 'firefox', 'libreoffice', 'vscode', 'gnome-terminal', 'kdeconnect'])
        ]

        if aplicacoes_relevantes:
            for p in aplicacoes_relevantes:
                write_log(f"Aplicação: {p['nome']} | Usuário: {p['usuario']} | Início: {p['inicio']}")
        else:
            write_log("Nenhuma aplicação relevante encontrada.")

    except subprocess.CalledProcessError as e:
        write_log(f"Erro ao executar comando de shell no Linux: {e}")
    except Exception as e:
        write_log(f"Erro inesperado durante a coleta de logs do Linux: {e}")
    finally:
        write_log("--- Coleta de logs no Linux finalizada ---\n")

def main():
    """Função principal que detecta o SO e chama a função de coleta correta."""
    so = platform.system()
    if so == "Windows":
        coletar_logs_windows()
    elif so == "Linux":
        coletar_logs_linux()
    else:
        write_log(f"Sistema operacional '{so}' não é suportado por este script.")

if __name__ == "__main__":
    main()