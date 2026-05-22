import os
import re
from pathlib import Path
from collections import defaultdict

# Find all Python files
py_files = list(Path("src").rglob("*.py"))
print(f"Total Python files: {len(py_files)}\n")

# Extract all imports and modules
imported_modules = set()
defined_modules = set()

for file in py_files:
    # Get module name
    rel_path = file.relative_to(".")
    module_name = str(rel_path).replace("\\", "/").replace(".py", "").replace("/", ".").lstrip(".")
    defined_modules.add(module_name)
    
    # Extract imports
    with open(file, encoding="utf-8", errors="ignore") as f:
        content = f.read()
        
    # Find all imports
    imports = re.findall(r'^(?:from|import)\s+([^\s\n]+)', content, re.MULTILINE)
    for imp in imports:
        if imp.startswith("."):
            continue
        # Get the root module
        root = imp.split(".")[0]
        if root.startswith("src"):
            imported_modules.add(root)

print("=" * 80)
print("ANÁLISE DE CÓDIGO MORTO")
print("=" * 80)

# Find unused files in src
src_modules = {m for m in defined_modules if m.startswith("src")}
print(f"\nTotal modules em src: {len(src_modules)}")

unused = []
for module in sorted(src_modules):
    # Check if any file imports this module
    found = False
    for imp in imported_modules:
        if module in imp or imp in module:
            found = True
            break
    
    # Special handling for __init__ files
    if module.endswith("__init__"):
        found = True
    
    # Check files that reference it
    if not found:
        unused.append(module)

print("\n❌ POSSÍVEIS ARQUIVOS NÃO UTILIZADOS:")
print("-" * 80)
for m in unused[:20]:
    file_path = m.replace(".", os.sep) + ".py"
    print(f"  • {file_path}")

# Find specific deprecated files
print("\n" + "=" * 80)
print("ARQUIVOS COM PADRÕES DUPLICADOS OU DEPRECATED:")
print("-" * 80)

patterns = {
    "EmailUtils.py": ("src/backend/utils/EmailUtils.py", "src/core/utils/email_utils.py"),
    "idenpotenceFuncionUtils.py": ("src/backend/utils/idenpotenceFuncionUtils.py", "src/core/utils/idempotency_utils.py"),
    "ConnectionWithLlamaApiGroqUtils.py": ("src/backend/utils/ConnectionWithLlamaApiGroqUtils.py", "src/core/utils/llama_api_utils.py"),
}

for name, (deprecated, correct) in patterns.items():
    print(f"\n  ⚠️  {name}")
    print(f"     Deprecated: {deprecated}")
    print(f"     Correto: {correct}")
    
    # Check which is being used
    deprecated_used = 0
    correct_used = 0
    
    for file in py_files:
        with open(file, encoding="utf-8", errors="ignore") as f:
            content = f.read()
        deprecated_used += len(re.findall(rf"from.*{deprecated}\b", content))
        correct_used += len(re.findall(rf"from.*{correct}\b", content))
    
    print(f"     Importações deprecated: {deprecated_used}")
    print(f"     Importações corretas: {correct_used}")
    print(f"     Status: {'PODE SER REMOVIDO' if deprecated_used == 0 else 'AINDA EM USO'}")
