# config/logging_config.py
"""
Configuración centralizada de logging para el proyecto.
"""
import logging
import sys
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler



class ColoredFormatter(logging.Formatter):
    """Formatter con colores ANSI (funciona en todos lados)."""
    
    # Códigos ANSI de colores
    GREY = '\033[90m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD_RED = '\033[91;1m'
    RESET = '\033[0m'
    
    # Colores por nivel
    LEVEL_COLORS = {
        logging.DEBUG: GREY,
        logging.INFO: GREEN,
        logging.WARNING: YELLOW,
        logging.ERROR: RED,
        logging.CRITICAL: BOLD_RED,
    }
    
    def format(self, record):
        # Color del nivel
        level_color = self.LEVEL_COLORS.get(record.levelno, self.RESET)
        
        # Formatear con colores
        time_str = self.formatTime(record, self.datefmt)
        
        log_fmt = (
            f"{level_color}[{record.levelname}]{self.RESET} - "
            f"{self.BLUE}{time_str}{self.RESET} - "
            # f"{self.GREY}{record.name}{self.RESET} - "
            f"{record.getMessage()}{self.RESET}"
        )
        
        return log_fmt

def setup_logging(
    level: str = "INFO",
    log_to_file: bool = True,
    log_dir: str = "logs",
    log_filename: str = "news_scraper.log"
):
    """
    Configura el sistema de logging para todo el proyecto.
    
    Args:
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Si guardar logs en archivo
        log_dir: Directorio donde guardar los logs
        log_filename: Nombre del archivo de log
    """
    # Crear directorio de logs si no existe
    if log_to_file:
        Path(log_dir).mkdir(exist_ok=True)
    
    # Formato de los mensajes
    file_log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    console_log_format = "%(levelname)s - %(asctime)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Handlers
    handlers = []
    
    # Console handler (siempre)
    console_handler = logging.StreamHandler(sys.stdout) # Log a consola
    console_handler.setLevel(getattr(logging, level)) # Nivel dinámico
    console_handler.setFormatter(ColoredFormatter(console_log_format, date_format))
    handlers.append(console_handler)
    
    # File handler (opcional)
    if log_to_file:
        file_handler = TimedRotatingFileHandler(
            Path(log_dir) / log_filename,
            when='midnight',        # Rota a medianoche
            interval=1,             # Cada 1 día
            backupCount=30,         # Mantiene 30 días de histórico
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)  # Archivo guarda todo
        file_handler.setFormatter(logging.Formatter(file_log_format, date_format))
        handlers.append(file_handler)
    
    # Configurar root logger
    logging.basicConfig(
        level=logging.DEBUG,  # Captura todo, los handlers filtran
        format=file_log_format,
        datefmt=date_format,
        handlers=handlers,
        force=True  # Sobrescribe configuraciones previas
    )
    
    # Silenciar logs verbosos de librerías externas
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("chardet").setLevel(logging.WARNING)
    logging.getLogger("charset_normalizer").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("groq").setLevel(logging.WARNING)

def get_logger(name: str) -> logging.Logger:
    """
    Factory function para obtener un logger.
    
    Args:
        name: Nombre del logger (usa __name__ del módulo)
    
    Returns:
        Logger configurado
    """
    return logging.getLogger(name)