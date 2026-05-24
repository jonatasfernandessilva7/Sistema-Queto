import platform
import subprocess
import os
import psutil
import logging
from datetime import datetime

log = logging.getLogger(__name__)

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
        except psutil.NoSuchProcess:
            # Process ended between iteration and access
            pass
        except psutil.AccessDenied:
            # No permission to access process info
            pass
        except psutil.ZombieProcess:
            # Zombie process
            pass
        except ValueError as e:
            # Invalid timestamp
            log.debug(f"Error converting process timestamp: {e}")
    return processos

def write_log(message):
    """Escreve a mensagem no arquivo de log com timestamp."""
    try:
        with open(LOG_FILENAME, "a") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
    except IOError as e:
        log.error(f"Error writing to log file: {e}")

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
        
        try:
            process = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                encoding='utf-8',
                timeout=30
            )
            
            if process.returncode == 0:
                write_log("Logs de Logon/Logoff (Visualizador de Eventos - Segurança):")
                write_log(process.stdout)
            else:
                log.warning(f"Erro ao coletar logs de segurança: {process.stderr}")
                write_log(f"Erro ao coletar logs de segurança: {process.stderr}")
                
        except subprocess.TimeoutExpired:
            error_msg = "Timeout ao coletar logs de segurança"
            log.warning(error_msg)
            write_log(error_msg)

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
            
    except subprocess.SubprocessError as e:
        error_msg = f"Erro ao executar subprocess: {e}"
        log.error(error_msg)
        write_log(error_msg)
    except OSError as e:
        error_msg = f"Erro de sistema operacional: {e}"
        log.error(error_msg)
        write_log(error_msg)
    except Exception as e:
        error_msg = f"Erro inesperado durante a coleta de logs do Windows: {e}"
        log.error(error_msg)
        write_log(error_msg)
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
            try:
                write_log("Logs de Autenticação (Login/Logout):")
                # Usa 'grep' para encontrar eventos de 'session opened' ou 'session closed'
                command = f"grep -E 'session opened|session closed' {auth_log} | tail -n 50"
                process = subprocess.run(
                    command, 
                    shell=True, 
                    capture_output=True, 
                    text=True,
                    timeout=30
                )
                
                if process.returncode == 0:
                    write_log(process.stdout)
                else:
                    # grep returns 1 if no matches found, which is not an error
                    if process.returncode != 1:
                        log.warning(f"Grep returned code {process.returncode}: {process.stderr}")
                        
            except subprocess.TimeoutExpired:
                error_msg = "Timeout ao procurar logs de autenticação"
                log.warning(error_msg)
                write_log(error_msg)
            except subprocess.SubprocessError as e:
                error_msg = f"Erro ao executar grep: {e}"
                log.error(error_msg)
                write_log(error_msg)
        else:
            msg = "Arquivo de log de autenticação não encontrado. Verifique /var/log/auth.log ou /var/log/secure."
            log.warning(msg)
            write_log(msg)

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

    except OSError as e:
        error_msg = f"Erro de sistema operacional: {e}"
        log.error(error_msg)
        write_log(error_msg)
    except Exception as e:
        error_msg = f"Erro inesperado durante a coleta de logs do Linux: {e}"
        log.error(error_msg)
        write_log(error_msg)
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
        msg = f"Sistema operacional '{so}' não é suportado por este script."
        log.warning(msg)
        write_log(msg)

if __name__ == "__main__":
    main()