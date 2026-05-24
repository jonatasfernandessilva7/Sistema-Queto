# Quick Start - C2M v2.0

## 🚀 Comece em 5 minutos

### 1. Setup Inicial

```bash
# Clone/navegue até a pasta
cd Sistema-Queto

# Crie ambiente virtual
python -m venv venv

# Ative
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instale dependências
pip install -r requirements.txt

# Configure .env
cp .env.example .env
# Edite .env e adicione sua GROQ_API_KEY
```

### 2. Rodar o Server

```bash
# Desenvolvimento (com reload automático)
python -m uvicorn src.backend.server:app --reload --host 0.0.0.0 --port 8000

# Output esperado:
# ════════════════════════════════════════════════════════════════════════
# 🚀 Queto System (C2M) iniciando...
# ════════════════════════════════════════════════════════════════════════
# ✓ FastAPI configurado
# ✓ Banco de dados inicializado
# ✓ Rotas registradas
# ════════════════════════════════════════════════════════════════════════
```

### 3. Acesse a Documentação

- **Swagger UI (Interativa)**: http://localhost:8000/docs
- **ReDoc (Leitura)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/v1/health

---

## 📝 Exemplos de Uso

### Exemplo 1: Upload e Processamento de Áudio

```bash
curl -X POST "http://localhost:8000/api/v1/audio/upload?consent=true" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@meeting.wav"

# Response:
{
  "meeting_id": "uuid",
  "status": "processed",
  "transcription": "Texto transcrito do áudio...",
  "speakers": 2,
  "sentiment": "Negativo",
  "duration_seconds": 120.5,
  "processing_time_seconds": 8.3
}
```

### Exemplo 2: Calcular Probabilidade de Crise

```bash
curl -X POST "http://localhost:8000/api/v1/crisis/probability" \
  -H "Content-Type: application/json" \
  -d '{
    "sentiment_polarity": -0.3,
    "maturity_level": 3.5,
    "has_risk_plan": true,
    "has_crisis_plan": false,
    "has_continuity_plan": true,
    "has_recovery_plan": false,
    "historical_similar_events": 2,
    "formal_governance": true,
    "risk_severity_scores": [0.4, 0.6, 0.5],
    "transcript_text": "Sistema indisponível por ataque"
  }'

# Response:
{
  "request_id": "uuid",
  "probability": 0.45,
  "confidence": 0.87,
  "iso_level": "LARANJA",
  "iso_color": "#FF8800",
  "action_required": "Ativar comitê de crise",
  "contributing_factors": ["Sentimento negativo", ...],
  "recommended_actions": ["Convocar comitê IMEDIATAMENTE", ...],
  "timestamp": "2024-05-22T10:30:00"
}
```

### Exemplo 3: Buscar Documentos Similares (Vector Search)

```bash
# Primeiro, inserir um documento corporativo
curl -X POST "http://localhost:8000/api/v1/vector/insert" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "politica_seguranca.pdf",
    "content": "Política de segurança da informação...",
    "category": "governance"
  }'

# Depois, buscar documentos similares
curl -X POST "http://localhost:8000/api/v1/vector/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "Sistema indisponível por ataque",
    "top_k": 5,
    "similarity_threshold": 0.3
  }'

# Response:
{
  "query": "Sistema indisponível por ataque",
  "num_results": 3,
  "results": [
    {
      "document_id": "uuid",
      "filename": "politica_seguranca.pdf",
      "similarity": 0.687,
      "preview": "Política de segurança da informação..."
    },
    ...
  ]
}
```

### Exemplo 4: Enviar Feedback (RLHF)

```bash
curl -X POST "http://localhost:8000/api/v1/feedback?report_id=uuid&correctness=5&usefulness=4&timeliness=5&relevance=5&comment=Classificacao%20correta"

# Response:
{
  "feedback_id": "uuid",
  "report_id": "uuid",
  "status": "accepted",
  "scores": {
    "correctness": 5,
    "usefulness": 4,
    "timeliness": 5,
    "relevance": 5
  },
  "average_score": 4.75,
  "timestamp": "2024-05-22T10:35:00"
}
```

---

## 🧪 Rodar Testes

```bash
# Todos os testes
pytest tests/

# Teste específico
pytest tests/test_vector_search.py -v

# Com cobertura
pytest tests/ --cov=src --cov-report=html

# Abrir relatório
open htmlcov/index.html
```

---

## 🔍 Logs e Debugging

### Ver logs em tempo real

```bash
# Terminal 1: Rodar servidor com logging verboso
python -m uvicorn src.backend.server:app --reload --log-level debug

# Terminal 2: Fazer requisições
curl http://localhost:8000/api/v1/health
```

### Estrutura de logs

```
2024-05-22 10:30:00 - src.backend.services.AudioProcessorService - INFO - AudioProcessor inicializado
2024-05-22 10:30:05 - src.backend.services.VectorSearchService - INFO - Modelo carregado: distiluse-base-multilingual-case-sensitive-v2
2024-05-22 10:30:10 - src.backend.server - INFO - 🚀 Queto System (C2M) iniciando...
```

---

## 🐳 Rodar com Docker

```bash
# Build
docker-compose build

# Run
docker-compose up -d

# Logs
docker-compose logs -f api

# Stop
docker-compose down
```

---

## 📊 Estrutura de Resposta Completa

### Crisis Probability Response (Detalhado)

```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "probability": 0.45,
  "confidence": 0.87,
  "iso_level": "LARANJA",
  "iso_color": "#FF8800",
  "action_required": "Ativar comitê de crise",
  "contributing_factors": [
    "Sentimento negativo: Negativo (polarity=-0.30)",
    "Tipo de evento crítico identificado: Evento Organizacional",
    "Governança inadequada (score=0.50)",
    "Maturidade adequada (3.50/5.0)"
  ],
  "recommended_actions": [
    "Convocar comitê de crise",
    "Ativar plano de continuidade",
    "Comunicar ao executivo",
    "Mobilizar equipes especializadas",
    "Iniciar comunicação de crise",
    "Estabelecer salas de guerra"
  ],
  "timestamp": "2024-05-22T10:30:45.123456"
}
```

---

## 🔐 Checklist de Segurança

- [ ] .env configurado (nunca commitar)
- [ ] API_KEY válida da Groq
- [ ] Database inicializado
- [ ] CORS configurado corretamente
- [ ] Logs habilitados
- [ ] TLS em produção
- [ ] Rate limiting configurado
- [ ] Backup de banco de dados

---

## ❓ FAQ

**P: Qual é a precisão do modelo C2M?**
R: O modelo foi validado com 50.000 simulações Monte Carlo. Acurácia depende da qualidade dos dados de entrada.

**P: Posso usar sem Groq API?**
R: Pode usar mock da transcrição editando `AudioProcessorService.py`.

**P: Como escalar para produção?**
R: Use PostgreSQL + Redis, implante em container (Docker/K8s), configure load balancer, adicione monitoramento.

**P: Preciso integrar com meu SIEM?**
R: Sim, pode criar novo endpoint em `api_v1_routes.py` que consome eventos do seu SIEM.

---

## 📞 Suporte

- 📧 Email: dev@sistema-queto.com
- 🐛 Issues: GitHub Issues
- 📚 Docs: `/docs/ARCHITECTURE_v2.md`
- 🎯 Roadmap: `/docs/project/ROADMAP.md`

---

**Última atualização: Maio 22, 2024**
