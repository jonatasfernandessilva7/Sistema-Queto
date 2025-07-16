# Queto – Sistema Multiagentes de IA para Gestão de Crises

**Queto** é um sistema de multiagentes inteligentes. 
Projetado para detectar, analisar, responder e aprender com situações de crise. 
Com base em eventos de diferentes naturezas (como falhas de sistema, ataques cibernéticos ou eventos sonoros anômalos), 
o sistema executa protocolos de resposta, planejamento, aprendizado e geração de relatórios com base em LLMs (Llama 4.0-scout).

---

##  Funcionalidades do Sistema

- **Respostas Reativas**: Lida imediatamente com eventos críticos.
- **Planejamento Deliberativo**: Sugere ações de contenção com base na situação.
- **Aprendizado Simulado**: Classifica a gravidade com base em histórico e regras.
- **Geração de Gráfico 3D**: Visualização impacto, probabilidade e amplitude geográfica.
- **Análise de Áudio**: Detecta padrões em tempo real (alarme, explosão, grito etc).
- **Geração de Relatórios com LLama**: PDFs automáticos com resposta, plano e prioridade.
- **Envio de E-mail**: Relatórios são enviados automaticamente ao administrador.

---

## Principais Tecnologias

- Backend: FastAPI
- Frontend: Ângular
- LLM: Llama 4.0 scout

---

## Como Executar o Backend

[1] Clone o repositório:

```bash
git clone https://github.com/jonatasfernandessilva7/Sistema-Queto.git
```

[2] Entre nas pastas:

```bash
cd src
cd backend
```

[3] Execute o comando no terminal:

```bash
uvicorn server:app --reload --port 8080
```

## Como Executar o Frontend

[1] Com o repositório clonado, como no exemplo acima.:

[2] Entre nas pastas:

```bash
cd src
cd Frontend
cd System-Queto
```

[3] Execute o comando no terminal:

```bash
ng serve
```
