"""
Módulo para gestionar operaciones de base de datos.
"""
import sqlite3
import logging
from pathlib import Path
from typing import List, Optional
from app.models.noticia import Noticia


logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).resolve().parent / "news.db"


def get_connection():
    """Obtiene una conexión a la base de datos."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # Para acceder a columnas por nombre
    conn.execute("PRAGMA foreign_keys = ON")  # Habilitar foreign keys
    return conn


def init_database():
    """Inicializa la base de datos creando las tablas necesarias."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tabla principal de noticias
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT UNIQUE NOT NULL,
        source TEXT NOT NULL,
        title TEXT NOT NULL,
        subtitle TEXT,
        body TEXT,
        published_at TEXT,
        scraped_at TEXT DEFAULT CURRENT_TIMESTAMP,
        
        ai_relevance_score REAL,
        ai_decision INTEGER,
        ai_reasoning TEXT,
        
        ai_sentiment TEXT,
        ai_sentiment_score REAL,
        ai_sentiment_confidence REAL,
        ai_tone TEXT,
        ai_main_topic TEXT
    )
    """)
    
    # Tabla de keywords
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS keywords (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    """)
    
    # Relación news-keywords (muchos a muchos)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS news_keywords (
        news_id INTEGER,
        keyword_id INTEGER,
        FOREIGN KEY (news_id) REFERENCES news(id) ON DELETE CASCADE,
        FOREIGN KEY (keyword_id) REFERENCES keywords(id),
        PRIMARY KEY (news_id, keyword_id)
    )
    """)
    
    # Tabla de topics
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS topics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    """)
    
    # Relación news-topics (muchos a muchos)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS news_topics (
        news_id INTEGER,
        topic_id INTEGER,
        FOREIGN KEY (news_id) REFERENCES news(id) ON DELETE CASCADE,
        FOREIGN KEY (topic_id) REFERENCES topics(id),
        PRIMARY KEY (news_id, topic_id)
    )
    """)
    
    # # Tabla de actores
    # cursor.execute("""
    # CREATE TABLE IF NOT EXISTS actors (
    #     id INTEGER PRIMARY KEY AUTOINCREMENT,
    #     name TEXT UNIQUE NOT NULL
    # )
    # """)
    
    # # Relación news-actors (muchos a muchos)
    # cursor.execute("""
    # CREATE TABLE IF NOT EXISTS news_actors (
    #     news_id INTEGER,
    #     actor_id INTEGER,
    #     role TEXT,
    #     FOREIGN KEY (news_id) REFERENCES news(id) ON DELETE CASCADE,
    #     FOREIGN KEY (actor_id) REFERENCES actors(id),
    #     PRIMARY KEY (news_id, actor_id)
    # )
    # """)
    
    # Índices para mejorar performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_keywords_news ON news_keywords(news_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_keywords_keyword ON news_keywords(keyword_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_topics_news ON news_topics(news_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_topics_topic ON news_topics(topic_id)")
    # cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_actors_news ON news_actors(news_id)")
    # cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_actors_actor ON news_actors(actor_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_source ON news(source)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_published ON news(published_at)")

    # Poblar tabla de topics con los permitidos
    from config.settings import get_allowed_topics
    allowed_topics = get_allowed_topics()
    
    for topic in allowed_topics:
        cursor.execute("INSERT OR IGNORE INTO topics (name) VALUES (?)", (topic,))
    
    conn.commit()
    conn.close()
    logger.info("Base de datos inicializada correctamente")


def _insert_keywords(cursor, news_id: int, keywords: List[str]):
    """Inserta keywords y sus relaciones con la noticia."""
    if not keywords:
        return
    for keyword in keywords:
        cursor.execute("INSERT OR IGNORE INTO keywords (name) VALUES (?)", (keyword,))
        cursor.execute("SELECT id FROM keywords WHERE name = ?", (keyword,))
        keyword_id = cursor.fetchone()[0]
        cursor.execute("INSERT OR IGNORE INTO news_keywords (news_id, keyword_id) VALUES (?, ?)", (news_id, keyword_id))


def _insert_topics(cursor, news_id: int, topics: List[str]):
    """Inserta topics y sus relaciones con la noticia."""
    if not topics:
        return
    for topic in topics:
        cursor.execute("INSERT OR IGNORE INTO topics (name) VALUES (?)", (topic,))
        cursor.execute("SELECT id FROM topics WHERE name = ?", (topic,))
        topic_id = cursor.fetchone()[0]
        cursor.execute("INSERT OR IGNORE INTO news_topics (news_id, topic_id) VALUES (?, ?)", (news_id, topic_id))


# def _insert_actors(cursor, news_id: int, actors: dict):
    # """Inserta actores y sus relaciones con la noticia."""
    # if not actors:
    #     return
    # for actor_name, role in actors.items():
    #     cursor.execute("INSERT OR IGNORE INTO actors (name) VALUES (?)", (actor_name,))
    #     cursor.execute("SELECT id FROM actors WHERE name = ?", (actor_name,))
    #     actor_id = cursor.fetchone()[0]
    #     cursor.execute("INSERT OR IGNORE INTO news_actors (news_id, actor_id, role) VALUES (?, ?, ?)", (news_id, actor_id, role))


def insert_noticia(noticia: Noticia) -> bool:
    """
    Inserta una noticia en la base de datos con todas sus relaciones.
    Retorna True si fue exitosa, False si ya existe.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Insertar noticia principal
        cursor.execute("""
        INSERT INTO news (url, source, title, subtitle, body, published_at, scraped_at,
                         ai_relevance_score, ai_decision, ai_reasoning,
                         ai_sentiment, ai_sentiment_score, ai_sentiment_confidence,
                         ai_tone, ai_main_topic)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            noticia.url,
            noticia.source,
            noticia.title,
            noticia.subtitle,
            noticia.body,
            noticia.published_at.isoformat() if noticia.published_at else None,
            noticia.scraped_at.isoformat(),
            noticia.ai_relevance_score,
            1 if noticia.ai_decision else (0 if noticia.ai_decision is not None else None),
            noticia.ai_reasoning,
            noticia.ai_sentiment,
            noticia.ai_sentiment_score,
            noticia.ai_sentiment_confidence,
            noticia.ai_tone,
            noticia.ai_main_topic
        ))
        
        news_id = cursor.lastrowid
        
        # Insertar relaciones
        _insert_keywords(cursor, news_id, noticia.ai_keywords_found)
        _insert_topics(cursor, news_id, noticia.ai_topics)
        # _insert_actors(cursor, news_id, noticia.ai_actors)
        
        conn.commit()
        conn.close()
        return True
        
    except sqlite3.IntegrityError as e:
        logger.debug(f"Noticia duplicada: {noticia.url}")
        return False
    except Exception as e:
        logger.error(f"Error al insertar noticia: {e}")
        return False


def insert_noticias_bulk(noticias: List[Noticia]) -> dict:
    """
    Inserta múltiples noticias en la base de datos con sus relaciones.
    
    Returns:
        dict con estadísticas: {'insertadas': int, 'duplicadas': int, 'errores': int}
    """
    stats = {'insertadas': 0, 'duplicadas': 0, 'errores': 0}
    
    conn = get_connection()
    cursor = conn.cursor()
    
    for i, noticia in enumerate(noticias, 1):
        try:
            # Insertar noticia principal
            cursor.execute("""
            INSERT INTO news (url, source, title, subtitle, body, published_at, scraped_at,
                             ai_relevance_score, ai_decision, ai_reasoning,
                             ai_sentiment, ai_sentiment_score, ai_sentiment_confidence,
                             ai_tone, ai_main_topic)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                noticia.url,
                noticia.source,
                noticia.title,
                noticia.subtitle,
                noticia.body,
                noticia.published_at.isoformat() if noticia.published_at else None,
                noticia.scraped_at.isoformat(),
                noticia.ai_relevance_score,
                1 if noticia.ai_decision else (0 if noticia.ai_decision is not None else None),
                noticia.ai_reasoning,
                noticia.ai_sentiment,
                noticia.ai_sentiment_score,
                noticia.ai_sentiment_confidence,
                noticia.ai_tone,
                noticia.ai_main_topic
            ))
            
            news_id = cursor.lastrowid
            
            # Insertar relaciones
            _insert_keywords(cursor, news_id, noticia.ai_keywords_found)
            _insert_topics(cursor, news_id, noticia.ai_topics)
            # _insert_actors(cursor, news_id, noticia.ai_actors)
            
            conn.commit()
            stats['insertadas'] += 1
            
        except sqlite3.IntegrityError:
            stats['duplicadas'] += 1
            logger.debug(f"[{i}/{len(noticias)}] Duplicada: {noticia.url}")
        except Exception as e:
            stats['errores'] += 1
            logger.error(f"[{i}/{len(noticias)}] Error al insertar {noticia.url}: {e}")
    
    conn.close()
    
    return stats


def get_noticias_count() -> int:
    """Retorna el número total de noticias en la base de datos."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM news")
    count = cursor.fetchone()[0]
    
    conn.close()
    return count


def get_noticias_by_source(source: str) -> List[dict]:
    """Obtiene todas las noticias de una fuente específica."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM news WHERE source = ? ORDER BY scraped_at DESC", (source,))
    rows = cursor.fetchall()
    
    conn.close()
    
    return [dict(row) for row in rows]


def delete_all_noticias():
    """Elimina todas las noticias de la base de datos (cascade elimina relaciones)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM news")
    
    conn.commit()
    conn.close()
    logger.info("Todas las noticias eliminadas")