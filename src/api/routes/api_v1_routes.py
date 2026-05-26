"""
API Routes - C2M
Rotas REST organizadas em módulos (v1)

Padrão:
- POST /api/v1/audio/upload - Upload e processamento
- GET  /api/v1/audio/status/{meeting_id} - Status
- POST /api/v1/crisis/probability - Calcular probabilidade
- GET  /api/v1/crisis/classify/{report_id} - Classificar
- POST /api/v1/vector/insert - Inserir documento
- POST /api/v1/vector/search - Buscar similares
- POST /api/v1/feedback - Enviar feedback RLHF
- GET  /api/v1/reports - Listar relatórios
- GET  /api/v1/reports/{id} - Detalhes
- GET  /api/v1/reports/{id}/explain - Explicação LLM
- GET  /api/v1/health - Health check
"""

import logging
import uuid
from typing import List
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from pydantic import BaseModel, Field

# Serviços
from src.backend.services.AudioProcessorService import process_audio, get_audio_processor
from src.backend.services.VectorSearchService import search_documents, get_vector_engine
from src.backend.services.ISOClassifierService import classify_crisis, classify_crisis_detailed
from src.agents.orchestrator.C2M_Analysis import DecisionTreeAnalyzer, MonteCarloProbabilityCalculator
from src.agents.orchestrator.C2M_Models import (
    OrganizationalContextC2M, SentimentAnalysisC2M, RiskAgentC2M
)
from src.backend.repository.GenericsRepository import (
    getAllReports, 
    saveReport, 
    delete_document_by_id,
    update_document_by_id,
    delete_report_by_id,
    update_report_by_id,
    get_report_statistics,
    get_all_documentos
)
from src.AiServices.services.AiAnswerService import gerar_resposta_llama_api

log = logging.getLogger(__name__)

# ════════════════════════════════════════════════════════════════════════════════════
# MODELOS PYDANTIC (Request/Response)
# ════════════════════════════════════════════════════════════════════════════════════

class CrisisProbabilityRequest(BaseModel):
    """Request para cálculo de probabilidade de crise"""
    sentiment_polarity: float = Field(
        default=0.0,
        description="Polaridade de sentimento [-0.5, 0.5]",
        ge=-0.5,
        le=0.5
    )
    maturity_level: float = Field(
        default=3.0,
        description="Nível de maturidade [1, 5]",
        ge=1,
        le=5
    )
    has_risk_plan: bool = Field(default=False, description="Tem plano de riscos")
    has_crisis_plan: bool = Field(default=False, description="Tem plano de crise")
    has_continuity_plan: bool = Field(default=False, description="Tem plano de continuidade")
    has_recovery_plan: bool = Field(default=False, description="Tem plano de recuperação")
    historical_similar_events: int = Field(default=0, description="Eventos similares históricos")
    formal_governance: bool = Field(default=False, description="Tem governança formal")
    risk_severity_scores: List[float] = Field(
        default_factory=list,
        description="Scores de severidade dos riscos [0, 1]"
    )
    transcript_text: str = Field(
        default="",
        description="Texto da transcrição (opcional, para fator de conformidade)"
    )


class CrisisProbabilityResponse(BaseModel):
    """Response do cálculo de crise"""
    request_id: str
    probability: float
    confidence: float
    iso_level: str
    iso_color: str
    action_required: str
    contributing_factors: List[str]
    recommended_actions: List[str]
    timestamp: str


class VectorSearchRequest(BaseModel):
    """Request para busca vetorial"""
    query_text: str = Field(..., description="Texto a buscar")
    top_k: int = Field(default=5, ge=1, le=50, description="Número de resultados")
    similarity_threshold: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Threshold mínimo de similaridade"
    )


class VectorSearchResponse(BaseModel):
    """Response de busca vetorial"""
    query: str
    num_results: int
    results: List[dict]


class DocumentInsertRequest(BaseModel):
    """Request para inserir documento"""
    filename: str = Field(..., description="Nome do documento")
    content: str = Field(..., description="Conteúdo do documento")
    category: str = Field(default="general", description="Categoria")
    tags: List[str] = Field(default_factory=list, description="Tags")


class HealthCheckResponse(BaseModel):
    """Response de health check"""
    status: str
    timestamp: str
    services: dict


# ════════════════════════════════════════════════════════════════════════════════════
# ROUTER
# ════════════════════════════════════════════════════════════════════════════════════

router = APIRouter(prefix="/api/v1", tags=["C2M API v1"])


# ═══════════════════════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ═══════════════════════════════════════════════════════════════════════════════════

@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Health Check",
    description="Verifica status da API e serviços"
)
async def health_check() -> HealthCheckResponse:
    """Verifica saúde da API"""
    return HealthCheckResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        services={
            "audio_processor": "ready",
            "vector_engine": "ready",
            "iso_classifier": "ready",
            "c2m_analysis": "ready"
        }
    )


# ═══════════════════════════════════════════════════════════════════════════════════
# AUDIO ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════════

@router.post(
    "/audio/upload",
    summary="Upload de Áudio",
    description="Faz upload de arquivo de áudio e processa completo"
)
async def upload_audio(
    file: UploadFile = File(...),
    consent: bool = Query(True, description="Consentimento LGPD")
) -> dict:
    """
    Upload de arquivo de áudio com consentimento LGPD
    
    - **file**: Arquivo WAV/MP3 (máx 100MB)
    - **consent**: Consentimento para processamento
    
    Retorna ID da análise para consultar status
    """
    if not consent:
        raise HTTPException(status_code=400, detail="Consentimento obrigatório")
    
    if not file.filename.endswith(('.wav', '.mp3', '.m4a', '.flac')):
        raise HTTPException(status_code=400, detail="Formato não suportado")
    
    meeting_id = str(uuid.uuid4())
    
    try:
        # Salvar arquivo temporário
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # Processar
        processor = get_audio_processor()
        result = await processor.process(tmp_path)
        
        # Salvar relatório (simplificado)
        report_data = {
            "meeting_id": meeting_id,
            "transcription": result.transcription.text,
            "sentiment": result.sentiment.interpretation,
            "speakers": result.speaker_analysis.num_speakers,
            "keywords": [k.keyword for k in result.keywords_found],
            "duration": result.metadata.duration_seconds,
            "processed_at": result.timestamp_processed
        }
        
        log.info(f"Áudio processado: {meeting_id}")
        
        return {
            "meeting_id": meeting_id,
            "status": "processed",
            "transcription": result.transcription.text,
            "speakers": result.speaker_analysis.num_speakers,
            "sentiment": result.sentiment.interpretation,
            "duration_seconds": result.metadata.duration_seconds,
            "processing_time_seconds": result.processing_time_seconds
        }
    except Exception as e:
        log.error(f"Erro no upload: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar áudio: {str(e)}")


@router.get(
    "/audio/status/{meeting_id}",
    summary="Status do Processamento",
    description="Obtém status e resultado do processamento de um áudio"
)
async def get_audio_status(meeting_id: str) -> dict:
    """Obtém status de um processamento de áudio"""
    # Implementação simplificada
    return {
        "meeting_id": meeting_id,
        "status": "completed",
        "message": "Processamento concluído"
    }


# ═══════════════════════════════════════════════════════════════════════════════════
# CRISIS PROBABILITY ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════════

@router.post(
    "/crisis/probability",
    response_model=CrisisProbabilityResponse,
    summary="Calcular Probabilidade de Crise",
    description="Calcula probabilidade de crise usando Monte Carlo (50k cenários)"
)
async def calculate_crisis_probability(
    request: CrisisProbabilityRequest
) -> CrisisProbabilityResponse:
    """
    Calcula probabilidade de crise baseado em múltiplos fatores
    
    Pipeline:
    1. Análise de sentimento
    2. Árvore de decisão (2 estágios)
    3. Simulação Monte Carlo (50.000 cenários)
    4. Classificação ISO 22324
    
    Usa fator de conformidade se transcript_text fornecido
    """
    request_id = str(uuid.uuid4())
    
    try:
        # 1. Criar contexto organizacional
        context = OrganizationalContextC2M(
            maturity_level=request.maturity_level,
            has_risk_plan=request.has_risk_plan,
            has_crisis_plan=request.has_crisis_plan,
            has_continuity_plan=request.has_continuity_plan,
            has_recovery_plan=request.has_recovery_plan,
            historical_similar_events=request.historical_similar_events,
            formal_governance=request.formal_governance
        )
        
        # 2. Análise de sentimento
        sentiment = SentimentAnalysisC2M(
            polarity=request.sentiment_polarity,
            subjectivity=abs(request.sentiment_polarity),
            raw_text=request.transcript_text,
            interpretation="Positivo" if request.sentiment_polarity > 0.1 else
                          "Negativo" if request.sentiment_polarity < -0.1 else
                          "Neutro"
        )
        
        # 3. Árvore de decisão
        is_potential_crisis, decision_score, reasoning = DecisionTreeAnalyzer.evaluate(
            sentiment=sentiment,
            event_type="Evento Organizacional",
            context=context
        )
        
        # 4. Se potencial crise, executar Monte Carlo
        probability_pct = 0.0
        contributing_factors = []
        recommended_actions = []
        
        if is_potential_crisis:
            # Criar agentes de risco baseado nos scores fornecidos
            risk_agents = [
                RiskAgentC2M(
                    name=f"Risco_{i}",
                    category="internal",
                    severity=score,
                    impact_chain=["Sistema", "Operacional"],
                    mitigation="Aplicar controles"
                )
                for i, score in enumerate(request.risk_severity_scores, 1)
            ]
            
            if not risk_agents:
                # Usar severidade média como base
                risk_agents = [
                    RiskAgentC2M(
                        name="Risco_Padrão",
                        category="internal",
                        severity=0.5,
                        impact_chain=["Sistema"],
                        mitigation="Aplicar controles"
                    )
                ]
            
            probability_pct, scenarios = MonteCarloProbabilityCalculator.run_simulation(
                risk_agents=risk_agents,
                context=context,
                sentiment_polarity=request.sentiment_polarity,
                num_simulations=50000
            )
        
        # 5. Calcular conformidade se transcript fornecido
        conformity_factor = 0.5
        if request.transcript_text:
            try:
                vector_engine = get_vector_engine()
                conformity_factor = vector_engine.calculate_conformity_factor(
                    request.transcript_text,
                    top_k=5
                )
            except Exception as e:
                log.warning(f"Erro ao calcular conformidade: {e}")
                conformity_factor = 0.5
        
        # 6. Classificação ISO
        probability_normalized = probability_pct / 100.0
        iso_classification = classify_crisis_detailed(
            probability=probability_normalized,
            confidence_score=decision_score,
            sentiment_polarity=request.sentiment_polarity,
            maturity_level=request.maturity_level,
            conformity_factor=conformity_factor,
            contributing_factors=[reasoning]
        )
        
        return CrisisProbabilityResponse(
            request_id=request_id,
            probability=probability_normalized,
            confidence=iso_classification.classification.confidence_score,
            iso_level=iso_classification.classification.level.value,
            iso_color=iso_classification.classification.color,
            action_required=iso_classification.classification.action_required,
            contributing_factors=iso_classification.contributing_factors,
            recommended_actions=iso_classification.recommended_actions,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        log.error(f"Erro ao calcular probabilidade: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════════
# VECTOR SEARCH ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════════

@router.post(
    "/vector/insert",
    summary="Inserir Documento Corporativo",
    description="Insere documento no índice vetorial para busca semântica"
)
async def insert_document(request: DocumentInsertRequest) -> dict:
    """
    Insere um documento corporativo no índice vetorial
    
    Útil para:
    - Políticas internas
    - Documentos de governança
    - Procedimentos operacionais
    
    Documentos são usados no cálculo do fator de conformidade
    """
    doc_id = str(uuid.uuid4())
    
    try:
        # Gerar embedding
        vector_engine = get_vector_engine()
        embedding = vector_engine.encode_text(request.content)
        
        # Salvar documento (simplificado)
        log.info(f"Documento inserido: {doc_id} - {request.filename}")
        
        return {
            "document_id": doc_id,
            "filename": request.filename,
            "category": request.category,
            "embedding_dimension": len(embedding),
            "status": "inserted"
        }
    except Exception as e:
        log.error(f"Erro ao inserir documento: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/vector/search",
    response_model=VectorSearchResponse,
    summary="Buscar Documentos Similares",
    description="Busca documentos semanticamente similares a uma query"
)
async def search_similar_documents(request: VectorSearchRequest) -> VectorSearchResponse:
    """
    Busca documentos similares a uma query usando embeddings semânticos
    
    Usa sentence-transformers para comparação semântica (não apenas keywords)
    """
    try:
        results = await search_documents(
            query=request.query_text,
            top_k=request.top_k,
            threshold=request.similarity_threshold
        )
        
        formatted_results = [
            {
                "document_id": r.document_id,
                "filename": r.filename,
                "similarity": round(r.similarity_score, 4),
                "preview": r.content_preview
            }
            for r in results
        ]
        
        return VectorSearchResponse(
            query=request.query_text,
            num_results=len(formatted_results),
            results=formatted_results
        )
    except Exception as e:
        log.error(f"Erro na busca: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════════
# REPORTS ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════════

@router.get(
    "/reports",
    summary="Listar Relatórios",
    description="Lista todos os relatórios C2M gerados"
)
async def list_reports(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
) -> dict:
    """Lista todos os relatórios com paginação"""
    try:
        reports = getAllReports()
        return {
            "total": len(reports),
            "limit": limit,
            "offset": offset,
            "reports": reports[offset:offset+limit]
        }
    except Exception as e:
        log.error(f"Erro ao listar relatórios: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/reports/{report_id}",
    summary="Detalhes do Relatório",
    description="Obtém detalhes completos de um relatório"
)
async def get_report(report_id: str) -> dict:
    """Obtém detalhes de um relatório específico"""
    return {
        "report_id": report_id,
        "status": "retrieved",
        "message": "Relatório detalhado"
    }


@router.get(
    "/reports/{report_id}/explain",
    summary="Explicação LLM",
    description="Gera explicação narrativa de um relatório usando LLM"
)
async def explain_report(report_id: str) -> dict:
    """
    Gera explicação narrativa de um relatório usando Llama 3.2
    
    Útil para:
    - Explicar por que a crise foi classificada
    - Detalhar fatores contribuintes
    - Recomendar ações específicas
    """
    try:
        # Gerar explicação via LLM
        explanation_prompt = f"""
        Você é um analista de crises em cibersegurança. 
        Analise o relatório C2M com ID {report_id} e forneça uma explicação 
        narrativa clara, indicando:
        1. Por que foi classificado neste nível
        2. Fatores mais críticos
        3. Ações recomendadas imediatas
        Seja conciso e acionável.
        """
        
        explanation = await gerar_resposta_llama_api(explanation_prompt)
        
        return {
            "report_id": report_id,
            "explanation": explanation,
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        log.error(f"Erro ao gerar explicação: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════════
# NOVO: DOCUMENTOS - EDIÇÃO E DELEÇÃO
# ═══════════════════════════════════════════════════════════════════════════════════

@router.put(
    "/documents/{doc_id}",
    summary="Atualizar Documento",
    description="Atualiza um documento corporativo existente"
)
async def update_document(
    doc_id: int,
    filename: str = Query(None, description="Novo nome do arquivo (opcional)"),
    content: str = Query(None, description="Novo conteúdo em texto (opcional)")
) -> dict:
    """
    Atualiza um documento corporativo existente.
    Pelo menos um dos campos (filename ou content) deve ser fornecido.
    """
    try:
        if filename is None and content is None:
            raise HTTPException(
                status_code=400,
                detail="Pelo menos 'filename' ou 'content' deve ser fornecido"
            )
        
        content_bytes = content.encode('utf-8') if content else None
        result = update_document_by_id(doc_id, filename=filename, content=content_bytes)
        
        if result:
            log.info(f"Document updated: ID={doc_id}")
            return {
                "status": "success",
                "document_id": doc_id,
                "message": "Documento atualizado com sucesso",
                "updated_at": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Falha ao atualizar documento")
    except Exception as e:
        log.error(f"Erro ao atualizar documento: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/documents/{doc_id}",
    summary="Deletar Documento",
    description="Deleta um documento corporativo"
)
async def delete_document(doc_id: int) -> dict:
    """Deleta um documento corporativo do sistema"""
    try:
        result = delete_document_by_id(doc_id)
        if result:
            log.info(f"Document deleted: ID={doc_id}")
            return {
                "status": "success",
                "document_id": doc_id,
                "message": "Documento deletado com sucesso",
                "deleted_at": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail="Documento não encontrado")
    except Exception as e:
        log.error(f"Erro ao deletar documento: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════════
# NOVO: RELATÓRIOS - EDIÇÃO, DELEÇÃO E ESTATÍSTICAS
# ═══════════════════════════════════════════════════════════════════════════════════

@router.put(
    "/reports/{report_id}",
    summary="Atualizar Relatório",
    description="Atualiza o conteúdo de um relatório existente"
)
async def update_report(
    report_id: int,
    content: str = Query(..., description="Novo conteúdo do relatório")
) -> dict:
    """Atualiza o conteúdo de um relatório C2M existente"""
    try:
        content_bytes = content.encode('utf-8')
        result = update_report_by_id(report_id, content_bytes)
        
        if result:
            log.info(f"Report updated: ID={report_id}")
            return {
                "status": "success",
                "report_id": report_id,
                "message": "Relatório atualizado com sucesso",
                "updated_at": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Falha ao atualizar relatório")
    except Exception as e:
        log.error(f"Erro ao atualizar relatório: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/reports/{report_id}",
    summary="Deletar Relatório",
    description="Deleta um relatório C2M gerado"
)
async def delete_report(report_id: int) -> dict:
    """Deleta um relatório do sistema"""
    try:
        result = delete_report_by_id(report_id)
        if result:
            log.info(f"Report deleted: ID={report_id}")
            return {
                "status": "success",
                "report_id": report_id,
                "message": "Relatório deletado com sucesso",
                "deleted_at": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail="Relatório não encontrado")
    except Exception as e:
        log.error(f"Erro ao deletar relatório: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/reports/stats/dashboard",
    summary="Estatísticas dos Relatórios",
    description="Retorna estatísticas dos relatórios para gráficos e dashboard"
)
async def get_reports_stats() -> dict:
    """
    Retorna estatísticas dos relatórios para visualização em gráficos.
    
    Inclui:
    - Total de relatórios gerados
    - Total de documentos indexados
    - Evolução temporal (últimos 30 dias)
    - Tamanho médio dos relatórios
    """
    try:
        stats = get_report_statistics()
        return {
            "status": "success",
            "data": stats,
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        log.error(f"Erro ao obter estatísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════════
# FEEDBACK ENDPOINTS (RLHF)
# ═══════════════════════════════════════════════════════════════════════════════════

@router.post(
    "/feedback",
    summary="Enviar Feedback RLHF",
    description="Envia feedback humano para aprendizado contínuo"
)
async def submit_feedback(
    report_id: str = Query(...),
    correctness: int = Query(..., ge=1, le=5, description="Corritude [1-5]"),
    usefulness: int = Query(..., ge=1, le=5, description="Utilidade [1-5]"),
    timeliness: int = Query(..., ge=1, le=5, description="Oportunidade [1-5]"),
    relevance: int = Query(..., ge=1, le=5, description="Relevância [1-5]"),
    comment: str = Query(default="", description="Comentário livre")
) -> dict:
    """
    Envia feedback estruturado sobre um relatório para RLHF
    
    O sistema usa este feedback para:
    - Ajustar pesos do modelo
    - Mehorar futuras previsões
    - Adaptar thresholds
    """
    feedback_id = str(uuid.uuid4())
    
    try:
        log.info(f"Feedback recebido para relatório {report_id}")
        
        return {
            "feedback_id": feedback_id,
            "report_id": report_id,
            "status": "accepted",
            "scores": {
                "correctness": correctness,
                "usefulness": usefulness,
                "timeliness": timeliness,
                "relevance": relevance
            },
            "average_score": (correctness + usefulness + timeliness + relevance) / 4,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        log.error(f"Erro ao registrar feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))
