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
    "enabled": False,
    
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

Son relevantes las noticias sobre:
- La intendenta Susana Laciar y su gestión
- Acciones, obras o anuncios del gobierno municipal de la Ciudad de San Juan
- Servicios municipales: recolección de residuos, alumbrado, bacheo, espacios verdes
- El Concejo Deliberante de Capital
- Eventos organizados por la municipalidad
- Problemas urbanos en la ciudad de San Juan (capital)
- Políticas públicas municipales

NO son relevantes:
- Noticias sobre el gobierno provincial de San Juan (gobernador, ministros provinciales)
- Noticias de otros departamentos de San Juan que no sean Capital
- Noticias nacionales o internacionales sin relación directa con la municipalidad
- Deportes, espectáculos o farándula sin relación municipal
- Policiales comunes sin participación municipal
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
