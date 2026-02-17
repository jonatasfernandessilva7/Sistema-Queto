"""
Core memory and learning utilities for the AI system.
Provides access to event history, memory state, and clustering capabilities.
"""

import json
import numpy as np
from typing import Dict, List, Any, Tuple, Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans

from src.core.models.event_models import EventModel
from src.backend.repository.GenericsRepository import (
    add_event_history,
    get_event_history,
    get_memory_state,
    update_system_status,
    get_system_status
)


def compare_events_with_history(current_event: EventModel) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Compare a current event with the history to find similar events.
    
    Args:
        current_event: The event to compare
        
    Returns:
        Tuple of (similarity message, most similar event or None)
    """
    history = get_event_history()

    if not history:
        return "No similar events found in history.", None

    documents = [
        json.dumps(e['evento']) for e in history
    ] + [json.dumps(current_event.model_dump())]

    vectorizer = TfidfVectorizer()
    tfidf = vectorizer.fit_transform(documents)

    similarities = cosine_similarity(tfidf[-1], tfidf[:-1])
    most_similar_index = np.argmax(similarities)
    max_similarity = similarities[0, most_similar_index]

    if max_similarity > 0.3:
        similar_event = history[most_similar_index]['evento']
        return f"Similar event found with similarity {max_similarity:.2f}", similar_event

    return "No similar events found.", None


def add_event_to_history(event_with_timestamp: Dict[str, Any]) -> None:
    """Add an event to the history."""
    event_data = event_with_timestamp['event']
    timestamp = event_with_timestamp['timestamp']
    add_event_history(event_data, timestamp)


def get_event_history_data() -> List[Dict[str, Any]]:
    """Retrieve the complete event history."""
    return get_event_history()


def get_memory_state_data() -> Dict[str, Any]:
    """Retrieve the current memory state of the system."""
    return get_memory_state()


def cluster_events(history: List[Dict[str, Any]], k: int = 3) -> Dict[int, List[Dict[str, Any]]]:
    """
    Cluster events using K-means algorithm.
    
    Args:
        history: List of historical events
        k: Number of clusters to create
        
    Returns:
        Dictionary mapping cluster IDs to lists of events
        
    Raises:
        ValueError: If k is greater than the number of events
    """
    if len(history) < k:
        raise ValueError(f"Number of clusters {k} exceeds available events.")

    texts = [json.dumps(ev["evento"]) for ev in history]

    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform(texts)

    kmeans = KMeans(n_clusters=k, random_state=0, n_init=10)
    clusters = kmeans.fit_predict(vectors)

    events_by_cluster: Dict[int, List[Dict[str, Any]]] = {i: [] for i in range(k)}
    for i, cluster_id in enumerate(clusters):
        events_by_cluster[cluster_id].append(history[i])

    return events_by_cluster


def update_system_status_data(system_name: str, status: str) -> None:
    """Update the status of a system component."""
    update_system_status(system_name, status)


def get_system_status_data(system_name: str) -> str:
    """Get the status of a system component."""
    return get_system_status(system_name)
