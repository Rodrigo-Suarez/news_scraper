"""
Parser de contenido de noticias.
Extrae título, subtítulo y cuerpo del artículo.
"""
from bs4 import BeautifulSoup
from app.utils.text_utils import normalizar_texto
from config.settings import get_validation_config


class ContentParser:
    """
    Clase para extraer el contenido de una noticia.
    Soporta múltiples estructuras HTML de diferentes diarios.
    """
    
    # Selectores para subtítulos
    SUBTITLE_SELECTORS = [
        'h2', 
        'h3', 
        ('p', {'class': 'lead'}), 
        ('div', {'class': 'subtitle'})
    ]
    
    # Contenedores donde buscar el cuerpo del artículo
    BODY_CONTAINERS = [
        ('div', 'itemFullText'),
        ('article', 'article-body-width'),
        ('article', 'article-body'),  # Tiempo de San Juan usa <article class="article-body">
        ('div', 'entry-content'),
        ('article', None),
        ('div', 'content'),
        ('div', 'article-body'),
        ('div', 'article-content'),
        ('div', 'post-content'),
        ('div', 'nota-content'),
    ]
    
    def __init__(self):
        """Inicializa el parser con la configuración de validación."""
        self.config = get_validation_config()
    
    def extraer_titulo(self, soup: BeautifulSoup) -> str:
        """
        Extrae el título de la noticia.
        
        Prioridad:
        1. Tag <h1>
        2. Meta tag og:title
        
        Args:
            soup: BeautifulSoup del HTML
            
        Returns:
            Título normalizado o string vacío
        """
        # Intentar primero <h1>
        h1_tag = soup.find('h1')
        if h1_tag:
            titulo = normalizar_texto(h1_tag.get_text(strip=True))
            if titulo:
                return titulo
        
        # Fallback: meta og:title
        meta_title = soup.find('meta', property='og:title')
        if meta_title and meta_title.get('content'):
            return normalizar_texto(meta_title['content'])
        
        return ""
    
    def extraer_subtitulo(self, soup: BeautifulSoup) -> str | None:
        """
        Extrae el subtítulo de la noticia.
        
        Args:
            soup: BeautifulSoup del HTML
            
        Returns:
            Subtítulo normalizado o None
        """
        for sel in self.SUBTITLE_SELECTORS:
            if isinstance(sel, tuple):
                tag, attrs = sel
                subtitle_tag = soup.find(tag, class_=attrs.get('class'))
            else:
                subtitle_tag = soup.find(sel)
            
            if subtitle_tag:
                subtitulo = normalizar_texto(subtitle_tag.get_text(strip=True))
                if subtitulo:
                    return subtitulo
        
        return None
    
    def extraer_cuerpo(self, soup: BeautifulSoup) -> str:
        """
        Extrae el cuerpo/contenido de la noticia.
        
        Busca en múltiples contenedores y extrae los párrafos.
        
        Args:
            soup: BeautifulSoup del HTML
            
        Returns:
            Cuerpo del artículo o string vacío
        """
        min_paragraphs = self.config['min_paragraphs']
        min_paragraph_length = self.config['min_paragraph_length']
        
        for tag, class_name in self.BODY_CONTAINERS:
            if class_name:
                # Primero buscar un solo contenedor
                container = soup.find(tag, class_=class_name)
            else:
                container = soup.find(tag)
            
            if container:
                paragraphs = container.find_all('p')
                
                if paragraphs and len(paragraphs) >= min_paragraphs:
                    body = "\n\n".join([
                        normalizar_texto(p.get_text(strip=True)) 
                        for p in paragraphs 
                        if len(p.get_text(strip=True)) > min_paragraph_length
                    ])
                    
                    if body:
                        return body
                
                # Si el contenedor existe pero no tiene suficientes párrafos,
                # buscar TODOS los contenedores con esta clase y combinarlos
                # (esto es común en sitios como San Juan 8 que dividen el artículo)
                if class_name:
                    all_containers = soup.find_all(tag, class_=lambda x: x and class_name in x)
                    if len(all_containers) > 1:
                        all_paragraphs = []
                        for cont in all_containers:
                            all_paragraphs.extend(cont.find_all('p'))
                        
                        if len(all_paragraphs) >= min_paragraphs:
                            body = "\n\n".join([
                                normalizar_texto(p.get_text(strip=True)) 
                                for p in all_paragraphs 
                                if len(p.get_text(strip=True)) > min_paragraph_length
                            ])
                            
                            if body:
                                return body
        
        return ""
    
    def es_contenido_valido(self, titulo: str, cuerpo: str) -> bool:
        """
        Verifica si el contenido extraído es válido.
        
        Args:
            titulo: Título de la noticia
            cuerpo: Cuerpo de la noticia
            
        Returns:
            True si el contenido es válido
        """
        min_body_length = self.config['min_body_length']
        return bool(titulo) and len(cuerpo) >= min_body_length
    
    def extraer_todo(self, soup: BeautifulSoup) -> dict:
        """
        Extrae todo el contenido de la noticia.
        
        Args:
            soup: BeautifulSoup del HTML
            
        Returns:
            Dict con título, subtítulo, cuerpo y validez
        """
        titulo = self.extraer_titulo(soup)
        subtitulo = self.extraer_subtitulo(soup)
        cuerpo = self.extraer_cuerpo(soup)
        
        return {
            'title': titulo,
            'subtitle': subtitulo,
            'body': cuerpo,
            'is_valid': self.es_contenido_valido(titulo, cuerpo)
        }
