"""
Script temporal para generar reporte de noticias filtradas.
"""
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "app" / "db" / "news.db"
OUTPUT_FILE = Path(__file__).parent / "reporte_noticias.txt"


def get_noticia_with_relations(news_id: int, cursor) -> dict:
    """Obtiene una noticia con todas sus relaciones."""
    # Obtener noticia principal
    cursor.execute("SELECT * FROM news WHERE id = ?", (news_id,))
    row = cursor.fetchone()
    
    if not row:
        return None
    
    noticia = dict(zip([col[0] for col in cursor.description], row))
    
    # Obtener keywords
    cursor.execute("""
        SELECT k.name FROM keywords k
        JOIN news_keywords nk ON k.id = nk.keyword_id
        WHERE nk.news_id = ?
    """, (news_id,))
    noticia['keywords'] = [r[0] for r in cursor.fetchall()]
    
    # Obtener topics
    cursor.execute("""
        SELECT t.name FROM topics t
        JOIN news_topics nt ON t.id = nt.topic_id
        WHERE nt.news_id = ?
    """, (news_id,))
    noticia['topics'] = [r[0] for r in cursor.fetchall()]
    
    return noticia


def generate_report():
    """Genera reporte de todas las noticias."""
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Obtener todas las noticias relevantes
    cursor.execute("""
        SELECT id, url, source, title,
               ai_relevance_score, ai_decision, ai_reasoning,
               ai_sentiment, ai_sentiment_score, ai_sentiment_confidence,
               ai_tone, ai_main_topic
        FROM news
        WHERE ai_decision = 1
        ORDER BY ai_relevance_score DESC
    """)
    
    noticias = cursor.fetchall()
    
    # Generar reporte
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("=" * 100 + "\n")
        f.write("REPORTE DE NOTICIAS FILTRADAS - MUNICIPALIDAD DE SAN JUAN\n")
        f.write(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total de noticias relevantes: {len(noticias)}\n")
        f.write("=" * 100 + "\n\n")
        
        # Explicación compacta de campos
        f.write("GUÍA DE LECTURA:\n")
        f.write("─" * 100 + "\n")
        f.write("• Relevancia: 0.0-1.0 (umbral: 0.6 para aprobar)\n")
        f.write("• Sentimiento: positiva/negativa/neutral/mixta hacia la gestión municipal\n")
        f.write("• Sentiment Score: -1.0 (muy negativo) a +1.0 (muy positivo)\n")
        f.write("• Tono: informativo/crítico/elogioso/investigativo/sensacionalista\n")
        f.write("• Topics: Categorías asignadas (máximo 3 por noticia)\n")
        f.write("• Keywords: Nombres propios, lugares, programas mencionados\n")
        f.write("=" * 100 + "\n\n\n")
        
        for idx, row in enumerate(noticias, 1):
            (news_id, url, source, title,
             ai_score, ai_decision, ai_reasoning,
             ai_sentiment, ai_sentiment_score, ai_sentiment_confidence,
             ai_tone, ai_main_topic) = row
            
            # Obtener relaciones
            noticia_full = get_noticia_with_relations(news_id, cursor)
            
            f.write(f"{'─' * 100}\n")
            f.write(f"[{idx}] {title}\n")
            f.write(f"{'─' * 100}\n")
            f.write(f"Fuente: {source}\n")
            f.write(f"URL: {url}\n\n")
            
            f.write(f"Relevancia: {ai_score:.3f} | Sentimiento: {ai_sentiment or 'N/A'} ({ai_sentiment_score or 'N/A'}) | Tono: {ai_tone or 'N/A'}\n")
            f.write(f"Razonamiento IA: {ai_reasoning or 'N/A'}\n\n")
            
            f.write(f"Topic Principal: {ai_main_topic or 'N/A'}\n")
            if noticia_full['topics']:
                f.write(f"Todos los Topics: {', '.join(noticia_full['topics'])}\n")
            
            if noticia_full['keywords']:
                keywords_str = ', '.join(noticia_full['keywords'])
                f.write(f"Keywords: {keywords_str}\n")
            
            f.write(f"\n\n")
        
        # Resumen estadístico
        f.write(f"\n{'=' * 100}\n")
        f.write("RESUMEN ESTADÍSTICO\n")
        f.write(f"{'=' * 100}\n\n")
        
        # Top topics
        cursor.execute("""
            SELECT t.name, COUNT(*) as count
            FROM topics t
            JOIN news_topics nt ON t.id = nt.topic_id
            JOIN news n ON nt.news_id = n.id
            WHERE n.ai_decision = 1
            GROUP BY t.name
            ORDER BY count DESC
            LIMIT 10
        """)
        
        f.write("📊 TOP 10 TOPICS:\n")
        for topic, count in cursor.fetchall():
            f.write(f"   {count:3d} - {topic}\n")
        
        f.write("\n")
        
        # Top keywords
        cursor.execute("""
            SELECT k.name, COUNT(*) as count
            FROM keywords k
            JOIN news_keywords nk ON k.id = nk.keyword_id
            JOIN news n ON nk.news_id = n.id
            WHERE n.ai_decision = 1
            GROUP BY k.name
            ORDER BY count DESC
            LIMIT 15
        """)
        
        f.write("🔑 TOP 15 KEYWORDS:\n")
        for keyword, count in cursor.fetchall():
            f.write(f"   {count:3d} - {keyword}\n")
        
        f.write("\n")
        
        # Sentimientos
        cursor.execute("""
            SELECT ai_sentiment, COUNT(*) as count
            FROM news
            WHERE ai_decision = 1 AND ai_sentiment IS NOT NULL
            GROUP BY ai_sentiment
        """)
        
        f.write("😊 DISTRIBUCIÓN DE SENTIMIENTOS:\n")
        for sentiment, count in cursor.fetchall():
            f.write(f"   {count:3d} - {sentiment}\n")
        
        f.write("\n")
        
        # Tonos
        cursor.execute("""
            SELECT ai_tone, COUNT(*) as count
            FROM news
            WHERE ai_decision = 1 AND ai_tone IS NOT NULL
            GROUP BY ai_tone
        """)
        
        f.write("🎭 DISTRIBUCIÓN DE TONOS:\n")
        for tone, count in cursor.fetchall():
            f.write(f"   {count:3d} - {tone}\n")
    
    conn.close()
    
    print(f"✅ Reporte generado: {OUTPUT_FILE}")
    print(f"📊 Total de noticias: {len(noticias)}")


if __name__ == "__main__":
    generate_report()
