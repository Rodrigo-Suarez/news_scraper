"""
Cliente HTTP asíncrono para scraping.
"""
import asyncio
import aiohttp
from config.settings import get_scraping_config
from config.logging_config import get_logger

logger = get_logger(__name__)

class AsyncHTTPClient:
    """
    Cliente HTTP asíncrono con soporte para encoding automático.
    Maneja timeouts, headers y detección de encoding.
    """
    
    def __init__(self):
        """Inicializa el cliente con la configuración."""
        self.config = get_scraping_config()
        # Headers que simulan un navegador real
        self.headers = {
            'User-Agent': self.config['user_agent'],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',  # Sin Brotli para evitar errores
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate', 
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }
    
    def crear_session(self, max_connections: int) -> aiohttp.ClientSession:
        """
        Crea una sesión HTTP con límites de conexión.
        
        Args:
            max_connections: Número máximo de conexiones concurrentes
            
        Returns:
            ClientSession configurada
        """
        connector = aiohttp.TCPConnector(
            limit=max_connections,
            limit_per_host=self.config['limit_per_host'],
            force_close=True,  # Forzar cierre de conexiones (evita problemas entre ejecuciones)
        )
        return aiohttp.ClientSession(
            connector=connector,
            headers=self.headers
        )
    
    async def fetch_html(self, session: aiohttp.ClientSession, url: str) -> str | None:
        """
        Obtiene el HTML de una URL de forma asíncrona.
        
        Detecta automáticamente el encoding usando chardet.
        
        Args:
            session: Sesión HTTP activa
            url: URL a obtener
            
        Returns:
            HTML como string o None si falla
        """
        try:
            timeout = aiohttp.ClientTimeout(total=self.config['request_timeout'])
            
            async with session.get(url, timeout=timeout) as response:
                if response.status >= 400:
                    logger.warning(f"⚠️ HTTP {response.status} para {url[:50]}...")
                    return None
                    
                # Leer contenido raw (bytes)
                content = await response.read()
                
                # Detectar encoding usando chardet
                detected_encoding = self._detectar_encoding(content)
                
                # Decodificar con el encoding detectado
                if detected_encoding:
                    try:
                        return content.decode(detected_encoding)
                    except (UnicodeDecodeError, LookupError):
                        pass
                
                # Fallback: usar la detección de aiohttp o UTF-8
                return content.decode(
                    response.get_encoding() or 'utf-8', 
                    errors='replace'
                )
                
        except asyncio.TimeoutError:
            logger.warning(f"⏱️ Timeout para {url[:50]}...")
            return None
        except aiohttp.ClientError as e:
            # Mostrar más detalles del error
            error_msg = str(e) if str(e) else type(e).__name__
            logger.error(f"❌ ClientError: {error_msg[:80]}")
            return None
        except Exception as e:
            logger.error(f"❌ Error: {type(e).__name__}: {e}")
            return None
    
    def _detectar_encoding(self, content: bytes) -> str | None:
        """
        Detecta el encoding del contenido usando chardet.
        
        Args:
            content: Contenido en bytes
            
        Returns:
            Encoding detectado o None
        """
        try:
            import chardet
            result = chardet.detect(content)
            if result and result.get('encoding'):
                return result['encoding']
        except ImportError:
            pass
        return None
