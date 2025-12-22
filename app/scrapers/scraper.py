"""
Scraper universal para extraer noticias de la página principal de cualquier diario.
"""
import requests
from bs4 import BeautifulSoup
from app.models.noticia import Noticia
from urllib.parse import urljoin, urlparse
from datetime import datetime
import time
import unicodedata


def normalizar_texto(texto):
    """
    Normaliza el texto corrigiendo codificación y eliminando tildes.
    Mantiene la ñ y otros caracteres especiales del español.
    """
    if not texto:
        return texto
    
    # Primero normalizar a NFC para corregir caracteres mal codificados
    texto = unicodedata.normalize('NFC', texto)
    
    # Eliminar tildes pero mantener ñ, ü y otros caracteres base del español:
    # NFD descompone caracteres con acento (á → a + ́)
    # pero la ñ no se descompone porque es un carácter único del alfabeto español
    texto_sin_tildes = ''.join(
        char for char in unicodedata.normalize('NFD', texto)
        if unicodedata.category(char) != 'Mn'  # Mn = Nonspacing_Mark (tildes/acentos)
    )
    
    return texto_sin_tildes


def extraer_datos_noticia(url_noticia, source_name):
    """
    Extrae toda la información de una noticia individual.
    Intenta ser lo más genérico posible para funcionar con diferentes diarios.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        }
        response = requests.get(url_noticia, timeout=10, headers=headers)
        
        # Usar apparent_encoding para detectar la codificación correcta
        if response.apparent_encoding:
            response.encoding = response.apparent_encoding
        
        soup = BeautifulSoup(response.text, "html.parser")
        
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
        
        # Extraer fecha de publicación
        published_at = None
        time_tag = soup.find('time', attrs={'datetime': True})
        if time_tag:
            try:
                date_str = time_tag['datetime']
                # Intentar diferentes formatos de fecha
                for fmt in ["%d/%m/%Y %H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"]:
                    try:
                        published_at = datetime.strptime(date_str.split('+')[0].split('Z')[0], fmt)
                        break
                    except ValueError:
                        continue
            except Exception:
                pass
        
        # Extraer cuerpo - estrategia más robusta
        body = ""
        # Buscar primero en contenedores comunes de artículos
        article_containers = [
            soup.find('div', class_='itemFullText'),  # SI San Juan
            soup.find('article', class_='article-body-width'),  # San Juan 8
            soup.find('div', class_='entry-content'),  # WordPress general
            soup.find('article'),
            soup.find('div', class_='content'),
            soup.find('div', class_='article-body'),
        ]
        
        for container in article_containers:
            if container:
                paragraphs = container.find_all('p')
                if paragraphs and len(paragraphs) >= 2:  # Al menos 2 párrafos
                    body = "\n\n".join([normalizar_texto(p.get_text(strip=True)) for p in paragraphs if len(p.get_text(strip=True)) > 20])
                    break
        
        # Si no se encontró contenido suficiente, no crear la noticia
        if not title or len(body) < 100:
            return None
        
        # Crear y retornar la noticia
        noticia = Noticia(
            url=url_noticia,
            source=source_name,
            title=title,
            subtitle=subtitle,
            body=body,
            published_at=published_at
        )
        
        return noticia
    except Exception as e:
        print(f"  Error al extraer datos de {url_noticia}: {e}")
        return None


def extraer_noticias_portada(source_url, source_name):
    """
    Extrae las noticias de la página principal de un diario.
    Busca artículos con clase 'entry-box' (común en muchos sitios).
    """
    start_time_source = time.time()
    
    try:
        print(f"\nScrapeando: {source_name}")
        print(f"URL: {source_url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        }
        response = requests.get(source_url, timeout=10, headers=headers)
        
        # Usar apparent_encoding para detectar la codificación correcta
        if response.apparent_encoding:
            response.encoding = response.apparent_encoding
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        noticias = []
        urls_procesadas = set()
        
        # Estrategia 1: Buscar artículos con selectores específicos
        # Ahora incluye selectores personalizados por sitio
        article_selectors = [
            # San Juan 8 - usa <article> con varias clases
            ('article', 'news-article'),
            ('article', 'article-badge-in-image'),
            # SI San Juan - usa <div> con clase gkNewsElement
            ('div', 'gkNewsElement'),
            ('div', 'nspArt'),
            # El Sol de San Juan - usa Read article y estructura específica
            ('article', 'wp-block-post'),
            ('div', 'post-item'),
            # Selectores genéricos
            ('article', 'entry-box'),
            ('article', 'card'),
            ('article', 'article'),
            ('article', 'post'),
            ('article', 'nota'),
            ('article', 'noticia'),
            ('div', 'article'),
            ('div', 'card'),
            ('div', 'news-item'),
            ('div', 'post'),
            ('div', 'nota'),
            ('div', 'noticia'),
        ]
        
        articles = []
        selector_usado = None
        
        for tag, class_name in article_selectors:
            found = soup.find_all(tag, class_=class_name)
            if found and len(found) > 3:  # Al menos 3 artículos para considerar válido
                articles = found
                selector_usado = f"{tag}.{class_name}"
                break
        
        # Estrategia 2: Si no encuentra con clases específicas, buscar todos los <article> o <a> con hrefs
        if not articles:
            # Intentar buscar todos los <article> sin clase específica
            articles = soup.find_all('article')
            if articles and len(articles) > 3:
                selector_usado = "article (genérico)"
            else:
                # Última estrategia: buscar enlaces que parezcan noticias
                print(f"  Intentando estrategia alternativa: buscar enlaces de noticias...")
                all_links = soup.find_all('a', href=True)
                
                # Filtrar enlaces que parezcan URLs de noticias
                article_containers = []
                for link in all_links:
                    href = link.get('href', '')
                    # Patrones comunes de URLs de noticias (ampliados para cubrir más casos)
                    patterns = [
                        '/noticia', '/nota', '/post', '/articulo', '/news', '202',
                        '/prensa', '/gobierno', '/deportes', '/economia', '/salud',
                        '/policiales', '/san-juan', '/ovacion', '/pais',
                        '-n1', '-n2', '-n3', '-n4', '-n5', '-n6', '-n7', '-n8', '-n9'  # Para San Juan 8
                    ]
                    if any(pattern in href.lower() for pattern in patterns):
                        # Encontrar el contenedor padre que tenga más contenido
                        parent = link.find_parent(['article', 'div', 'li', 'section'])
                        if parent and parent not in article_containers:
                            article_containers.append(parent)
                
                if article_containers and len(article_containers) > 3:
                    articles = article_containers
                    selector_usado = "enlaces de noticias (detección automática)"
        
        if articles:
            print(f"  Encontrados {len(articles)} artículos con: {selector_usado}")
        else:
            print(f"  ⚠ No se encontraron artículos en la página principal")
            return []
        
        print(f"  Procesando artículos...")
        
        for i, article in enumerate(articles, 1):
            link = article.find('a', href=True)
            if link:
                url_completa = urljoin(source_url, link['href'])
                
                # Validar que sea una URL del mismo dominio
                source_domain = urlparse(source_url).netloc
                news_domain = urlparse(url_completa).netloc
                
                # Evitar duplicados, plantillas y URLs de otros dominios
                if (url_completa not in urls_procesadas and 
                    '{{' not in url_completa and 
                    source_domain == news_domain):
                    
                    urls_procesadas.add(url_completa)
                    
                    # Mostrar progreso
                    print(f"    [{i}/{len(articles)}] Extrayendo: {url_completa[:80]}...")
                    
                    # Extraer datos completos de la noticia
                    start_time_noticia = time.time()
                    noticia = extraer_datos_noticia(url_completa, source_name)
                    elapsed_noticia = time.time() - start_time_noticia
                    
                    if noticia:
                        noticias.append(noticia)
                        print(f"      ✓ Extraída: {noticia.title[:60]}... ({elapsed_noticia:.2f}s)")
                        
                    else:
                        print(f"      ✗ No se pudo extraer ({elapsed_noticia:.2f}s)")
        
        elapsed_source = time.time() - start_time_source
        print(f"  ✅ Noticias extraídas exitosamente: {len(noticias)}")
        print(f"  ⏱️  Tiempo total para esta fuente: {elapsed_source:.2f}s ({elapsed_source/60:.2f} min)")
        return noticias
        
    except Exception as e:
        elapsed_source = time.time() - start_time_source
        print(f"  ❌ Error al extraer noticias de {source_url}: {e}")
        print(f"  ⏱️  Tiempo transcurrido: {elapsed_source:.2f}s")
        return []


def scrape_all_sources(sources):
    """
    Scrapea todas las fuentes proporcionadas.
    
    Args:
        sources: Lista de diccionarios con 'name' y 'url'
    
    Returns:
        Lista de todas las noticias extraídas
    """
    start_time_total = time.time()
    todas_las_noticias = []
    
    print("="*60)
    print("INICIANDO SCRAPING DE FUENTES")
    print("="*60)
    
    for i, source in enumerate(sources, 1):
        print(f"\n[{i}/{len(sources)}] Procesando: {source['name']}")
        
        noticias = extraer_noticias_portada(source['url'], source['name'])
        todas_las_noticias.extend(noticias)
    
    elapsed_total = time.time() - start_time_total
    
    print(f"\n{'='*60}")
    print(f"RESUMEN FINAL:")
    print(f"Total de fuentes procesadas: {len(sources)}")
    print(f"Total de noticias extraídas: {len(todas_las_noticias)}")
    print(f"⏱️  TIEMPO TOTAL: {elapsed_total:.2f}s ({elapsed_total/60:.2f} min)")
    if len(todas_las_noticias) > 0:
        print(f"⏱️  Tiempo promedio por noticia: {elapsed_total/len(todas_las_noticias):.2f}s")
    print(f"{'='*60}\n")
    
    return todas_las_noticias
