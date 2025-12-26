"""
Scraper asíncrono para extraer noticias de múltiples fuentes en paralelo.
Mucho más rápido que el scraper secuencial.
"""
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from app.models.noticia import Noticia
from urllib.parse import urljoin, urlparse
from datetime import datetime
import time
import unicodedata
from config.settings import (
    get_scraping_config, 
    get_validation_config, 
    get_url_patterns, 
    get_article_selectors
)

# Cargar configuraciones
SCRAPING_CONFIG = get_scraping_config()
VALIDATION_CONFIG = get_validation_config()
URL_PATTERNS = get_url_patterns()
ARTICLE_SELECTORS = get_article_selectors()

HEADERS = {
    'User-Agent': SCRAPING_CONFIG['user_agent']
}


def normalizar_texto(texto):
    """
    Normaliza el texto corrigiendo codificación y eliminando tildes.
    Mantiene la ñ y otros caracteres especiales del español.
    """
    if not texto:
        return texto
    
    texto = unicodedata.normalize('NFC', texto)
    texto_sin_tildes = ''.join(
        char for char in unicodedata.normalize('NFD', texto)
        if unicodedata.category(char) != 'Mn'
    )
    return texto_sin_tildes


async def fetch_html(session: aiohttp.ClientSession, url: str) -> str | None:
    """Fetch HTML de una URL de forma asíncrona."""
    try:
        timeout = aiohttp.ClientTimeout(total=SCRAPING_CONFIG['request_timeout'])
        async with session.get(url, timeout=timeout) as response:
            # Leer contenido raw (bytes)
            content = await response.read()
            
            # Detectar encoding usando chardet (similar a apparent_encoding de requests)
            detected_encoding = None
            try:
                import chardet
                result = chardet.detect(content)
                if result and result.get('encoding'):
                    detected_encoding = result['encoding']
            except ImportError:
                pass
            
            # Decodificar con el encoding detectado
            if detected_encoding:
                try:
                    return content.decode(detected_encoding)
                except (UnicodeDecodeError, LookupError):
                    pass
            
            # Fallback: usar la detección de aiohttp o UTF-8
            return content.decode(response.get_encoding() or 'utf-8', errors='replace')
            
    except asyncio.TimeoutError:
        return None
    except Exception:
        return None


async def extraer_datos_noticia_async(
    session: aiohttp.ClientSession, 
    url_noticia: str, 
    source_name: str, 
    semaphore: asyncio.Semaphore
) -> Noticia | None:
    """
    Extrae toda la información de una noticia individual de forma asíncrona.
    Usa semaphore para limitar conexiones concurrentes.
    """
    async with semaphore:
        try:
            html = await fetch_html(session, url_noticia)
            if not html:
                return None
            
            soup = BeautifulSoup(html, "html.parser")
            
            # Extraer título - múltiples selectores
            title = ""
            # Intentar primero <h1>
            h1_tag = soup.find('h1')
            if h1_tag:
                title = normalizar_texto(h1_tag.get_text(strip=True))
            
            # Si no hay title aún, intentar meta tags
            if not title:
                meta_title = soup.find('meta', property='og:title')
                if meta_title and meta_title.get('content'):
                    title = normalizar_texto(meta_title['content'])
            
            # Extraer subtítulo - varios selectores
            subtitle = None
            subtitle_selectors = ['h2', 'h3', ('p', {'class': 'lead'}), ('div', {'class': 'subtitle'})]
            for sel in subtitle_selectors:
                if isinstance(sel, tuple):
                    tag, attrs = sel
                    subtitle_tag = soup.find(tag, class_=attrs.get('class'))
                else:
                    subtitle_tag = soup.find(sel)
                if subtitle_tag:
                    subtitle = normalizar_texto(subtitle_tag.get_text(strip=True))
                    break
            
            # Extraer fecha
            published_at = None
            time_tag = soup.find('time', attrs={'datetime': True})
            if time_tag:
                try:
                    date_str = time_tag['datetime']
                    for fmt in ["%d/%m/%Y %H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"]:
                        try:
                            published_at = datetime.strptime(date_str.split('+')[0].split('Z')[0], fmt)
                            break
                        except ValueError:
                            continue
                except Exception:
                    pass
            
            # Extraer cuerpo
            body = ""
            article_containers = [
                soup.find('div', class_='itemFullText'),
                soup.find('article', class_='article-body-width'),
                soup.find('div', class_='entry-content'),
                soup.find('article'),
                soup.find('div', class_='content'),
                soup.find('div', class_='article-body'),
            ]
            
            for container in article_containers:
                if container:
                    paragraphs = container.find_all('p')
                    min_paragraphs = VALIDATION_CONFIG['min_paragraphs']
                    min_paragraph_length = VALIDATION_CONFIG['min_paragraph_length']
                    if paragraphs and len(paragraphs) >= min_paragraphs:
                        body = "\n\n".join([
                            normalizar_texto(p.get_text(strip=True)) 
                            for p in paragraphs 
                            if len(p.get_text(strip=True)) > min_paragraph_length
                        ])
                        break
            
            min_body_length = VALIDATION_CONFIG['min_body_length']
            if not title or len(body) < min_body_length:
                return None
            
            return Noticia(
                url=url_noticia,
                source=source_name,
                title=title,
                subtitle=subtitle,
                body=body,
                published_at=published_at
            )
            
        except Exception:
            return None


async def extraer_noticias_portada_async(
    session: aiohttp.ClientSession, 
    source_url: str, 
    source_name: str, 
    semaphore: asyncio.Semaphore
) -> list[Noticia]:
    """
    Extrae las noticias de la página principal de un diario de forma asíncrona.
    """
    start_time = time.time()
    
    try:
        print(f"\n🔍 Scrapeando: {source_name}")
        
        html = await fetch_html(session, source_url)
        if not html:
            print(f"   ❌ No se pudo obtener HTML")
            return []
        
        soup = BeautifulSoup(html, "html.parser")
        urls_noticias = []
        urls_procesadas = set()
        
        # Selectores de artículos desde configuración
        articles = []
        for tag, class_name in ARTICLE_SELECTORS:
            found = soup.find_all(tag, class_=class_name)
            min_articles = VALIDATION_CONFIG['min_articles_found']
            if found and len(found) > min_articles:
                articles = found
                break
        
        # Fallback: buscar todos los articles
        if not articles:
            articles = soup.find_all('article')
            min_articles = VALIDATION_CONFIG['min_articles_found']
            if not articles or len(articles) < min_articles:
                all_links = soup.find_all('a', href=True)
                article_containers = []
                for link in all_links:
                    href = link.get('href', '')
                    if any(pattern in href.lower() for pattern in URL_PATTERNS):
                        parent = link.find_parent(['article', 'div', 'li'])
                        if parent and parent not in article_containers:
                            article_containers.append(parent)
                articles = article_containers if len(article_containers) > min_articles else []
        
        if not articles:
            print(f"   ⚠️ No se encontraron artículos")
            return []
        
        # Extraer URLs
        # Asegurar que las URLs pertenezcan al mismo dominio
        source_domain = urlparse(source_url).netloc
        for article in articles:
            link = article.find('a', href=True)
            if link:
                url_completa = urljoin(source_url, link['href'])
                news_domain = urlparse(url_completa).netloc
                
                if (url_completa not in urls_procesadas and 
                    '{{' not in url_completa and 
                    source_domain == news_domain):
                    urls_procesadas.add(url_completa)
                    urls_noticias.append(url_completa)
        
        print(f"   📰 {source_name}:{len(articles)} artículos encontrados, procesando {len(urls_noticias)} URLs...")
        
        # Procesar todas las noticias EN PARALELO
        tasks = [
            extraer_datos_noticia_async(session, url, source_name, semaphore)
            for url in urls_noticias
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


async def scrape_all_sources_async(sources: list[dict], max_concurrent_requests: int) -> list[Noticia]:
    """
    Scrapea todas las fuentes de forma asíncrona y en paralelo.
    
    Args:
        sources: Lista de diccionarios con 'name' y 'url'
        max_concurrent_requests: Número máximo de requests HTTP concurrentes
    
    Returns:
        Lista de todas las noticias extraídas
    """
    start_time = time.time()
    
    print("=" * 60)
    print("🚀 SCRAPING ASÍNCRONO - MODO PARALELO")
    print("=" * 60)
    print(f"   Fuentes: {len(sources)}")
    print(f"   Conexiones concurrentes: {max_concurrent_requests}")
    
    semaphore = asyncio.Semaphore(max_concurrent_requests)
    
    limit_per_host = SCRAPING_CONFIG['limit_per_host']
    connector = aiohttp.TCPConnector(limit=max_concurrent_requests, limit_per_host=limit_per_host)
    async with aiohttp.ClientSession(connector=connector, headers=HEADERS) as session:
        # Procesar todas las fuentes EN PARALELO
        tasks = [
            extraer_noticias_portada_async(session, source['url'], source['name'], semaphore)
            for source in sources
        ]
        
        resultados_por_fuente = await asyncio.gather(*tasks)
    
    # Combinar todas las noticias
    todas_las_noticias = []
    for noticias in resultados_por_fuente:
        todas_las_noticias.extend(noticias)
    
    elapsed = time.time() - start_time
    
    print(f"\n{'=' * 60}")
    print(f"📊 RESUMEN FINAL:")
    print(f"   Fuentes procesadas: {len(sources)}")
    print(f"   Total noticias: {len(todas_las_noticias)}")
    print(f"   ⏱️  TIEMPO TOTAL: {elapsed:.2f}s ({elapsed/60:.2f} min)")
    if todas_las_noticias:
        print(f"   ⚡ Promedio: {elapsed/len(todas_las_noticias):.2f}s/noticia")
    print("=" * 60)
    
    return todas_las_noticias


def scrape_all_sources(sources: list[dict], max_concurrent_requests: int) -> list[Noticia]:
    """
    Wrapper síncrono para usar el scraper asíncrono desde código normal.
    """
    return asyncio.run(scrape_all_sources_async(sources, max_concurrent_requests))
