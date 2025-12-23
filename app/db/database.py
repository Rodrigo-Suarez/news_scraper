"""
Módulo para gestionar operaciones de base de datos.
"""
import sqlite3
from pathlib import Path
from typing import List
from app.models.noticia import Noticia


DB_PATH = Path(__file__).resolve().parent / "news.db"


def get_connection():
    """Obtiene una conexión a la base de datos."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # Para acceder a columnas por nombre
    return conn


def init_database():
    """Inicializa la base de datos creando las tablas necesarias."""
    conn = get_connection()
    cursor = conn.cursor()
    
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
        ai_reasoning TEXT
    )
    """)
    
    # Migración: agregar columnas de IA si no existen (para DBs existentes)
    try:
        cursor.execute("ALTER TABLE news ADD COLUMN ai_relevance_score REAL")
    except Exception:
        pass  # Columna ya existe
    try:
        cursor.execute("ALTER TABLE news ADD COLUMN ai_decision INTEGER")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE news ADD COLUMN ai_reasoning TEXT")
    except Exception:
        pass
    
    conn.commit()
    conn.close()


def insert_noticia(noticia: Noticia) -> bool:
    """
    Inserta una noticia en la base de datos.
    Retorna True si fue exitosa, False si ya existe.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO news (url, source, title, subtitle, body, published_at, scraped_at, ai_relevance_score, ai_decision, ai_reasoning)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            noticia.ai_reasoning
        ))
        
        conn.commit()
        conn.close()
        return True
        
    except sqlite3.IntegrityError as e:
        # La noticia ya existe (URL duplicada)
        print(f"IntegrityError: {e}")
        return False
    except Exception as e:
        print(f"Error al insertar noticia: {e}")
        import traceback
        traceback.print_exc()
        return False


def insert_noticias_bulk(noticias: List[Noticia]) -> dict:
    """
    Inserta múltiples noticias en la base de datos.
    
    Returns:
        dict con estadísticas: {'insertadas': int, 'duplicadas': int, 'errores': int}
    """
    stats = {'insertadas': 0, 'duplicadas': 0, 'errores': 0}
    
    conn = get_connection()
    cursor = conn.cursor()
    
    for i, noticia in enumerate(noticias, 1):
        try:
            cursor.execute("""
            INSERT INTO news (url, source, title, subtitle, body, published_at, scraped_at, ai_relevance_score, ai_decision, ai_reasoning)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                noticia.ai_reasoning
            ))
            conn.commit()  # Commit después de cada inserción exitosa
            stats['insertadas'] += 1
            
        except sqlite3.IntegrityError as e:
            stats['duplicadas'] += 1
            print(f"   [{i}/{len(noticias)}] Duplicada: {noticia.url}")
        except Exception as e:
            stats['errores'] += 1
            print(f"   [{i}/{len(noticias)}] Error al insertar {noticia.url}: {e}")
    
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
    """Elimina todas las noticias de la base de datos."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM news")
    
    conn.commit()
    conn.close()
