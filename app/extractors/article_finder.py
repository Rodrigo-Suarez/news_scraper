"""
Extractor de artículos desde páginas de portada.
"""
import re
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
        COMBINA todos los selectores para capturar artículos en diferentes secciones.
        
        Args:
            soup: BeautifulSoup del HTML de la portada
            
        Returns:
            Lista de elementos BeautifulSoup que representan artículos
        """
        min_articles = self.config['min_articles_found']
        all_articles = []
        found_elements = set()  # Para evitar duplicados
        
        # Prioridad 1: buscar todos los <article>
        articles = soup.find_all('article')
        for art in articles:
            article_id = id(art)
            if article_id not in found_elements:
                all_articles.append(art)
                found_elements.add(article_id)
        
        # Prioridad 2: Buscar por selectores específicos (incluso si ya encontramos articles)
        for tag, class_name in self.article_selectors:
            # Buscar clases que contengan el texto (coincidencia parcial)
            found = soup.find_all(tag, class_=lambda x: x and class_name in ' '.join(x) if isinstance(x, list) else class_name in str(x))
            for elem in found:
                elem_id = id(elem)
                if elem_id not in found_elements:
                    all_articles.append(elem)
                    found_elements.add(elem_id)
        
        # Si tenemos suficientes artículos, devolver
        if len(all_articles) >= min_articles:
            return all_articles
        
        # Fallback: buscar por patrones de URL
        url_articles = self._buscar_por_url_patterns(soup, min_articles)
        for elem in url_articles:
            elem_id = id(elem)
            if elem_id not in found_elements:
                all_articles.append(elem)
                found_elements.add(elem_id)
        
        return all_articles if len(all_articles) >= min_articles else []
    
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
            # Método 1: Buscar TODOS los enlaces dentro del contenedor
            links = article.find_all('a', href=True)
            for link in links:
                url = self._validar_url(link['href'], source_url, source_domain)
                if url and url not in urls_procesadas:
                    urls_procesadas.add(url)
                    urls_noticias.append(url)
            
            # Método 2: Si no hay enlaces dentro, buscar en ancestros cercanos
            if not links:
                # Verificar si el parent es un <a>
                parent = article.parent
                if parent and parent.name == 'a' and parent.get('href'):
                    url = self._validar_url(parent['href'], source_url, source_domain)
                    if url and url not in urls_procesadas:
                        urls_procesadas.add(url)
                        urls_noticias.append(url)
                # Verificar hermanos cercanos (siguiente elemento)
                elif parent:
                    sibling_link = parent.find('a', href=True)
                    if sibling_link:
                        url = self._validar_url(sibling_link['href'], source_url, source_domain)
                        if url and url not in urls_procesadas:
                            urls_procesadas.add(url)
                            urls_noticias.append(url)
        
        return urls_noticias
    
    def _normalizar_dominio(self, domain: str) -> str:
        """Normaliza un dominio quitando 'www.' si existe."""
        return domain.lower().removeprefix('www.')
    
    def _validar_url(
        self, 
        href: str, 
        source_url: str, 
        source_domain: str
    ) -> str | None:
        """
        Valida y normaliza una URL de artículo.
        
        Args:
            href: URL o path relativo del enlace
            source_url: URL base para resolver URLs relativas
            source_domain: Dominio del diario para validación
            
        Returns:
            URL completa o None si no es válida
        """
        url_completa = urljoin(source_url, href)
        news_domain = urlparse(url_completa).netloc
        
        # Validaciones básicas
        if '{{' in url_completa:  # Template no procesado
            return None
        
        # Comparar dominios normalizados (ignorar www)
        if self._normalizar_dominio(source_domain) != self._normalizar_dominio(news_domain):
            return None
        
        # Filtrar URLs que no son artículos
        path = urlparse(url_completa).path.lower()
        
        # Excluir páginas de categorías, archivos por fecha, tags, etc.
        excluded_patterns = [
            '/category/', '/tag/', '/author/', '/page/', '/secciones/',
            '/wp-content/', '/wp-admin/', '/feed/',
            '/#', '/search', '/contacto', '/quienes-somos',
            '/politica-de-privacidad', '/terminos',
        ]
        if any(pattern in path for pattern in excluded_patterns):
            return None
        
        # Excluir URLs que son solo fechas (ej: /2025/12/20/)
        if re.match(r'^/\d{4}/\d{2}/\d{2}/?$', path):
            return None
        
        # Excluir la página principal
        if path in ['/', '']:
            return None
        
        # Excluir URLs muy cortas (probablemente no son artículos)
        if len(path) < 5:
            return None
        
        return url_completa
