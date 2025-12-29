"""
Parser de fechas para noticias.
Soporta múltiples formatos: ISO, texto en español, URLs.
"""
import re
import json
from datetime import datetime
from bs4 import BeautifulSoup


class DateParser:
    """
    Clase para parsear fechas de publicación de noticias.
    Soporta múltiples fuentes y formatos.
    """
    
    # Meses en español
    MESES_ES = {
        'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
        'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
        'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
    }
    
    # Formatos ISO comunes
    FORMATOS_ISO = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y",
        "%d-%m-%Y",
    ]
    
    # Meta tags donde buscar fechas
    META_TAGS_FECHA = [
        ('meta', {'property': 'article:published_time'}),
        ('meta', {'property': 'og:published_time'}),
        ('meta', {'name': 'date'}),
        ('meta', {'name': 'pubdate'}),
        ('meta', {'name': 'DC.date.issued'}),
        ('meta', {'name': 'article:published'}),
    ]
    
    # Clases CSS que suelen contener fechas
    CLASES_FECHA = [
        'itemDateCreated', 'itemDateModified',
        'entry-date', 'post-date', 'td-post-date',
        'jeg_meta_date',
        'date', 'fecha', 'published',
        'article-date', 'news-date', 'nota-fecha',
    ]
    
    # Patrones para extraer fechas de URLs
    PATRONES_URL = [
        r'/(\d{4})/(\d{2})/(\d{2})/',      # /2024/12/28/
        r'/(\d{4})-(\d{2})-(\d{2})[-/]',   # /2024-12-28-
        r'-(\d{4})(\d{2})(\d{2})-',        # -20241228-
        r'/(\d{4})(\d{2})(\d{2})\d*\.html', # 20241228.html
    ]
    
    @classmethod
    def parsear_fecha_texto(cls, texto: str) -> datetime | None:
        """
        Parsea una fecha desde texto en español.
        
        Soporta formatos como:
        - "28 de diciembre de 2025"
        - "28 diciembre - 2025"
        - "domingo 28 de diciembre, 2025"
        - "29 diciembre, 2025"
        - "Martes, 28 Octubre 2025 07:53"
        
        Args:
            texto: Texto con la fecha
            
        Returns:
            datetime o None si no se pudo parsear
        """
        if not texto:
            return None
        
        texto = texto.lower().strip()
        
        # Limpiar texto
        texto = re.sub(
            r'^(lunes|martes|miercoles|miércoles|jueves|viernes|sabado|sábado|domingo)[,\s]+', 
            '', texto
        )
        texto = texto.replace(' de ', ' ').replace(' - ', ' ').replace(',', ' ')
        texto = re.sub(r'\s+', ' ', texto).strip()
        
        # Patrón: "28 diciembre 2025" o "28 diciembre 2025 11:43"
        patron = r'(\d{1,2})\s+(\w+)\s+(\d{4})(?:\s+(\d{1,2}):(\d{2}))?'
        match = re.search(patron, texto)
        
        if match:
            dia = int(match.group(1))
            mes_texto = match.group(2)
            año = int(match.group(3))
            hora = int(match.group(4)) if match.group(4) else 0
            minuto = int(match.group(5)) if match.group(5) else 0
            
            mes = cls.MESES_ES.get(mes_texto)
            if mes and 1 <= dia <= 31 and 2020 <= año <= 2030:
                try:
                    return datetime(año, mes, dia, hora, minuto)
                except ValueError:
                    pass
        
        return None
    
    @classmethod
    def parsear_fecha_iso(cls, fecha_str: str) -> datetime | None:
        """
        Parsea fechas en formato ISO y variantes.
        
        Args:
            fecha_str: String con fecha en formato ISO
            
        Returns:
            datetime o None si no se pudo parsear
        """
        if not fecha_str:
            return None
        
        # Limpiar el string
        fecha_str = fecha_str.strip()
        
        # Remover timezone info para simplificar
        fecha_str = re.sub(r'[+-]\d{2}:\d{2}$', '', fecha_str)
        fecha_str = fecha_str.replace('Z', '').replace('.000', '')
        
        for fmt in cls.FORMATOS_ISO:
            try:
                return datetime.strptime(fecha_str, fmt)
            except ValueError:
                continue
        
        return None
    
    @classmethod
    def extraer_de_json_ld(cls, soup: BeautifulSoup) -> datetime | None:
        """Extrae fecha desde JSON-LD (Schema.org)."""
        try:
            json_ld = soup.find('script', type='application/ld+json')
            if json_ld and json_ld.string:
                data = json.loads(json_ld.string)
                if isinstance(data, list):
                    data = data[0] if data else {}
                
                date_str = (
                    data.get('datePublished') or 
                    data.get('dateCreated') or 
                    data.get('dateModified')
                )
                if date_str:
                    return cls.parsear_fecha_iso(date_str)
        except (json.JSONDecodeError, TypeError, KeyError):
            pass
        return None
    
    @classmethod
    def extraer_de_meta_tags(cls, soup: BeautifulSoup) -> datetime | None:
        """Extrae fecha desde meta tags HTML."""
        for tag, attrs in cls.META_TAGS_FECHA:
            meta = soup.find(tag, attrs=attrs)
            if meta and meta.get('content'):
                fecha = cls.parsear_fecha_iso(meta['content'])
                if fecha:
                    return fecha
        return None
    
    @classmethod
    def extraer_de_time_tag(cls, soup: BeautifulSoup) -> datetime | None:
        """Extrae fecha desde tag <time datetime="">."""
        time_tag = soup.find('time', attrs={'datetime': True})
        if time_tag:
            return cls.parsear_fecha_iso(time_tag['datetime'])
        return None
    
    @classmethod
    def extraer_de_clases_css(cls, soup: BeautifulSoup) -> datetime | None:
        """Extrae fecha desde elementos con clases específicas."""
        for clase in cls.CLASES_FECHA:
            elementos = soup.find_all(class_=lambda x: x and clase in x.lower())
            for elem in elementos:
                texto = elem.get_text(strip=True)
                if texto and len(texto) < 100:
                    fecha = cls.parsear_fecha_texto(texto)
                    if fecha:
                        return fecha
        return None
    
    @classmethod
    def extraer_de_url(cls, url: str) -> datetime | None:
        """Extrae fecha desde la URL de la noticia."""
        for patron in cls.PATRONES_URL:
            match = re.search(patron, url)
            if match:
                try:
                    año = int(match.group(1))
                    mes = int(match.group(2))
                    dia = int(match.group(3))
                    if 2020 <= año <= 2030 and 1 <= mes <= 12 and 1 <= dia <= 31:
                        return datetime(año, mes, dia)
                except (ValueError, IndexError):
                    continue
        return None
    
    @classmethod
    def extraer(cls, soup: BeautifulSoup, url: str) -> datetime | None:
        """
        Extrae la fecha de publicación usando múltiples métodos.
        
        Orden de prioridad:
        1. JSON-LD (más confiable)
        2. Meta tags article:published_time
        3. Tag <time datetime="">
        4. Elementos con clases de fecha
        5. Fecha en la URL
        
        Args:
            soup: BeautifulSoup del HTML
            url: URL de la noticia
            
        Returns:
            datetime o None si no se encontró fecha
        """
        # Intentar cada método en orden de prioridad
        extractores = [
            cls.extraer_de_json_ld,
            cls.extraer_de_meta_tags,
            cls.extraer_de_time_tag,
            cls.extraer_de_clases_css,
        ]
        
        for extractor in extractores:
            fecha = extractor(soup)
            if fecha:
                return fecha
        
        # Último recurso: extraer de URL
        return cls.extraer_de_url(url)
