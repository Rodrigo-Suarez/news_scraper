"""
Configuración para el filtrado de noticias con IA usando Groq.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# CONFIGURACIÓN DE GROQ
# ============================================================

AI_CONFIG = {
    # Habilitar/deshabilitar el filtrado por IA
    "enabled": True,
    
    # API Key de Groq (obtén la tuya gratis en: https://console.groq.com/keys)
    # Se recomienda usar variable de entorno: GROQ_API_KEY
    "api_key": os.getenv("GROQ_API_KEY", ""),
    
    # Modelo de Groq a usar:
    # - "llama-3.3-70b-versatile" (RECOMENDADO - muy potente y rápido)
    # - "mixtral-8x7b-32768" (alternativa rápida)
    # - "llama-3.1-8b-instant" (más rápido, menos preciso)
    "model": "llama-3.3-70b-versatile",
    
    # Umbral de relevancia (0.0 a 1.0)
    # Solo se guardarán noticias con score >= este valor
    "relevance_threshold": 0.6,
    
    # Prompt del contexto de filtrado
    # Este es el criterio que la IA usará para determinar relevancia
    "context_prompt": """
Estoy buscando noticias relacionadas con la Municipalidad de la Ciudad de San Juan, Argentina.

CRITERIOS DE RELEVANCIA:

✅ SON RELEVANTES las noticias sobre:
- La intendenta Susana Laciar y su gestión municipal
- Acciones, obras, proyectos o anuncios del gobierno municipal de Capital
- Decisiones y ordenanzas del Concejo Deliberante de la Ciudad
- Servicios municipales: recolección de residuos, alumbrado, bacheo, espacios verdes, limpieza
- Obras públicas e infraestructura urbana en Capital
- Eventos, actividades o programas organizados por la municipalidad
- Políticas públicas municipales: salud, educación, acción social, cultura, deportes
- Presupuesto, licitaciones o contrataciones municipales
- Problemas urbanos en la Ciudad de San Juan que involucren a la municipalidad
- Reclamos vecinales o participación ciudadana relacionados con la gestión municipal

❌ NO SON RELEVANTES:
- Noticias del gobierno provincial (gobernador, ministros provinciales)
- Noticias de otros departamentos/municipios de San Juan (Pocito, Rivadavia, Chimbas, etc.)
- Noticias nacionales o internacionales sin vínculo directo con la municipalidad
- Policiales comunes sin participación o declaración de la municipalidad
- Deportes, espectáculos o farándula sin relación con gestión municipal
- Eventos privados sin auspicio o participación municipal


IMPORTANTE:
- Sé estricto con la relevancia: solo marca como relevante si realmente involucra directamente a la municipalidad de Capital
"""
}


def get_ai_config() -> dict:
    """Retorna la configuración de IA."""
    return AI_CONFIG


def update_context_prompt(new_prompt: str):
    """
    Actualiza el prompt de contexto en runtime.
    Útil para cambiar el criterio de filtrado sin modificar el archivo.
    """
    AI_CONFIG["context_prompt"] = new_prompt
