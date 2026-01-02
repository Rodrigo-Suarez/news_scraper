"""
Script principal para ejecutar los scrapers del proyecto.
Scrapea noticias de múltiples diarios configurados en config/sources.py
"""

from app.scrapers import AsyncNewsScraper
from app.db.database import init_database, insert_noticias_bulk, get_noticias_count
from config.sources import get_enabled_sources
from config.ai_config import get_ai_config
from config.settings import get_scraping_config
from app.utils.ai_filter import AIFilter, get_ai_filter
from config.logging_config import setup_logging, get_logger
from config.settings import get_logging_config


def filtrar_con_ia(noticias, ai_filter: AIFilter):
    """Filtra noticias usando IA si está habilitada."""
    if not ai_filter:
        return noticias
    
    logger.info(f"🤖 Filtrado con IA ({ai_filter.provider.__class__.__name__}):")
    logger.info(f"   Umbral de relevancia: {ai_filter.relevance_threshold}")
    logger.info(f"   Analizando {len(noticias)} noticias...")
    
    noticias_relevantes = ai_filter.filter_noticias(noticias)
    
    stats = ai_filter.get_stats()
    logger.info(f"   📊 Resultados IA:")
    logger.info(f"      Total analizadas: {stats['total_analyzed']}")
    logger.info(f"      Relevantes: {stats['relevant']}")
    logger.info(f"      No relevantes: {stats['not_relevant']}")
    if stats['errors'] > 0:
        logger.warning(f"      Errores: {stats['errors']}")
    
    return noticias_relevantes


if __name__ == "__main__":
    # Inicializar logging
    logging_config = get_logging_config()
    setup_logging(**logging_config)
    logger = get_logger(__name__)

    logger.info("=== News Scraper - Multi-Source ===")
    # Inicializar base de datos
    logger.info("📊 Inicializando base de datos...")
    init_database()
    logger.info(f"Noticias en BD antes de scrapear: {get_noticias_count()}")
    
    # Cargar configuración de IA
    ai_config = get_ai_config()
    ai_filter = get_ai_filter(ai_config)
    
    # Cargar configuración de scraping
    scraping_config = get_scraping_config()
    max_concurrent = scraping_config['max_concurrent_requests']
    
    if ai_filter:
        logger.info(f"🤖 Filtrado IA habilitado: Groq ({ai_config['model']})")
    else:
        logger.info("🤖 Filtrado IA deshabilitado (solo keywords)")

    logger.info(f"⚡ Scraping asíncrono: {max_concurrent} requests concurrentes")

    # Obtener fuentes habilitadas
    sources = get_enabled_sources()
    
    if not sources:
        logger.warning("⚠ No hay fuentes habilitadas en config/sources.py")
        exit(1)
    
    logger.info(f"Fuentes habilitadas: {', '.join([s['name'] for s in sources])}")
    
    # Ejecutar scraping
    scraper = AsyncNewsScraper(max_concurrent_requests=max_concurrent)
    noticias = scraper.scrape(sources)
    

    # Filtrar noticias por keywords (pre-filtro rápido)
    if noticias:
        from config.sources import noticia_contiene_keywords
        
        noticias_filtradas = [n for n in noticias if noticia_contiene_keywords(n)]
        
        logger.info(f"🔍 Filtrado por keywords (pre-filtro):")
        logger.info(f"   Total scrapeadas: {len(noticias)}")
        logger.info(f"   Con keywords: {len(noticias_filtradas)}")
        logger.info(f"   Descartadas: {len(noticias) - len(noticias_filtradas)}")
        
        noticias = noticias_filtradas
        
        # Filtrar con IA (si está habilitado)
        if ai_filter and noticias:
            noticias = filtrar_con_ia(noticias, ai_filter)
    
    
    # Guardar en la base de datos
    if noticias:
        logger.info(f"💾 Guardando noticias en la base de datos...")
        stats = insert_noticias_bulk(noticias)
        
        logger.info(f"   ✅ Insertadas: {stats['insertadas']}")
        logger.info(f"   ⏭️  Duplicadas (ignoradas): {stats['duplicadas']}")
        if stats['errores'] > 0:
            logger.error(f"   ❌ Errores: {stats['errores']}")
        
        logger.info(f"📊 Total de noticias en BD: {get_noticias_count()}")
        logger.info(f"✓ Proceso completado exitosamente")
    else:
        logger.warning("⚠ No se extrajeron noticias")