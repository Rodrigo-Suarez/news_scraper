"""
Configuración de fuentes de noticias.
Define las URLs y configuración para cada diario a scrapear.
"""

SOURCES = [
    {
        "name": "Diario de Cuyo",
        "url": "https://www.diariodecuyo.com.ar/",
        "enabled": True
    },
    {
        "name": "SI San Juan",
        "url": "https://www.sisanjuan.gob.ar/",
        "enabled": True  # Ahora con selectores específicos para gkNewsElement
    },
    {
        "name": "San Juan 8",
        "url": "https://www.sanjuan8.com/",
        "enabled": True  # Ahora con selectores específicos para article.news-article
    },
    {
        "name": "0264 Noticias",
        "url": "https://www.0264noticias.com.ar/",
        "enabled": True
    },
    {
        "name": "Nuevo Diario San Juan",
        "url": "https://www.nuevodiariosanjuan.com.ar/",
        "enabled": True  # Usando selectores mejorados
    },
    {
        "name": "Canal 13 San Juan",
        "url": "https://www.canal13sanjuan.com/",
        "enabled": True
    },
    {
        "name": "Diario El Zonda",
        "url": "https://www.diarioelzondasj.com.ar/",
        "enabled": True
    },
    {
        "name": "Telesol Diario",
        "url": "https://www.telesoldiario.com/",
        "enabled": True
    },
    {
        "name": "Diario Huarpe",
        "url": "https://www.diariohuarpe.com/",
        "enabled": True
    },
    {
        "name": "Ahora San Juan",
        "url": "https://www.ahorasanjuan.com/",
        "enabled": True
    },
    {
        "name": "El Sol de San Juan",
        "url": "https://elsoldesanjuan.com.ar/",
        "enabled": True  # Ahora con patrones de URL mejorados
    },
    {
        "name": "Diario Las Noticias",
        "url": "https://diariolasnoticias.com/",
        "enabled": True
    }
]

# KEYWORDS = [
#     "susana laciar",
#     "intendenta susana laciar",
#     "gestion susana laciar",
#     "gestión susana laciar",
#     "municipalidad de la ciudad de san juan",
#     "municipalidad de san juan",
#     "municipio de san juan",
#     "intendente de san juan",
#     "intendencia de san juan",
#     "capital",
#     "ciudad de san juan",
#     "trinidad",
#     "desamparados",
#     "concepcion",
#     "susy.laciar"
# ]

KEYWORDS = [
    # Intendenta / gestión
    "susana laciar", "susana e. laciar", "susy laciar", "laciar",
    "intendenta susana laciar", "intendenta de la ciudad de san juan",
    "gestion susana laciar", "gestión susana laciar",
    "administración laciar", "equipo de gobierno municipal",

    # Municipalidad
    "municipalidad de la ciudad de san juan", "municipalidad de san juan",
    "municipio de san juan", "municipio capital", "municipalidad capital",
    "gobierno municipal", "administración municipal",
    "concejo deliberante de capital", "concejo deliberante de san juan",

    # Cargo / función
    "intendenta de san juan", "intendente capital", "intendente de san juan"
    "ejecutivo municipal", "autoridades municipales",

    # Ciudad / capital
    "ciudad de san juan", "capital sanjuanina", "departamento capital",

    # Barrios
    "trinidad", "desamparados", "concepción", "concepcion",
    "microcentro", "plaza 25 de mayo",

    # Temas municipales
    "obras municipales", "obra pública municipal", "bacheo",
    "alumbrado público", "recolección de residuos", "limpieza urbana",
    "ordenamiento urbano", "espacios verdes", "arbolado público",

    # Redes
    "susy.laciar", "@susylaciar"
]

def get_enabled_sources():
    """Retorna solo las fuentes habilitadas."""
    return [source for source in SOURCES if source.get("enabled", False)]


def get_source_by_name(name):
    """Obtiene una fuente específica por nombre."""
    for source in SOURCES:
        if source["name"].lower() == name.lower():
            return source
    return None


def noticia_contiene_keywords(noticia):
    """Verifica si una noticia contiene alguna de las keywords configuradas."""
    # Concatenar título, subtítulo y cuerpo para buscar
    texto_completo = f"{noticia.title} {noticia.subtitle or ''} {noticia.body}".lower()
    
    # Verificar si alguna keyword está presente
    for keyword in KEYWORDS:
        if keyword.lower() in texto_completo:
            return True
    
    return False
