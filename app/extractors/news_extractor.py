"""
Extractor de datos de noticias individuales.
"""
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from app.models.noticia import Noticia
from app.parsers.date_parser import DateParser
from app.parsers.content_parser import ContentParser
from app.http.async_client import AsyncHTTPClient


class NewsExtractor:
    """
    Clase para extraer los datos completos de una noticia individual.
    Coordina los parsers de contenido y fechas.
    """
    
    def __init__(self, http_client: AsyncHTTPClient):
        """
        Inicializa el extractor.
        
        Args:
            http_client: Cliente HTTP para obtener las páginas
        """
        self.http_client = http_client
        self.content_parser = ContentParser()
    
    async def extraer(
        self,
        session: aiohttp.ClientSession,
        url: str,
        source_name: str,
        semaphore: asyncio.Semaphore
    ) -> Noticia | None:
        """
        Extrae todos los datos de una noticia.
        
        Args:
            session: Sesión HTTP activa
            url: URL de la noticia
            source_name: Nombre del diario fuente
            semaphore: Semáforo para limitar concurrencia
            
        Returns:
            Objeto Noticia o None si falla la extracción
        """
        async with semaphore:
            try:
                html = await self.http_client.fetch_html(session, url)
                if not html:
                    return None
                
                soup = BeautifulSoup(html, "html.parser")
                
                # Extraer contenido
                contenido = self.content_parser.extraer_todo(soup)
                
                if not contenido['is_valid']:
                    return None
                
                # Extraer fecha
                fecha = DateParser.extraer(soup, url)
                
                return Noticia(
                    url=url,
                    source=source_name,
                    title=contenido['title'],
                    subtitle=contenido['subtitle'],
                    body=contenido['body'],
                    published_at=fecha
                )
                
            except Exception:
                return None
