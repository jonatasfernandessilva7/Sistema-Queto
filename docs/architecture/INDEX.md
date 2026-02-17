# 🏗️ Arquitetura e Design

## 📑 Diagramas, Modelos e Especificações de Arquitetura

Esta pasta contém documentação sobre a arquitetura técnica do sistema.

### 📚 Documentos e Diagramas

#### 1. **[software-architecture.png](software-architecture.png)** - 🖼️ Diagrama de Arquitetura
Visualização completa da arquitetura do sistema.
- Componentes principais
- Fluxos de dados
- Integração entre módulos
- Estrutura em camadas

#### 2. **[A_maturity_model.pdf](A_maturity_model.pdf)** - 📚 Modelo de Maturidade
Modelo conceitual de níveis de confiança e maturidade.
- Escalas de maturidade
- Níveis de confiança
- Critérios de avaliação
- Frameworks de assessment

---

## 🎯 Como Usar Esta Pasta

### Cenários de Uso

**Quero entender a arquitetura geral**
→ software-architecture.png

**Preciso entender o modelo de maturidade**
→ A_maturity_model.pdf

**Vou desenhar novo componente**
→ Revise software-architecture.png primeiramente

**Vou avaliar maturidade**
→ A_maturity_model.pdf

---

## 🏗️ Visão Geral da Arquitetura

```
┌─────────────────────────────────────────────┐
│           API REST (FastAPI)                 │
│  ┌────────────────────────────────────────┐ │
│  │  Routes & Controllers               │ │
│  └────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────────┐
│      Application Logic (Services)           │
│  ┌────────────────────────────────────────┐ │
│  │  Analysis, Audio, Reports, etc   │ │
│  └────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────────┐
│    AI Agents (LangChain)                    │
│  ┌────────────────────────────────────────┐ │
│  │ Orchestrator, Emotional, Risk, etc │ │
│  └────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────────┐
│      Data Layer (SQLite/Database)           │
└─────────────────────────────────────────────┘
```

---

## 📊 Conteúdo Rápido

| Documento | Foco | Tipo |
|-----------|------|------|
| software-architecture.png | Visão geral | Imagem |
| A_maturity_model.pdf | Maturidade | PDF |

---

## 🔗 Relações com Outras Pastas

- **project/**: Requisitos da arquitetura
- **reorganization/**: Como código está estruturado
- **models/**: Especificações dos componentes

---

## 💡 Princípios de Arquitetura

- **Separação de Preocupações**: Cada camada tem responsabilidade clara
- **DRY (Don't Repeat Yourself)**: Código compartilhado em `core/`
- **Modularidade**: Componentes independentes e desacoplados
- **Escalabilidade**: Fácil adicionar novos agentes e serviços

---

**Total de documentos nesta pasta**: 2  
**Data de Atualização**: Fevereiro 2026

👉 [Voltar ao Índice Geral](../INDEX.md)
