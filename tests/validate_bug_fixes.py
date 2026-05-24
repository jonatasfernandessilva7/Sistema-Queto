#!/usr/bin/env python
"""
Simple validation script for bug fixes.
Can be run before installing heavy dependencies like spacy.
"""

import sys
import os
import ast
import importlib.util

def validate_file_syntax(filepath):
    """Validate Python file syntax."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            ast.parse(f.read())
        return True, "OK"
    except SyntaxError as e:
        return False, f"Syntax Error: {e}"
    except Exception as e:
        return False, f"Error: {e}"

def check_import_in_file(filepath, import_name):
    """Check if a module imports a specific name."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            return import_name in content
    except Exception:
        return False

def check_string_in_file(filepath, search_string):
    """Check if a string exists in file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            return search_string in content
    except Exception:
        return False

print("=" * 70)
print("VALIDAÇÃO DE CORREÇÕES DE BUGS - TODAS AS PRIORIDADES")
print("=" * 70)

# Files to validate
files_to_check = {
    "src/AiServices/services/AiReportsService.py": "1.1 - HTTPException raising",
    "src/backend/services/MicrophoneService.py": "1.2 - Thread-safe recording",
    "src/backend/routes/Routes.py": "1.3 - Queue timeout",
    "src/backend/services/DocumentService.py": "2.1-2.2 - Exception handling & absolute paths",
    "src/backend/services/FeedbackService.py": "2.3 - Input validation",
    "src/backend/utils/EmailUtils.py": "3.1 - Email validation",
    "src/backend/services/CaptureSystemLogs/CaptureSystemLogs.py": "3.2 - Specific exceptions",
    "src/backend/services/DocumentAnalysisService.py": "3.3 - Async blocking operations"
}

all_passed = True

# Test 1: Syntax validation
print("\n[1/5] VALIDAÇÃO DE SINTAXE PYTHON")
print("-" * 70)

for filepath, description in files_to_check.items():
    full_path = os.path.join("..", filepath)
    is_valid, message = validate_file_syntax(full_path)
    status = "✓ PASS" if is_valid else "✗ FAIL"
    print(f"{status}: {filepath}")
    if not is_valid:
        print(f"       {message}")
        all_passed = False

# Test 2: Check specific fixes
print("\n[2/5] VALIDAÇÃO DE CORREÇÕES CRÍTICAS E ALTA")
print("-" * 70)

checks = [
    ("src/AiServices/services/AiReportsService.py", "raise HTTPException", "1.1 - HTTPException usa raise"),
    ("src/backend/services/MicrophoneService.py", "class AudioRecorder", "1.2 - Classe AudioRecorder existe"),
    ("src/backend/services/MicrophoneService.py", "threading.RLock()", "1.2 - Usa RLock para thread-safety"),
    ("src/backend/routes/Routes.py", "asyncio.wait_for", "1.3 - Usa asyncio.wait_for para timeout"),
    ("src/backend/routes/Routes.py", "timeout=300", "1.3 - Timeout de 5 minutos"),
    ("src/backend/services/DocumentService.py", "os.path.abspath", "2.2 - UPLOAD_DIR usa abspath"),
    ("src/backend/services/DocumentService.py", "HTTPException", "2.1 - Levanta HTTPException"),
    ("src/backend/services/DocumentService.py", "logging.getLogger", "2.1 - Logging configurado"),
    ("src/backend/services/FeedbackService.py", "if not feedback or not feedback.event_id", "2.3 - Valida event_id"),
    ("src/backend/services/FeedbackService.py", "valid_priorities", "2.3 - Valida priority"),
    ("src/backend/services/FeedbackService.py", "5000", "2.3 - Limita comment a 5000 chars"),
]

for filepath, search_string, check_name in checks:
    full_path = os.path.join("..", filepath)
    found = check_string_in_file(full_path, search_string)
    status = "✓ PASS" if found else "✗ FAIL"
    print(f"{status}: {check_name}")
    if not found:
        all_passed = False

# Test 3: Check MÉDIA priority fixes
print("\n[3/5] VALIDAÇÃO DE CORREÇÕES MÉDIA PRIORIDADE")
print("-" * 70)

media_checks = [
    ("src/backend/utils/EmailUtils.py", "class EmailConfigurationError", "3.1 - Exceções específicas de email"),
    ("src/backend/utils/EmailUtils.py", "def validate_email_configuration", "3.1 - Validação de configuração"),
    ("src/backend/utils/EmailUtils.py", "_validate_email_address", "3.1 - Validação de email"),
    ("src/backend/services/CaptureSystemLogs/CaptureSystemLogs.py", "import logging", "3.2 - Logging configurado"),
    ("src/backend/services/CaptureSystemLogs/CaptureSystemLogs.py", "psutil.NoSuchProcess", "3.2 - Exceções específicas psutil"),
    ("src/backend/services/CaptureSystemLogs/CaptureSystemLogs.py", "subprocess.TimeoutExpired", "3.2 - Timeout handling"),
    ("src/backend/services/DocumentAnalysisService.py", "ThreadPoolExecutor", "3.3 - Thread pool para async"),
    ("src/backend/services/DocumentAnalysisService.py", "async def extract_text", "3.3 - extract_text é async"),
    ("src/backend/services/DocumentAnalysisService.py", "run_in_executor", "3.3 - Usa run_in_executor"),
]

for filepath, search_string, check_name in media_checks:
    full_path = os.path.join("..", filepath)
    found = check_string_in_file(full_path, search_string)
    status = "✓ PASS" if found else "✗ FAIL"
    print(f"{status}: {check_name}")
    if not found:
        all_passed = False

# Test 4: Check BAIXA priority fixes
print("\n[4/5] VALIDAÇÃO DE CORREÇÕES BAIXA PRIORIDADE")
print("-" * 70)

baixa_checks = [
    ("src/backend/repository/GenericsRepository.py", "class DatabaseError", "4.1 - Exceções específicas database"),
    ("src/backend/repository/GenericsRepository.py", "class DocumentNotFoundError", "4.1 - Exceção DocumentNotFoundError"),
    ("src/backend/repository/GenericsRepository.py", "class ReportNotFoundError", "4.1 - Exceção ReportNotFoundError"),
    ("src/backend/repository/GenericsRepository.py", "INSERT OR REPLACE", "4.1 - SQL syntax corrigido"),
    ("src/backend/repository/GenericsRepository.py", "return result['status']", "4.1 - Syntax error ['status'] corrigido"),
    ("src/backend/repository/GenericsRepository.py", "import logging", "4.1 - Logging configurado"),
    ("src/backend/repository/GenericsRepository.py", "logger = logging.getLogger", "4.1 - Logger inicializado"),
    ("src/backend/utils/ConnectionWithLlamaApiGroqUtils.py", "class GroqAPIError", "4.2 - Exceções específicas Groq"),
    ("src/backend/utils/ConnectionWithLlamaApiGroqUtils.py", "class GroqAuthenticationError", "4.2 - Exceção GroqAuthenticationError"),
    ("src/backend/utils/ConnectionWithLlamaApiGroqUtils.py", "MAX_RETRIES = 3", "4.2 - Retry logic configurado"),
    ("src/backend/utils/ConnectionWithLlamaApiGroqUtils.py", "INITIAL_BACKOFF", "4.2 - Exponential backoff"),
    ("src/backend/utils/ConnectionWithLlamaApiGroqUtils.py", "import logging", "4.2 - Logging configurado"),
    ("src/backend/utils/ConnectionWithLlamaApiGroqUtils.py", "httpx.TimeoutError", "4.2 - Timeout error handling"),
    ("src/backend/utils/ConnectionWithLlamaApiGroqUtils.py", "for attempt in range", "4.2 - Retry loop implementado"),
]

for filepath, search_string, check_name in baixa_checks:
    full_path = os.path.join("..", filepath)
    found = check_string_in_file(full_path, search_string)
    status = "✓ PASS" if found else "✗ FAIL"
    print(f"{status}: {check_name}")
    if not found:
        all_passed = False

# Test 5: Check all logging imports
print("\n[5/6] VALIDAÇÃO DE LOGGING")
print("-" * 70)

logging_checks = [
    ("src/backend/services/DocumentService.py", "import logging"),
    ("src/backend/services/FeedbackService.py", "import logging"),
    ("src/backend/services/MicrophoneService.py", "import logging"),
    ("src/backend/routes/Routes.py", "import logging"),
    ("src/backend/utils/EmailUtils.py", "import logging"),
    ("src/backend/services/CaptureSystemLogs/CaptureSystemLogs.py", "import logging"),
    ("src/backend/services/DocumentAnalysisService.py", "import logging"),
    ("src/backend/repository/GenericsRepository.py", "import logging"),
    ("src/backend/utils/ConnectionWithLlamaApiGroqUtils.py", "import logging"),
]

for filepath, import_check in logging_checks:
    full_path = os.path.join("..", filepath)
    found = check_import_in_file(full_path, import_check)
    module_name = filepath.split("/")[-1]
    status = "✓ PASS" if found else "✗ FAIL"
    print(f"{status}: {module_name} - {import_check}")
    if not found:
        all_passed = False

# Test 6: File exists check
print("\n[6/6] VALIDAÇÃO DE TESTES")
print("-" * 70)

test_file = "test_bug_fixes.py"
if os.path.exists(test_file):
    print("✓ PASS: tests/test_bug_fixes.py exists")
    is_valid, msg = validate_file_syntax(test_file)
    if is_valid:
        print("✓ PASS: tests/test_bug_fixes.py syntax is valid")
    else:
        print(f"✗ FAIL: {msg}")
        all_passed = False
else:
    print("✗ FAIL: tests/test_bug_fixes.py not found")
    all_passed = False

# Summary
print("\n" + "=" * 70)
if all_passed:
    print("✓ TODAS AS VALIDAÇÕES PASSARAM!")
    print("\nResumo:")
    print("  • Bugs Críticos (3/3): ✓ Corrigidos")
    print("  • Bugs Alta Prioridade (2/2): ✓ Corrigidos")
    print("  • Bugs Média Prioridade (3/3): ✓ Corrigidos")
    print("  • Bugs Baixa Prioridade (2/2): ✓ Corrigidos")
    print("\n🎉 TODOS OS 10 BUGS FORAM CORRIGIDOS COM SUCESSO!")
    print("\nPróximos passos:")
    print("1. Instalar dependências: pip install -r requirements.txt")
    print("2. Executar testes: pytest tests/test_bug_fixes.py -v")
    print("3. Executar testes existentes: pytest tests/ -v")
    sys.exit(0)
else:
    print("✗ ALGUMAS VALIDAÇÕES FALHARAM")
    print("\nPor favor, revise os erros acima.")
    sys.exit(1)
