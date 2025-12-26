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
    # Selectores genéricos
    ('article', 'entry-box'),
    ('article', 'card'),
    ('article', 'article'),
    ('article', 'post'),
    ('div', 'article'),
    ('div', 'news-item'),
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
