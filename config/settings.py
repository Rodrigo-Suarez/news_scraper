"""
Configuración global del proyecto News Scraper.
"""

# ============================================================
# CONFIGURACIÓN DE SCRAPING ASÍNCRONO
# ============================================================

SCRAPING_CONFIG = {
    # Número máximo de requests HTTP concurrentes
    # - 10: Conservador, más estable
    # - 15: Balanceado (RECOMENDADO)
    # - 20-30: Agresivo, más rápido pero puede tener timeouts
    # - 50+: Muy agresivo, muchos errores esperados
    "max_concurrent_requests": 15,
    
    # Límite de conexiones por host (evita saturar un mismo servidor)
    "limit_per_host": 5,
    
    # Timeout en segundos para cada request HTTP
    "request_timeout": 15,
    
    # User-Agent para las peticiones HTTP
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}


# ============================================================
# CONFIGURACIÓN DE VALIDACIÓN DE NOTICIAS
# ============================================================

VALIDATION_CONFIG = {
    # Longitud mínima del cuerpo de la noticia (en caracteres)
    "min_body_length": 100,
    
    # Número mínimo de artículos encontrados para considerar la página válida
    "min_articles_found": 3,
    
    # Número mínimo de párrafos en el cuerpo de la noticia
    "min_paragraphs": 2,
    
    # Longitud mínima de cada párrafo (en caracteres)
    "min_paragraph_length": 20,
}


# ============================================================
# PATRONES DE DETECCIÓN DE NOTICIAS
# ============================================================

URL_PATTERNS = [
    '/noticia', '/nota', '/post', '/articulo', '/news', '202',
    '/prensa', '/gobierno', '-n1', '-n2', '-n3', '-n4', '-n5',
    '/deportes', '/economia', '/salud', '/policiales', '/san-juan'
]


# ============================================================
# SELECTORES CSS PARA SCRAPING
# ============================================================

ARTICLE_SELECTORS = [
    # Selectores específicos por sitio
    ('article', 'news-article'),
    ('article', 'article-badge-in-image'),
    ('div', 'gkNewsElement'),
    ('div', 'nspArt'),
    ('article', 'wp-block-post'),
    ('div', 'post-item'),
    ('div', 'single_post'),       # Nuevo Diario San Juan y similares
    ('div', 'post_type5'),        # Nuevo Diario San Juan - slider
    ('div', 'td_module_'),        # Ahora San Juan (Newspaper theme)
    ('div', 'read-single'),       # Diario Las Noticias (MoreNews theme)
    # Selectores genéricos
    ('article', 'entry-box'),
    ('article', 'card'),
    ('article', 'article'),
    ('article', 'post'),
    ('div', 'article'),
    ('div', 'news-item'),
    ('div', 'nota'),
    ('li', 'post'),               # Listas de posts
]

#=============================================================
# CONFIGURACIÓN DE LOGGING
#=============================================================


LOGGING_CONFIG = {
    "level": "DEBUG",  # DEBUG para desarrollo, INFO para producción
    "log_to_file": True,
    "log_dir": "logs",
    "log_filename": "news_scraper.log"
}



# ============================================================
# TEMAS PERMITIDOS PARA CLASIFICACIÓN DE NOTICIAS
# ============================================================
ALLOWED_TOPICS = [
    # Infraestructura y obras
    "obras públicas",
    "infraestructura urbana",
    "espacios verdes",
    "iluminación pública",
    
    # Servicios municipales
    "servicios públicos",
    "recolección de residuos",
    "limpieza urbana",
    "mantenimiento urbano",
    "tránsito y movilidad",
    
    # Gestión y administración
    "gestión municipal",
    "políticas públicas",
    "presupuesto municipal",
    "ordenanzas municipales",
    "concejo deliberante",
    
    # Áreas sociales
    "salud pública",
    "educación",
    "acción social",
    "derechos humanos",
    "género y diversidad",
    
    # Desarrollo económico
    "desarrollo económico",
    "comercio local",
    "empleo",
    "turismo",
    
    # Seguridad y emergencias
    "seguridad ciudadana",
    "protección civil",
    "emergencias",
    
    # Cultura y deporte
    "cultura",
    "deportes",
    "eventos municipales",
    "festividades",
    
    # Participación ciudadana
    "participación ciudadana",
    "reclamos vecinales",
    "audiencias públicas",
    
    # Medio ambiente
    "medio ambiente",
    "sostenibilidad",
    "reciclaje",
    
    # Tecnología y modernización
    "innovación tecnológica",
    "gobierno digital",
    "digitalización",
    
    # Otros
    "anuncios oficiales",
    "comunicación institucional",
    "otro"  # Catch-all
]


# ============================================================
# FUNCIONES HELPER
# ============================================================

def get_scraping_config() -> dict:
    """Retorna la configuración de scraping."""
    return SCRAPING_CONFIG


def get_validation_config() -> dict:
    """Retorna la configuración de validación."""
    return VALIDATION_CONFIG


def get_url_patterns() -> list:
    """Retorna los patrones de URLs de noticias."""
    return URL_PATTERNS


def get_article_selectors() -> list:
    """Retorna los selectores CSS para artículos."""
    return ARTICLE_SELECTORS


def get_logging_config() -> dict:
    """Retorna la configuración de logging."""
    return LOGGING_CONFIG


def get_allowed_topics() -> list:
    """Retorna la lista de topics permitidos."""
    return ALLOWED_TOPICS