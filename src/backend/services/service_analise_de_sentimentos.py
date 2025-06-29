from textblob import TextBlob
from langdetect import detect

def analisar_sentimento(texto: str):
    try:
        if not texto or not texto.strip():
            return {"erro": "Texto vazio"}

        blob = TextBlob(texto)
        polaridade = blob.sentiment.polarity
        sentimento = (
            "positivo" if polaridade > 0.1 else
            "negativo" if polaridade < -0.1 else
            "neutro"
        )

        return {
            "polaridade": polaridade,
            "sentimento": sentimento
        }

    except Exception as e:
        return {"erro": f"Erro na análise de sentimento: {e}"}
