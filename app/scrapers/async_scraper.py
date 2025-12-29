"""
Scraper asíncrono para extraer noticias de múltiples fuentes en paralelo.

Este módulo orquesta el proceso de scraping usando componentes modulares:
- AsyncHTTPClient: Cliente HTTP asíncrono
- ArticleFinder: Encuentra artículos en portadas
- NewsExtractor: Extrae datos de noticias individuales
- DateParser: Parsea fechas de publicación
- ContentParser: Extrae contenido (título, cuerpo, etc.)
"""
import asyncio
import time
from bs4 import BeautifulSoup

from app.models.noticia import Noticia
from app.http import AsyncHTTPClient
from app.extractors import ArticleFinder, NewsExtractor
from config.settings import get_scraping_config


class AsyncNewsScraper:
    """
    Scraper asíncrono de noticias.
    
    Coordina el proceso de scraping de múltiples fuentes de forma
    paralela y eficiente.
    """
    
    def __init__(self, max_concurrent_requests: int = None):
        """
        Inicializa el scraper.
        
        Args:
            max_concurrent_requests: Límite de requests concurrentes.
                                   Si es None, usa el valor de configuración.
        """
        self.config = get_scraping_config()
        self.max_concurrent = max_concurrent_requests or self.config['max_concurrent_requests']
        
        # Componentes
        self.http_client = AsyncHTTPClient()
        self.article_finder = ArticleFinder()
    
    async def _scrape_source(
        self,
        session,
        source: dict,
        semaphore: asyncio.Semaphore,
        news_extractor: NewsExtractor
    ) -> list[Noticia]:
        """
        Scrapea una fuente individual.
        
        Args:
            session: Sesión HTTP activa
            source: Dict con 'name' y 'url' del diario
            semaphore: Semáforo para limitar concurrencia
            news_extractor: Extractor de noticias
            
        Returns:
            Lista de noticias extraídas
        """
        source_url = source['url']
        source_name = source['name']
        start_time = time.time()
        
        try:
            print(f"\n🔍 Scrapeando: {source_name}")
            
            # Obtener HTML de la portada
            html = await self.http_client.fetch_html(session, source_url)
            if not html:
                print(f"   ❌ No se pudo obtener HTML")
                return []
            
            soup = BeautifulSoup(html, "html.parser")
            
            # Encontrar artículos
            articles = self.article_finder.encontrar_articulos(soup)
            if not articles:
                print(f"   ⚠️ No se encontraron artículos")
                return []
            
            # Extraer URLs
            urls = self.article_finder.extraer_urls(articles, source_url)
            print(f"   📰 {source_name}:{len(articles)} artículos encontrados, procesando {len(urls)} URLs...")
            
            # Procesar noticias en paralelo
            tasks = [
                news_extractor.extraer(session, url, source_name, semaphore)
                for url in urls
            ]
            
            resultados = await asyncio.gather(*tasks)
            noticias = [n for n in resultados if n is not None]
            
            elapsed = time.time() - start_time
            print(f"   ✅ {source_name}: {len(noticias)} noticias extraídas en {elapsed:.2f}s")
            
            return noticias
            
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"   ❌ Error: {e} ({elapsed:.2f}s)")
            return []
    
    async def scrape_async(self, sources: list[dict]) -> list[Noticia]:
        """
        Scrapea todas las fuentes de forma asíncrona.
        
        Args:
            sources: Lista de dicts con 'name' y 'url'
            
        Returns:
            Lista de todas las noticias extraídas
        """
        start_time = time.time()
        
        print("=" * 60)
        print("🚀 SCRAPING ASÍNCRONO - MODO PARALELO")
        print("=" * 60)
        print(f"   Fuentes: {len(sources)}")
        print(f"   Conexiones concurrentes: {self.max_concurrent}")
        
        semaphore = asyncio.Semaphore(self.max_concurrent)
        news_extractor = NewsExtractor(self.http_client)
        
        async with self.http_client.crear_session(self.max_concurrent) as session:
            # Procesar todas las fuentes en paralelo
            tasks = [
                self._scrape_source(session, source, semaphore, news_extractor)
                for source in sources
            ]
            
            resultados_por_fuente = await asyncio.gather(*tasks)
        
        # Combinar todas las noticias
        todas_las_noticias = []
        for noticias in resultados_por_fuente:
            todas_las_noticias.extend(noticias)
        
        elapsed = time.time() - start_time
        
        self._imprimir_resumen(len(sources), len(todas_las_noticias), elapsed)
        
        return todas_las_noticias
    
    def _imprimir_resumen(self, num_fuentes: int, num_noticias: int, elapsed: float):
        """Imprime el resumen final del scraping."""
        print(f"\n{'=' * 60}")
        print(f"📊 RESUMEN FINAL:")
        print(f"   Fuentes procesadas: {num_fuentes}")
        print(f"   Total noticias: {num_noticias}")
        print(f"   ⏱️  TIEMPO TOTAL: {elapsed:.2f}s ({elapsed/60:.2f} min)")
        if num_noticias:
            print(f"   ⚡ Promedio: {elapsed/num_noticias:.2f}s/noticia")
        print("=" * 60)
    
    def scrape(self, sources: list[dict]) -> list[Noticia]:
        """
        Wrapper síncrono para scrape_async.
        
        Args:
            sources: Lista de dicts con 'name' y 'url'
            
        Returns:
            Lista de todas las noticias extraídas
        """
        return asyncio.run(self.scrape_async(sources))


# Exportar clase principal
__all__ = ['AsyncNewsScraper']
