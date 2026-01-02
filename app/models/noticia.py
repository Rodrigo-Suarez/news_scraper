from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime


@dataclass
class Noticia:
    """Modelo para representar una noticia del diario."""
    url: str
    source: str  # Nombre del diario
    title: str
    subtitle: Optional[str] = None
    body: str = ""
    published_at: Optional[datetime] = None
    scraped_at: datetime = field(default_factory=datetime.now)
    
    # Campos de análisis de IA (opcionales)
    ai_relevance_score: Optional[float] = None  # Score de relevancia (0.0 a 1.0)
    ai_decision: Optional[bool] = None  # Decisión de la IA (relevante o no)
    ai_reasoning: Optional[str] = None  # Explicación de la IA
    ai_keywords_found: Optional[List[str]] = None  # Palabras clave encontradas por la IA

    ai_sentiment: Optional[str] = None  # Sentimiento detectado por la IA
    ai_sentiment_score: Optional[float] = None  # Puntuación de sentimiento
    ai_sentiment_confidence: Optional[float] = None  # Confianza en el análisis de sentimiento

    ai_tone: Optional[str] = None  # Tono detectado por la IA

    ai_topics: Optional[List[str]] = None  # Temas detectados por la IA
    ai_main_topic: Optional[str] = None  # Tema principal detectado por la IA

    # ai_actors: Optional[dict] = None  # Actores detectados por la IA


    def __post_init__(self):
        """Validación de datos al crear una instancia."""
        if not self.url:
            raise ValueError("La URL no puede estar vacía")
        if not self.source:
            raise ValueError("La fuente no puede estar vacía")
        if not self.title:
            raise ValueError("El título no puede estar vacío")
        if not self.body:
            raise ValueError("El cuerpo de la noticia no puede estar vacío")
