"""
Script principal para ejecutar los scrapers del proyecto.
Scrapea noticias de múltiples diarios configurados en config/sources.py
"""
from app.scrapers.scraper import scrape_all_sources
from app.db.database import init_database, insert_noticias_bulk, get_noticias_count
from config.sources import get_enabled_sources
from config.ai_config import get_ai_config
from app.utils.ai_filter import AIFilter, get_ai_filter


def filtrar_con_ia(noticias, ai_filter: AIFilter):
    """Filtra noticias usando IA si está habilitada."""
    if not ai_filter:
        return noticias
    
    print(f"\n🤖 Filtrado con IA ({ai_filter.provider.__class__.__name__}):")
    print(f"   Umbral de relevancia: {ai_filter.relevance_threshold}")
    print(f"   Analizando {len(noticias)} noticias...\n")
    
    noticias_relevantes = ai_filter.filter_noticias(noticias, verbose=True)
    
    stats = ai_filter.get_stats()
    print(f"\n   📊 Resultados IA:")
    print(f"      Total analizadas: {stats['total_analyzed']}")
    print(f"      Relevantes: {stats['relevant']}")
    print(f"      No relevantes: {stats['not_relevant']}")
    if stats['errors'] > 0:
        print(f"      Errores: {stats['errors']}")
    
    return noticias_relevantes


if __name__ == "__main__":
    print("\n=== News Scraper - Multi-Source ===\n")
    # Inicializar base de datos
    print("📊 Inicializando base de datos...")
    init_database()
    print(f"   Noticias en BD antes de scrapear: {get_noticias_count()}\n")
    
    # Cargar configuración de IA
    ai_config = get_ai_config()
    ai_filter = get_ai_filter(ai_config)
    
    if ai_filter:
        print(f"🤖 Filtrado IA habilitado: Groq ({ai_config['model']})")
    else:
        print("🤖 Filtrado IA deshabilitado (solo keywords)")
    print()

    # Obtener fuentes habilitadas
    sources = get_enabled_sources()
    
    if not sources:
        print("⚠ No hay fuentes habilitadas en config/sources.py")
        exit(1)
    
    print(f"Fuentes habilitadas: {', '.join([s['name'] for s in sources])}\n")
    

    # Ejecutar scraping
    noticias = scrape_all_sources(sources)
    

    # Filtrar noticias por keywords (pre-filtro rápido)
    if noticias:
        from config.sources import noticia_contiene_keywords
        
        noticias_filtradas = [n for n in noticias if noticia_contiene_keywords(n)]
        
        print(f"\n🔍 Filtrado por keywords (pre-filtro):")
        print(f"   Total scrapeadas: {len(noticias)}")
        print(f"   Con keywords: {len(noticias_filtradas)}")
        print(f"   Descartadas: {len(noticias) - len(noticias_filtradas)}")
        
        noticias = noticias_filtradas
        
        # Filtrar con IA (si está habilitado)
        if ai_filter and noticias:
            noticias = filtrar_con_ia(noticias, ai_filter)
    
    
    # Guardar en la base de datos
    if noticias:
        print(f"\n💾 Guardando noticias en la base de datos...")
        stats = insert_noticias_bulk(noticias)
        
        print(f"   ✅ Insertadas: {stats['insertadas']}")
        print(f"   ⏭️  Duplicadas (ignoradas): {stats['duplicadas']}")
        if stats['errores'] > 0:
            print(f"   ❌ Errores: {stats['errores']}")
        
        print(f"\n📊 Total de noticias en BD: {get_noticias_count()}")
        print(f"\n✓ Proceso completado exitosamente")
    else:
        print("\n⚠ No se extrajeron noticias")
