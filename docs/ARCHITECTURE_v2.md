# C2M - ARQUITETURA COMPLETA v2.0

## 📋 Overview

**C2M (Cyber Crisis Management)** é um sistema de IA multiagente para gerenciamento inteligente de crises organizacionais baseado em:
- Análise de comunicações (áudio, transcrições)
- Simulação probabilística (Monte Carlo - 50k cenários)
- Conformidade com políticas (busca vetorial semântica)
- Classificação ISO 22324 (verde/amarelo/laranja/vermelho)
- Aprendizado contínuo com feedback humano (RLHF)

---

## 🏗️ ARQUITETURA MODERNA (CLEAN)

```
Sistema-Queto/
│
├── src/
│   ├── backend/
│   │   ├── server.py                          # FastAPI app principal
│   │   ├── services/                          # 🆕 Serviços de negócio
│   │   │   ├── __init__.py
│   │   │   ├── AudioProcessorService.py       # 🆕 Processamento de áudio
│   │   │   ├── VectorSearchService.py         # 🆕 Busca semântica
│   │   │   ├── ISOClassifierService.py        # 🆕 Classificação ISO 22324
│   │   │   ├── DocumentService.py
│   │   │   ├── FeedbackService.py
│   │   │   └── ReportsService.py
│   │   ├── controllers/                        # Controllers HTTP
│   │   ├── models/                             # Pydantic models
│   │   ├── repository/                         # Data access layer
│   │   └── database/                           # DB connections
│   │
│   ├── api/
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   └── api_v1_routes.py              # 🆕 Rotas REST v1
│   │   ├── controllers/
│   │   └── services/
│   │
│   ├── agents/
│   │   ├── orchestrator/                       # Orquestrador C2M
│   │   │   ├── C2M_Models.py                  # Modelos de dados
│   │   │   ├── C2M_Analysis.py                # Decision Tree + Monte Carlo
│   │   │   ├── C2M_Orchestrator.py            # Orquestração
│   │   │   └── ...
│   │   └── ...
│   │
│   ├── AiServices/                             # Serviços de IA
│   │   ├── AiApprenticeship.py                # RLHF learning
│   │   ├── services/
│   │   │   ├── WeightManager.py
│   │   │   ├── RLHFFeedbackService.py
│   │   │   └── ...
│   │   └── ...
│   │
│   └── core/
│       ├── config/
│       ├── models/
│       └── utils/
│
├── tests/
│   ├── test_vector_search.py                  # 🆕 Testes VectorSearch
│   ├── test_iso_classifier.py                 # 🆕 Testes ISO
│   ├── test_audio_processor.py                # 🆕 Testes Audio
│   ├── test_c2m_api.py                        # 🆕 Testes API v1
│   └── ...
│
├── docs/
│   ├── ARCHITECTURE.md                        # Este arquivo
│   ├── API_V1.md                              # 🆕 Documentação API
│   ├── QUICK_START.md                         # 🆕 Quick start
│   └── ...
│
├── requirements.txt                            # Dependências
├── .env.example                                # 🆕 Variáveis de ambiente
├── docker-compose.yml                          # 🆕 Orquestração containers
└── README.md
```

---

## 🔄 PIPELINE DE PROCESSAMENTO

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    UPLOAD DE ÁUDIO (POST /api/v1/audio/upload)         │
└──────────────────────────┬────────────────────────────────────────────────┘
                           │
                           ▼
         ┌─────────────────────────────────────┐
         │  1️⃣ VALIDAÇÃO & METADADOS          │
         │     - Formato (wav, mp3, m4a)      │
         │     - Tamanho (< 100MB)            │
         │     - Duration, sample rate        │
         └────────────┬────────────────────────┘
                      │
                      ▼
         ┌─────────────────────────────────────┐
         │  2️⃣ TRANSCRIÇÃO (Whisper Groq)     │
         │     - Modelo: whisper-large-v3     │
         │     - Linguagem: PT                 │
         │     - Output: texto_completo       │
         └────────────┬────────────────────────┘
                      │
         ┌────────────┴────────────┐
         │                         │
         ▼                         ▼
  3️⃣ ANÁLISE        3️⃣ ANÁLISE
  DE SENTIMENTO      DE FALANTES
  (TextBlob)         (MFCC + KMeans)
  - polarity         - num_speakers
  - subjectivity     - confidence
         │                         │
         └────────────┬────────────┘
                      │
                      ▼
         ┌─────────────────────────────────────┐
         │  4️⃣ DETECÇÃO DE PALAVRAS-CHAVE    │
         │     - Crise, ataque, falha, etc   │
         └────────────┬────────────────────────┘
                      │
                      ▼
         ┌─────────────────────────────────────┐
         │  5️⃣ CÁLCULO DE PROBABILIDADE C2M   │
         └────────────┬────────────────────────┘
                      │
     ┌────────────────┼────────────────┐
     │                │                │
     ▼                ▼                ▼
  DECISION TREE   MONTE CARLO    VECTOR SEARCH
  (Estágio 2)    (50k cenários)  (Conformidade)
  Score 0-1      Prob %         Fator C
     │                │                │
     └────────────────┼────────────────┘
                      │
                      ▼
         ┌─────────────────────────────────────┐
         │  6️⃣ CLASSIFICAÇÃO ISO 22324        │
         │  - GREEN (P < 0.20)                 │
         │  - YELLOW (0.20 ≤ P < 0.40)        │
         │  - ORANGE (0.40 ≤ P < 0.70)        │
         │  - RED (P ≥ 0.70)                   │
         └────────────┬────────────────────────┘
                      │
                      ▼
         ┌─────────────────────────────────────┐
         │  7️⃣ GERAÇÃO DE RELATÓRIO           │
         │  - Ações recomendadas               │
         │  - Próximos passos                  │
         │  - Explicação LLM (opcional)        │
         └────────────┬────────────────────────┘
                      │
                      ▼
         ┌─────────────────────────────────────┐
         │  8️⃣ FEEDBACK HUMANO (RLHF)         │
         │  - Correções & validação            │
         │  - Ajuste de pesos                  │
         │  - Aprendizado contínuo             │
         └─────────────────────────────────────┘
```

---

## 📡 API REST v1

### Base URL
```
http://localhost:8000/api/v1
```

### Endpoints Principais

#### 1. **AUDIO PROCESSING**
```
POST /audio/upload
  - Upload de arquivo de áudio
  - Processamento completo (transcrição + análise)
  - Retorna: meeting_id, transcription, sentiment, speakers

GET /audio/status/{meeting_id}
  - Status e resultado do processamento
```

#### 2. **CRISIS PROBABILITY**
```
POST /crisis/probability
  Request:
    {
      "sentiment_polarity": -0.3,
      "maturity_level": 3.5,
      "has_risk_plan": true,
      "has_crisis_plan": false,
      "risk_severity_scores": [0.4, 0.6, 0.5],
      "transcript_text": "..."  # opcional, para conformidade
    }
  
  Response:
    {
      "request_id": "uuid",
      "probability": 0.45,
      "confidence": 0.87,
      "iso_level": "LARANJA",
      "iso_color": "#FF8800",
      "action_required": "Ativar comitê de crise",
      "contributing_factors": [...],
      "recommended_actions": [...]
    }
```

#### 3. **VECTOR SEARCH (Conformidade)**
```
POST /vector/insert
  - Inserir documento corporativo no índice vetorial
  - Documentos = políticas, procedures, governance docs

POST /vector/search
  Request:
    {
      "query_text": "...",
      "top_k": 5,
      "similarity_threshold": 0.3
    }
  Response: documentos similares com scores
```

#### 4. **REPORTS**
```
GET /reports
  - Listar todos os relatórios

GET /reports/{report_id}
  - Detalhes de um relatório

GET /reports/{report_id}/explain
  - Explicação narrativa por LLM
```

#### 5. **FEEDBACK (RLHF)**
```
POST /feedback
  - Enviar feedback sobre classificação
  - Scores: correctness, usefulness, timeliness, relevance
  - Sistema ajusta pesos automaticamente
```

---

## 🔧 SERVIÇOS IMPLEMENTADOS

### 1. **AudioProcessorService** 🆕
```python
from src.backend.services.AudioProcessorService import AudioProcessor, process_audio

# Uso simples
result = await process_audio("meeting.wav")

# Resultado contém:
- metadata: AudioMetadata
- transcription: TranscriptionResult
- speaker_analysis: SpeakerAnalysis
- sentiment: SentimentAnalysis
- keywords_found: List[KeywordMatch]
- summary: str
```

**Características:**
- Validação de arquivo (formato, tamanho)
- Transcrição com Whisper (Groq)
- Extração de MFCCs + análise de falantes
- Análise de sentimento (TextBlob)
- Detecção de palavras-chave

---

### 2. **VectorSearchService** 🆕
```python
from src.backend.services.VectorSearchService import VectorSearchEngine, get_vector_engine

engine = get_vector_engine()

# Buscar documentos similares
results = await engine.search_similar_documents(
    query_text="Sistema indisponível",
    top_k=5,
    similarity_threshold=0.3
)

# Calcular conformidade
conformity = engine.calculate_conformity_factor(
    transcript_text="...",
    top_k=5
)  # Retorna 0.0 (conforme) a 1.0 (divergente)

# Análise detalhada
analysis = await engine.analyze_conformity_detailed(
    transcript_text="...",
    top_k=5
)
```

**Características:**
- Modelo: sentence-transformers (multilíngue)
- Cálculo de similaridade de cosseno
- Fator de conformidade C = 1 - similaridade_média
- Cache de embeddings em memória
- Escalável para FAISS/QDRANT em produção

---

### 3. **ISOClassifierService** 🆕
```python
from src.backend.services.ISOClassifierService import classify_crisis, classify_crisis_detailed

# Classificação simples
classification = classify_crisis(probability=0.45, confidence=0.9)
# Retorna: CrisisClassification(level=RED, color="#FF0000", ...)

# Classificação detalhada
report = classify_crisis_detailed(
    probability=0.45,
    confidence=0.9,
    sentiment_polarity=-0.3,
    maturity_level=3.5,
    conformity_factor=0.2,
    contributing_factors=[...]
)
# Retorna: DetailedCrisisReport com ações recomendadas
```

**Características:**
- ISO 22324 colors: GREEN, YELLOW, ORANGE, RED
- Thresholds: 0.20, 0.40, 0.70
- Ações específicas por nível
- Score agregado de risco
- Análise de impactos

---

### 4. **C2M_Analysis** (Existente, integrado)
```python
from src.agents.orchestrator.C2M_Analysis import DecisionTreeAnalyzer, MonteCarloProbabilityCalculator

# Decision Tree (Estágio 2)
is_crisis, score, reasoning = DecisionTreeAnalyzer.evaluate(
    sentiment=sentiment_obj,
    event_type="Ataque cibernético",
    context=context_obj
)

# Monte Carlo (Estágio 3)
probability_pct, scenarios = MonteCarloProbabilityCalculator.run_simulation(
    risk_agents=[...],
    context=context_obj,
    sentiment_polarity=-0.3,
    num_simulations=50000
)
```

---

## 📚 MODELOS DE DADOS

### AudioProcessingResult
```python
@dataclass
class AudioProcessingResult:
    metadata: AudioMetadata
    transcription: TranscriptionResult
    speaker_analysis: SpeakerAnalysis
    sentiment: SentimentAnalysis
    keywords_found: List[KeywordMatch]
    summary: str
    timestamp_processed: str
    processing_time_seconds: float
```

### CrisisClassification
```python
@dataclass
class CrisisClassification:
    probability: float
    level: CrisisLevel  # GREEN, YELLOW, ORANGE, RED
    color: str
    action_required: str
    description: str
    confidence_score: float
    timestamp: str
```

### ConformityAnalysisResult
```python
@dataclass
class ConformityAnalysisResult:
    conformity_factor: float  # 0-1
    similarity_score: float
    top_matches: List[VectorSearchResult]
    reasoning: str
```

---

## ⚙️ CONFIGURAÇÃO

### .env (exemplo)
```
# API Keys
API_KEY=sk-...  # Groq API Key

# Database
DATABASE_URL=sqlite:///./queto.db

# Model
SENTENCE_TRANSFORMER_MODEL=distiluse-base-multilingual-case-sensitive-v2

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=False

# Monte Carlo
MONTE_CARLO_SIMULATIONS=50000

# Crisis Thresholds
CRISIS_PROBABILITY_THRESHOLD=0.5
CRISIS_DECISION_THRESHOLD=0.4
```

---

## 🚀 EXECUÇÃO

### Desenvolvimento
```bash
cd Sistema-Queto

# Instalar dependências
pip install -r requirements.txt

# Rodar servidor
python -m uvicorn src.backend.server:app --reload --host 0.0.0.0 --port 8000

# Acessar:
# - API: http://localhost:8000/api/v1
# - Docs: http://localhost:8000/docs
# - ReDoc: http://localhost:8000/redoc
```

### Produção (Docker)
```bash
docker-compose up -d

# Verificar status
curl http://localhost:8000/api/v1/health
```

---

## 🧪 TESTES

```bash
# Rodar todos os testes
pytest tests/

# Com cobertura
pytest tests/ --cov=src --cov-report=html

# Teste específico
pytest tests/test_vector_search.py -v
```

---

## 📊 FLUXO COMPLETO DE EXEMPLO

```python
# 1. Upload de áudio
response = await client.post(
    "/api/v1/audio/upload",
    files={"file": open("meeting.wav", "rb")},
    params={"consent": True}
)
meeting_id = response["meeting_id"]

# 2. Processar e calcular crise
request_data = {
    "sentiment_polarity": -0.3,  # De transcrição
    "maturity_level": 3.5,
    "has_risk_plan": True,
    "risk_severity_scores": [0.4, 0.6],
    "transcript_text": "Texto transcrito..."
}
response = await client.post("/api/v1/crisis/probability", json=request_data)
probability = response["probability"]
iso_level = response["iso_level"]

# 3. Buscar conformidade
search_request = {
    "query_text": "Texto transcrito",
    "top_k": 5
}
similar_docs = await client.post("/api/v1/vector/search", json=search_request)

# 4. Enviar feedback
await client.post(
    "/api/v1/feedback",
    params={
        "report_id": report_id,
        "correctness": 5,
        "usefulness": 4,
        "timeliness": 5,
        "relevance": 5,
        "comment": "Classificação correta"
    }
)
```

---

## 🔐 SEGURANÇA & CONFORMIDADE

- **LGPD**: Consentimento obrigatório, anonimização de PII, descarte de áudio bruto
- **ISO 27001**: API Key, logs auditados, TLS support
- **ISO 31000**: Gestão de riscos integrada
- **ISO 22324**: Codificação de cores
- **ISO 22361**: Estrutura de resposta a crises

---

## 📈 PRÓXIMAS EVOLUÇÕES

1. **PostgreSQL + Redis** em produção
2. **FAISS/Qdrant** para índice vetorial escalável
3. **WebSocket** para monitoramento em tempo real
4. **Dashboard** executivo (React/Vue)
5. **Integração SIEM** (logs, eventos)
6. **Modelo Fine-tuned** para português
7. **Auto-scaling** na nuvem (AWS/Azure)

---

**Documento versão 2.0 - Maio 2024**
**Mantido por: Tim de Desenvolvimento**
