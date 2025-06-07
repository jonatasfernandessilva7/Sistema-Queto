# Queto – Agente Autônomo de Gestão de Crises

**Queto** é um agente autônomo inteligente projetado para detectar, analisar, responder e aprender com situações de crise. Com base em eventos de diferentes naturezas (como falhas de sistema, ataques cibernéticos ou eventos sonoros anômalos), o agente executa protocolos de resposta, planejamento, aprendizado e geração de relatórios com base em LLMs (LLaMA 3.2).

---

## 🧠 Funcionalidades do Agente

- **🛑 Respostas Reativas**: Lida imediatamente com eventos críticos.
- **🗂️ Planejamento Deliberativo**: Sugere ações de contenção com base na situação.
- **🎓 Aprendizado Simulado**: Classifica a gravidade com base em histórico e regras.
- **📊 Geração de Gráfico 3D**: Visualização de crises por impacto, probabilidade e amplitude geográfica.
- **🎧 Análise de Áudio**: Detecta padrões em tempo real (alarme, explosão, grito etc).
- **📄 Geração de Relatórios com LLaMA**: PDFs automáticos com resposta, plano e prioridade.
- **📨 Envio de E-mail**: Relatórios são enviados automaticamente ao administrador.

---

## 🚀 Como Executar

[1] Clone o repositório:

```bash
git clone https://github.com/seuusuario/QuetoAgent.git
```

[2] Entre nas pastas:

```bash
cd QuetoAgent
cd src
```

[3] Execute o comando no terminal:

```bash
uvicorn main:app --reload --port 8500
```
