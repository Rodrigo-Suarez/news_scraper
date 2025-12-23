"""
Módulo de filtrado de noticias mediante IA usando Groq.
"""
import json
from typing import List, Optional
from dataclasses import dataclass

from app.models.noticia import Noticia


@dataclass
class AIFilterResult:
    """Resultado del análisis de IA para una noticia."""
    is_relevant: bool
    relevance_score: float  # 0.0 a 1.0
    reasoning: str
    keywords_found: List[str]


class GroqProvider:
    """Proveedor para Groq API - Rápido y gratuito."""
    
    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        self.api_key = api_key
        self.model = model
        self._client = None
    
    def _get_client(self):
        """Lazy initialization del cliente Groq."""
        if self._client is None:
            try:
                from groq import Groq
                self._client = Groq(api_key=self.api_key)
            except ImportError:
                raise ImportError("Instala groq: pip install groq")
        return self._client
    
    def _build_analysis_prompt(self, noticia: Noticia, context_prompt: str) -> str:
        """Construye el prompt para el análisis."""
        return f"""Eres un asistente que filtra noticias según su relevancia para un contexto específico.

CONTEXTO DE FILTRADO:
{context_prompt}

NOTICIA A ANALIZAR:
- Título: {noticia.title}
- Subtítulo: {noticia.subtitle or 'N/A'}
- Fuente: {noticia.source}
- Contenido (primeros 1500 caracteres): {noticia.body[:1500] if noticia.body else 'Sin contenido'}

INSTRUCCIONES:
Analiza si esta noticia es relevante para el contexto especificado.
Responde ÚNICAMENTE con un JSON válido (sin markdown, sin ```json):

{{
    "is_relevant": true/false,
    "relevance_score": 0.0 a 1.0,
    "reasoning": "Explicación breve de por qué es o no relevante",
    "keywords_found": ["lista", "de", "términos", "relevantes", "encontrados"]
}}"""
    
    def _parse_response(self, response_text: str) -> AIFilterResult:
        """Parsea la respuesta de la IA a AIFilterResult."""
        try:
            # Limpiar respuesta de posibles markers de código
            cleaned = response_text.strip()
            if cleaned.startswith("```"):
                # Remover bloques de código markdown
                lines = cleaned.split('\n')
                cleaned = '\n'.join(lines[1:-1] if lines[-1] == '```' else lines[1:])
            
            data = json.loads(cleaned)
            return AIFilterResult(
                is_relevant=data.get('is_relevant', False),
                relevance_score=float(data.get('relevance_score', 0.0)),
                reasoning=data.get('reasoning', 'Sin explicación'),
                keywords_found=data.get('keywords_found', [])
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # Fallback si no se puede parsear
            return AIFilterResult(
                is_relevant=False,
                relevance_score=0.0,
                reasoning=f"Error al parsear respuesta de IA: {str(e)}",
                keywords_found=[]
            )
    
    def analyze_relevance(self, noticia: Noticia, context_prompt: str) -> AIFilterResult:
        """Analiza una noticia usando Groq."""
        client = self._get_client()
        prompt = self._build_analysis_prompt(noticia, context_prompt)
        
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Eres un asistente que analiza noticias y responde solo en JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            return self._parse_response(response.choices[0].message.content)
        except Exception as e:
            return AIFilterResult(
                is_relevant=False,
                relevance_score=0.0,
                reasoning=f"Error en Groq API: {str(e)}",
                keywords_found=[]
            )


class AIFilter:
    """Clase principal para filtrar noticias usando IA (Groq)."""
    
    def __init__(self, api_key: str, model: str, context_prompt: str, relevance_threshold: float = 0.6):
        """
        Inicializa el filtro de IA.
        
        Args:
            api_key: API key de Groq
            model: Modelo de Groq a usar
            context_prompt: El prompt con el contexto de filtrado
            relevance_threshold: Umbral mínimo de relevancia (0.0 a 1.0)
        """
        self.provider = GroqProvider(api_key=api_key, model=model)
        self.context_prompt = context_prompt
        self.relevance_threshold = relevance_threshold
        
        # Estadísticas
        self.stats = {
            'total_analyzed': 0,
            'relevant': 0,
            'not_relevant': 0,
            'errors': 0
        }
    
    def filter_noticias(self, noticias: List[Noticia], verbose: bool = True) -> List[Noticia]:
        """
        Filtra una lista de noticias, retornando solo las relevantes.
        
        Args:
            noticias: Lista de noticias a filtrar
            verbose: Si mostrar progreso
            
        Returns:
            Lista de noticias relevantes
        """
        if not noticias:
            return []
        
        relevant_noticias = []
        total = len(noticias)
        
        for i, noticia in enumerate(noticias, 1):
            if verbose:
                print(f"   🤖 Analizando [{i}/{total}]: {noticia.title[:50]}...")
            
            self.stats['total_analyzed'] += 1
            result = self.provider.analyze_relevance(noticia, self.context_prompt)
            
            # Actualizar noticia con metadatos de IA
            noticia.ai_relevance_score = result.relevance_score
            noticia.ai_decision = result.is_relevant and result.relevance_score >= self.relevance_threshold
            noticia.ai_reasoning = result.reasoning
            
            if "Error" in result.reasoning:
                self.stats['errors'] += 1
                if verbose:
                    print(f"      ⚠️ Error: {result.reasoning}")
            elif noticia.ai_decision:
                self.stats['relevant'] += 1
                relevant_noticias.append(noticia)
                if verbose:
                    print(f"      ✅ Relevante (score: {result.relevance_score:.2f})")
            else:
                self.stats['not_relevant'] += 1
                if verbose:
                    print(f"      ❌ No relevante (score: {result.relevance_score:.2f})")
        
        return relevant_noticias
    
    def get_stats(self) -> dict:
        """Retorna estadísticas del filtrado."""
        return self.stats.copy()


def get_ai_filter(config: dict) -> Optional[AIFilter]:
    """
    Factory function para crear un AIFilter basado en configuración.
    
    Args:
        config: Diccionario con la configuración de IA
        
    Returns:
        Instancia de AIFilter configurada, o None si está deshabilitado
    """
    if not config.get('enabled', False):
        return None
    
    return AIFilter(
        api_key=config.get('api_key', ''),
        model=config.get('model', 'llama-3.3-70b-versatile'),
        context_prompt=config.get('context_prompt', ''),
        relevance_threshold=config.get('relevance_threshold', 0.6)
    )
