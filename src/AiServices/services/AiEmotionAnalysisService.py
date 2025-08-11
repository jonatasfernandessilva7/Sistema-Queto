from textblob import TextBlob

"""
This function calculate level emotion, positive or negative whit based on polarity voice
"""
def emotionAnalysis(texto: str):

    try:
        if not texto or not texto.strip():
            return {"error": "empty text"}

        blob = TextBlob(texto)
        polarity = blob.sentiment.polarity
        emotion = (
            "positive" if polarity > 0.1 else
            "negative" if polarity < -0.1 else
            "neutral"
        )

        return {
            "polarity": polarity,
            "emotion": emotion
        }

    except Exception as e:
        return {"error": f"Error in emotion analysis: {e}"}
