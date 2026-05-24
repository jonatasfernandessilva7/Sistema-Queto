import os
import librosa
import numpy as np

from sklearn.cluster import MiniBatchKMeans
from sklearn.metrics import silhouette_score

from groq import Groq
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY)
phrases_crisis = "data_phrases_relationship_with_cyber_crisis/data.txt"

def audioRecognize(audioPath:str):

    try:
        with open(audioPath, "rb") as file:
            transcription = groq_client.audio.transcriptions.create(
                file=file,
                model="whisper-large-v3-turbo",
                language="pt",
                temperature=0.0
            )
            return transcription.text

    except Exception as e:
        return f"Error in recognize audio: {e}"
    
def audioAnalysisDetectWordsInText(text: str) -> str:

    text_lower = text.lower().split()
    correspondence = [word for word in phrases_crisis if word.lower() in text_lower]
    if not correspondence or correspondence == [] or correspondence == [""] or correspondence ==["."]:
        return f"não encontrei nenhuma correspondencia"
    return ", ".join(correspondence)

def extracting_characteristics(audio_path, voices=10) -> int:

    """
    Dynamically determines the number of speakers in an audio file.

    Args:
        audio_path (str): The path to the audio file.
        max_clusters (int): The maximum number of speakers to consider.

    Returns:
        int: The estimated number of speakers.
    """
    try: 
        # load audio
        y, sr = librosa.load(audio_path, sr = None)

        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20)
        mfccs = mfccs.T # traspose lines for time window

        # verify tam of mfccs
        if len(mfccs) < 1:
            return 1
        
        # count voices
        silhouette_scores = []
        for i in range(1, voices + 1):
            kmeans = MiniBatchKMeans(n_clusters=i, random_state=0, n_init=10, max_iter=300)
            labels = kmeans.fit_predict(mfccs)

            if len(np.unique(labels)) > 1:
                score = silhouette_score(mfccs, labels)
                silhouette_scores.append(score)
            else:
                silhouette_scores.append(-1)
        
        if not silhouette_scores or max(silhouette_scores) <= 0:
            return 1

        # search the major score
        optimal_clusters_index = np.argmax(silhouette_scores)

        num_voices = optimal_clusters_index + 1

        # verify if num voices is equal 0
        if all(score == 0 for score in silhouette_scores):
            print(f"score: {score}")
            return 1

        print(f"num voices {num_voices}")
        return num_voices

    except Exception as e:
        print(f"Erro na extração dinâmica de características: {e}")
        return 1 
