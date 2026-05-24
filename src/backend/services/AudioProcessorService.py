"""
Audio Processor Service - C2M
Unifica processamento de áudio de forma modular e robusta

Pipeline:
1. Carregamento e validação do arquivo
2. Transcrição (Whisper Groq)
3. Extração de características (MFCCs)
4. Análise de diarização (número de falantes)
5. Análise de sentimento
6. Detecção de palavras-chave
7. Geração de evento estruturado
"""

import logging
import os
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime
import asyncio

try:
    from groq import Groq
except ImportError:
    raise ImportError("groq is required. Install with: pip install groq")

try:
    import librosa
    import numpy as np
except ImportError:
    raise ImportError("librosa and numpy are required. Install with: pip install librosa numpy")

from sklearn.cluster import MiniBatchKMeans
from sklearn.metrics import silhouette_score
from textblob import TextBlob

from dotenv import load_dotenv

log = logging.getLogger(__name__)
load_dotenv()


@dataclass
class AudioMetadata:
    """Metadados do áudio"""
    filename: str
    duration_seconds: float
    sample_rate: int
    num_channels: int
    file_size_bytes: int
    timestamp: str


@dataclass
class TranscriptionResult:
    """Resultado da transcrição"""
    text: str
    language: str
    confidence: float
    duration_seconds: float


@dataclass
class SpeakerAnalysis:
    """Análise de falantes"""
    num_speakers: int
    confidence: float
    mfcc_features: Optional[np.ndarray] = None
    silhouette_scores: Optional[List[float]] = None


@dataclass
class SentimentAnalysis:
    """Análise de sentimento do texto"""
    polarity: float  # -1.0 a 1.0
    subjectivity: float  # 0.0 a 1.0
    interpretation: str


@dataclass
class KeywordMatch:
    """Correspondência de palavra-chave"""
    keyword: str
    count: int
    positions: List[int]


@dataclass
class AudioProcessingResult:
    """Resultado completo do processamento de áudio"""
    metadata: AudioMetadata
    transcription: TranscriptionResult
    speaker_analysis: SpeakerAnalysis
    sentiment: SentimentAnalysis
    keywords_found: List[KeywordMatch]
    summary: str
    timestamp_processed: str
    processing_time_seconds: float


class AudioProcessor:
    """
    Processador de áudio com múltiplos estágios
    
    Integra:
    - Transcrição (Whisper via Groq)
    - Análise de áudio (librosa MFCC)
    - Análise de sentimento (TextBlob)
    - Detecção de palavras-chave
    """
    
    def __init__(self):
        """Inicializa o processador"""
        self.groq_client = Groq(api_key=os.getenv("API_KEY"))
        self.crisis_keywords_path = "data_phrases_relationship_with_cyber_crisis/data.txt"
        self._crisis_keywords = self._load_crisis_keywords()
        log.info("AudioProcessor inicializado")
    
    def _load_crisis_keywords(self) -> List[str]:
        """Carrega palavras-chave de crise"""
        keywords = []
        try:
            if os.path.exists(self.crisis_keywords_path):
                with open(self.crisis_keywords_path, 'r', encoding='utf-8') as f:
                    keywords = [line.strip().lower() for line in f if line.strip()]
                log.info(f"Carregadas {len(keywords)} palavras-chave de crise")
            else:
                # Fallback: palavras-chave padrão
                keywords = [
                    "ataque", "attack", "intrusion", "intrusão", "falha", "failure",
                    "indisponível", "unavailable", "indisponibilidade", "unavailability",
                    "violação", "violation", "breach", "ransomware", "malware",
                    "comprometimento", "compromise", "roubo", "theft", "vazamento", "leak"
                ]
                log.warning(f"Arquivo de palavras-chave não encontrado, usando {len(keywords)} palavras padrão")
        except Exception as e:
            log.error(f"Erro ao carregar palavras-chave: {e}")
        
        return keywords
    
    async def validate_audio_file(self, filepath: str) -> Tuple[bool, str]:
        """
        Valida arquivo de áudio
        
        Args:
            filepath: Caminho do arquivo
        
        Returns:
            (is_valid, error_message)
        """
        if not os.path.exists(filepath):
            return False, f"Arquivo não encontrado: {filepath}"
        
        if os.path.getsize(filepath) == 0:
            return False, "Arquivo vazio"
        
        # Validar formato (wav, mp3, etc)
        valid_formats = ['.wav', '.mp3', '.m4a', '.flac']
        if not any(filepath.lower().endswith(fmt) for fmt in valid_formats):
            return False, f"Formato não suportado. Use: {', '.join(valid_formats)}"
        
        # Validar tamanho máximo (100MB)
        max_size = 100 * 1024 * 1024
        if os.path.getsize(filepath) > max_size:
            return False, "Arquivo excede 100MB"
        
        return True, ""
    
    async def extract_metadata(self, filepath: str) -> AudioMetadata:
        """Extrai metadados do arquivo de áudio"""
        try:
            # Carregar para obter info
            y, sr = librosa.load(filepath, sr=None)
            
            metadata = AudioMetadata(
                filename=os.path.basename(filepath),
                duration_seconds=librosa.get_duration(y=y, sr=sr),
                sample_rate=sr,
                num_channels=1 if len(y.shape) == 1 else y.shape[0],
                file_size_bytes=os.path.getsize(filepath),
                timestamp=datetime.now().isoformat()
            )
            
            log.info(f"Metadados extraídos: {metadata.duration_seconds:.2f}s em {sr}Hz")
            return metadata
        except Exception as e:
            log.error(f"Erro ao extrair metadados: {e}")
            raise
    
    async def transcribe_audio(self, filepath: str) -> TranscriptionResult:
        """
        Transcreve áudio usando Whisper (Groq)
        
        Args:
            filepath: Caminho do arquivo de áudio
        
        Returns:
            TranscriptionResult com texto e metadados
        """
        log.info(f"Iniciando transcrição: {filepath}")
        
        try:
            with open(filepath, "rb") as audio_file:
                transcription = self.groq_client.audio.transcriptions.create(
                    file=audio_file,
                    model="whisper-large-v3-turbo",
                    language="pt",
                    temperature=0.0
                )
            
            # Calcular duração a partir do arquivo
            y, sr = librosa.load(filepath, sr=None)
            duration = librosa.get_duration(y=y, sr=sr)
            
            result = TranscriptionResult(
                text=transcription.text,
                language="pt",
                confidence=1.0,  # Whisper não retorna confidence
                duration_seconds=duration
            )
            
            log.info(f"Transcrição completa. Texto: {len(result.text)} caracteres")
            return result
        except Exception as e:
            log.error(f"Erro na transcrição: {e}")
            raise
    
    async def analyze_speakers(
        self,
        filepath: str,
        max_clusters: int = 10
    ) -> SpeakerAnalysis:
        """
        Analisa número de falantes usando diarização
        
        Usa MFCC + KMeans com silhueta para determinar número ótimo
        
        Args:
            filepath: Caminho do áudio
            max_clusters: Máximo de clusters a testar
        
        Returns:
            SpeakerAnalysis com número de falantes
        """
        log.info("Analisando número de falantes...")
        
        try:
            # Carregar áudio
            y, sr = librosa.load(filepath, sr=None)
            
            # Extrair MFCCs (Mel-Frequency Cepstral Coefficients)
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20)
            mfccs = mfccs.T  # Transpor para amostras × features
            
            if len(mfccs) < 2:
                log.warning("Áudio muito curto para análise de diarização")
                return SpeakerAnalysis(
                    num_speakers=1,
                    confidence=0.5,
                    mfcc_features=mfccs,
                    silhouette_scores=[]
                )
            
            # Testar diferentes números de clusters
            silhouette_scores = []
            for n_clusters in range(1, min(max_clusters + 1, len(mfccs))):
                kmeans = MiniBatchKMeans(
                    n_clusters=n_clusters,
                    random_state=42,
                    n_init=10,
                    max_iter=300
                )
                labels = kmeans.fit_predict(mfccs)
                
                if len(np.unique(labels)) > 1:
                    score = silhouette_score(mfccs, labels)
                    silhouette_scores.append(score)
                else:
                    silhouette_scores.append(-1)
            
            # Encontrar número ótimo
            if silhouette_scores and max(silhouette_scores) > 0:
                optimal_clusters = np.argmax(silhouette_scores) + 1
                confidence = float(max(silhouette_scores))
            else:
                optimal_clusters = 1
                confidence = 0.3
            
            result = SpeakerAnalysis(
                num_speakers=optimal_clusters,
                confidence=confidence,
                mfcc_features=mfccs,
                silhouette_scores=silhouette_scores
            )
            
            log.info(f"Análise de falantes: {optimal_clusters} falantes (confiança: {confidence:.2%})")
            return result
        except Exception as e:
            log.error(f"Erro na análise de falantes: {e}")
            return SpeakerAnalysis(
                num_speakers=1,
                confidence=0.0
            )
    
    async def analyze_sentiment(self, text: str) -> SentimentAnalysis:
        """
        Analisa sentimento do texto transcrito
        
        Args:
            text: Texto a analisar
        
        Returns:
            SentimentAnalysis com polaridade e subjetividade
        """
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity
            
            if polarity > 0.1:
                interpretation = "Positivo"
            elif polarity < -0.1:
                interpretation = "Negativo"
            else:
                interpretation = "Neutro"
            
            result = SentimentAnalysis(
                polarity=polarity,
                subjectivity=subjectivity,
                interpretation=interpretation
            )
            
            log.info(f"Análise de sentimento: {interpretation} (polarity={polarity:.2f})")
            return result
        except Exception as e:
            log.error(f"Erro na análise de sentimento: {e}")
            return SentimentAnalysis(polarity=0.0, subjectivity=0.0, interpretation="Erro")
    
    async def detect_keywords(self, text: str) -> List[KeywordMatch]:
        """
        Detecta palavras-chave de crise no texto
        
        Args:
            text: Texto a analisar
        
        Returns:
            Lista de KeywordMatch encontrados
        """
        matches = {}
        text_lower = text.lower()
        text_words = text_lower.split()
        
        for keyword in self._crisis_keywords:
            keyword_lower = keyword.lower()
            count = text_lower.count(keyword_lower)
            
            if count > 0:
                # Encontrar posições
                positions = []
                start = 0
                while True:
                    pos = text_lower.find(keyword_lower, start)
                    if pos == -1:
                        break
                    positions.append(pos)
                    start = pos + 1
                
                if keyword not in matches:
                    matches[keyword] = KeywordMatch(
                        keyword=keyword,
                        count=count,
                        positions=positions
                    )
        
        result = list(matches.values())
        result.sort(key=lambda x: x.count, reverse=True)
        
        log.info(f"Detectadas {len(result)} palavras-chave distintas")
        return result
    
    async def process(self, filepath: str) -> AudioProcessingResult:
        """
        Processa arquivo de áudio completo
        
        Pipeline completo:
        1. Validação
        2. Metadados
        3. Transcrição
        4. Análise de falantes
        5. Sentimento
        6. Palavras-chave
        
        Args:
            filepath: Caminho do arquivo de áudio
        
        Returns:
            AudioProcessingResult com todos os resultados
        
        Raises:
            ValueError: Se arquivo inválido
        """
        start_time = datetime.now()
        
        # Validação
        is_valid, error_msg = await self.validate_audio_file(filepath)
        if not is_valid:
            raise ValueError(f"Arquivo inválido: {error_msg}")
        
        log.info(f"Iniciando processamento de: {filepath}")
        
        # Executar análises em paralelo quando possível
        metadata = await self.extract_metadata(filepath)
        transcription = await self.transcribe_audio(filepath)
        
        # Executar análises paralelas
        speaker_task = self.analyze_speakers(filepath)
        sentiment_task = self.analyze_sentiment(transcription.text)
        keywords_task = self.detect_keywords(transcription.text)
        
        speakers, sentiment, keywords = await asyncio.gather(
            speaker_task,
            sentiment_task,
            keywords_task
        )
        
        # Gerar resumo
        summary = self._generate_summary(
            transcription, speakers, sentiment, keywords
        )
        
        # Calcular tempo de processamento
        processing_time = (datetime.now() - start_time).total_seconds()
        
        result = AudioProcessingResult(
            metadata=metadata,
            transcription=transcription,
            speaker_analysis=speakers,
            sentiment=sentiment,
            keywords_found=keywords,
            summary=summary,
            timestamp_processed=datetime.now().isoformat(),
            processing_time_seconds=processing_time
        )
        
        log.info(f"Processamento completo em {processing_time:.2f}s")
        return result
    
    def _generate_summary(
        self,
        transcription: TranscriptionResult,
        speakers: SpeakerAnalysis,
        sentiment: SentimentAnalysis,
        keywords: List[KeywordMatch]
    ) -> str:
        """Gera resumo do processamento"""
        summary_parts = [
            f"Duração: {transcription.duration_seconds:.1f}s",
            f"Falantes: {speakers.num_speakers}",
            f"Sentimento: {sentiment.interpretation}",
            f"Palavras-chave: {len(keywords)}"
        ]
        
        if keywords:
            top_keywords = ", ".join([k.keyword for k in keywords[:3]])
            summary_parts.append(f"Top keywords: {top_keywords}")
        
        return " | ".join(summary_parts)


# Instância global
_audio_processor: Optional[AudioProcessor] = None


def get_audio_processor() -> AudioProcessor:
    """Retorna instância singleton do processador"""
    global _audio_processor
    if _audio_processor is None:
        _audio_processor = AudioProcessor()
    return _audio_processor


async def process_audio(filepath: str) -> AudioProcessingResult:
    """Helper para processar áudio"""
    processor = get_audio_processor()
    return await processor.process(filepath)
