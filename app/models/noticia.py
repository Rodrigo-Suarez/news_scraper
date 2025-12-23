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

    def __post_init__(self):
        """Validación de datos al crear una instancia."""
        if not self.url:
            raise ValueError("La URL no puede estar vacía")
        if not self.source:
            raise ValueError("La fuente no puede estar vacía")
        if not self.title:
            raise ValueError("El título no puede estar vacío")

    def to_dict(self) -> dict:
        """Convierte la noticia a un diccionario."""
        return {
            'url': self.url,
            'source': self.source,
            'title': self.title,
            'subtitle': self.subtitle,
            'body': self.body,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'scraped_at': self.scraped_at.isoformat(),
            'ai_relevance_score': self.ai_relevance_score,
            'ai_decision': self.ai_decision,
            'ai_reasoning': self.ai_reasoning
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Noticia':
        """Crea una instancia de Noticia desde un diccionario."""
        if 'published_at' in data and data['published_at']:
            data['published_at'] = datetime.fromisoformat(data['published_at'])
        if 'scraped_at' in data:
            data['scraped_at'] = datetime.fromisoformat(data['scraped_at'])
        # Campos de IA (opcionales)
        data.setdefault('ai_relevance_score', None)
        data.setdefault('ai_decision', None)
        data.setdefault('ai_reasoning', None)
        return cls(**data)
