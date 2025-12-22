"""
Script principal para ejecutar los scrapers del proyecto.
Scrapea noticias de múltiples diarios configurados en config/sources.py
"""
from app.scrapers.scraper import scrape_all_sources
from app.db.database import init_database, insert_noticias_bulk, get_noticias_count
from config.sources import get_enabled_sources


if __name__ == "__main__":
    print("\n=== News Scraper - Multi-Source ===\n")
    
    # Inicializar base de datos
    print("📊 Inicializando base de datos...")
    init_database()
    print(f"   Noticias en BD antes de scrapear: {get_noticias_count()}\n")
    

    # Obtener fuentes habilitadas
    sources = get_enabled_sources()
    
    if not sources:
        print("⚠ No hay fuentes habilitadas en config/sources.py")
        exit(1)
    
    print(f"Fuentes habilitadas: {', '.join([s['name'] for s in sources])}\n")
    

    # Ejecutar scraping
    noticias = scrape_all_sources(sources)
    

    # Filtrar noticias por keywords
    if noticias:
        from config.sources import noticia_contiene_keywords
        
        noticias_filtradas = [n for n in noticias if noticia_contiene_keywords(n)]
        
        print(f"\n🔍 Filtrado por keywords:")
        print(f"   Total scrapeadas: {len(noticias)}")
        print(f"   Con keywords: {len(noticias_filtradas)}")
        print(f"   Descartadas: {len(noticias) - len(noticias_filtradas)}")
        
        noticias = noticias_filtradas
    
    
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
