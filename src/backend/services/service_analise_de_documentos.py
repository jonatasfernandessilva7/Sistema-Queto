import numpy as np
import torch

from gensim.models import KeyedVectors
from src.backend.utils.pdf_reader import PDFReader
from src.backend.utils.preprocessor import Preprocessor
from src.backend.utils.bert_model import BertModel
from src.backend.utils.analyzer import Analyzer
from src.backend.utils.llm_integration import analise_com_llm 

class DocumentAnalyzer:

    def __init__(self, bert_model_path='jackaduma/SecBERT', word2vec_model_path='word2Vec_models/skip_s50.txt'):
        self.pdf_reader = PDFReader()
        self.preprocessor = Preprocessor()
        self.bert_model = BertModel(bert_model_path)
        self.analyzer = Analyzer()

        try:
            self.word2vec_model = KeyedVectors.load_word2vec_format(word2vec_model_path, binary=False)

        except FileNotFoundError:

            print(f"Erro: Modelo Word2Vec não encontrado em {word2vec_model_path}. Certifique-se de que o caminho está correto e o arquivo existe.")
            self.word2vec_model = None

    def _document_to_vec(self, words):
        
        if self.word2vec_model is None:
            return np.zeros(50)
        
        vectors = [self.word2vec_model[word] for word in words if word in self.word2vec_model]
        return np.mean(vectors, axis=0) if vectors else np.zeros(self.word2vec_model.vector_size)

    async def analyze_pdf(self, file_path: str, train_embeddings: list = None):

        """
        Executa a análise completa de um arquivo PDF.
        Args:
            file_path: Caminho para o arquivo PDF a ser analisado.
            train_embeddings: Opcional. Lista de embeddings de documentos de treinamento para comparação.
        Returns:
            Um dicionário contendo o relatório de análise.
        """

        text = self.pdf_reader.extract_text(file_path)

        processed_text = self.preprocessor.process(text)
        analysis_data = {
            "details": self.preprocessor.analyze_details(processed_text),
            "complexity": self.preprocessor.analyze_complexity(processed_text),
            "style": self.preprocessor.analyze_style(processed_text),
            "vocabulary_diversity": self.preprocessor.analyze_vocabulary(processed_text),
            "key_terms": list(self.preprocessor.extract_key_terms(processed_text)),
            "topics": self.preprocessor.analyze_topics(processed_text)
        }

        bert_embedding = self.bert_model.get_embeddings(processed_text)
        w2v_embedding = self._document_to_vec(processed_text.split())
        
        w2v_embedding_tensor = torch.from_numpy(w2v_embedding).float() 
        
        if bert_embedding.dim() > 1:
            bert_embedding = bert_embedding.squeeze(0)

        combined_embedding = torch.cat(
            (bert_embedding.detach(), w2v_embedding_tensor), dim=0)

        similarity_feedback = "Nenhuma comparação com documentos de treinamento realizada."
        if train_embeddings:
            avg_distance = self.analyzer.average_distance_to_train_docs(combined_embedding, train_embeddings)
            similarity_feedback = "O documento se alinha com os padrões de treinamento." if avg_distance <= 0.21 else "O documento difere significativamente dos padrões de treinamento."

        llm_feedback = await analise_com_llm(text, analysis_data) 

        report = {
            "file_path": file_path,
            "statistical_analysis": similarity_feedback,
            "detailed_analysis_metrics": analysis_data,
            "llm_crisis_evaluation": llm_feedback
        }
        
        return report