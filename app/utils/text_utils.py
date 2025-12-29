"""
Utilidades para normalización y procesamiento de texto.
"""
import unicodedata


def normalizar_texto(texto: str) -> str:
    """
    Normaliza el texto corrigiendo codificación y eliminando tildes.
    Mantiene la ñ y otros caracteres especiales del español.
    
    Args:
        texto: Texto a normalizar
        
    Returns:
        Texto normalizado sin tildes
    """
    if not texto:
        return texto
    
    texto = unicodedata.normalize('NFC', texto)
    texto_sin_tildes = ''.join(
        char for char in unicodedata.normalize('NFD', texto)
        if unicodedata.category(char) != 'Mn'
    )
    return texto_sin_tildes
