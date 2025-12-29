"""
Extractor de artículos desde páginas de portada.
"""
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from config.settings import get_article_selectors, get_validation_config, get_url_patterns


class ArticleFinder:
    """
    Clase para encontrar y extraer URLs de artículos desde una portada.
    Soporta múltiples estructuras HTML de diferentes diarios.
    """
    
    def __init__(self):
        """Inicializa el finder con la configuración."""
        self.article_selectors = get_article_selectors()
        self.url_patterns = get_url_patterns()
        self.config = get_validation_config()
    
    def encontrar_articulos(self, soup: BeautifulSoup) -> list:
        """
        Encuentra todos los elementos de artículo en la página.
        
        Args:
            soup: BeautifulSoup del HTML de la portada
            
        Returns:
            Lista de elementos BeautifulSoup que representan artículos
        """
        min_articles = self.config['min_articles_found']
        
        # Intentar selectores específicos primero
        for tag, class_name in self.article_selectors:
            # Buscar clases que contengan el texto (coincidencia parcial)
            found = soup.find_all(tag, class_=lambda x: x and class_name in x)
            if found and len(found) > min_articles:
                return found
        
        # Fallback 1: buscar todos los <article>
        articles = soup.find_all('article')
        if articles and len(articles) >= min_articles:
            return articles
        
        # Fallback 2: buscar por patrones de URL
        return self._buscar_por_url_patterns(soup, min_articles)
    
    def _buscar_por_url_patterns(self, soup: BeautifulSoup, min_articles: int) -> list:
        """
        Busca artículos por patrones de URL cuando otros métodos fallan.
        
        Args:
            soup: BeautifulSoup del HTML
            min_articles: Número mínimo de artículos requeridos
            
        Returns:
            Lista de contenedores de artículos
        """
        all_links = soup.find_all('a', href=True)
        article_containers = []
        
        for link in all_links:
            href = link.get('href', '')
            if any(pattern in href.lower() for pattern in self.url_patterns):
                parent = link.find_parent(['article', 'div', 'li'])
                if parent and parent not in article_containers:
                    article_containers.append(parent)
        
        return article_containers if len(article_containers) > min_articles else []
    
    def extraer_urls(self, articles: list, source_url: str) -> list[str]:
        """
        Extrae las URLs de los artículos encontrados.
        
        Filtra URLs duplicadas, templates y dominios externos.
        
        Args:
            articles: Lista de elementos de artículo
            source_url: URL base del diario
            
        Returns:
            Lista de URLs únicas de artículos
        """
        urls_procesadas = set()
        urls_noticias = []
        source_domain = urlparse(source_url).netloc
        
        for article in articles:
            url = self._extraer_url_de_articulo(article, source_url, source_domain)
            
            if url and url not in urls_procesadas:
                urls_procesadas.add(url)
                urls_noticias.append(url)
        
        return urls_noticias
    
    def _extraer_url_de_articulo(
        self, 
        article, 
        source_url: str, 
        source_domain: str
    ) -> str | None:
        """
        Extrae la URL de un elemento de artículo individual.
        
        Busca el enlace dentro del artículo o en el padre si es un <a>.
        
        Args:
            article: Elemento BeautifulSoup del artículo
            source_url: URL base para resolver URLs relativas
            source_domain: Dominio del diario para validación
            
        Returns:
            URL completa o None si no es válida
        """
        # Buscar enlace dentro del artículo
        link = article.find('a', href=True)
        
        # Si no hay enlace hijo, verificar si el padre es un <a>
        if not link and article.parent and article.parent.name == 'a':
            if article.parent.get('href'):
                link = article.parent
        
        if not link:
            return None
        
        url_completa = urljoin(source_url, link['href'])
        news_domain = urlparse(url_completa).netloc
        
        # Validaciones
        if '{{' in url_completa:  # Template no procesado
            return None
        if source_domain != news_domain:  # Dominio externo
            return None
        
        return url_completa
