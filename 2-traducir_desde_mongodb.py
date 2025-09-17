"""
Este script traduce texto almacenado en una colección de MongoDB utilizando el servicio Ollama.

Lee documentos de una colección origen, traduce cada línea del español al inglés
mediante llamadas a la API de Ollama, y almacena las traducciones en una nueva colección.

El script maneja errores durante la traducción y salta líneas vacías o irrelevantes
para optimizar el proceso.

Uso:
    python 2-traducir_desde_mongodb.py

Dependencias:
    - requests: Para realizar peticiones HTTP a la API de Ollama
    - pymongo: Para la conexión y operaciones con MongoDB
    - Ollama: Debe estar ejecutándose localmente en https://localhost:11434
    - Modelo Ollama: 'gemma3:4b' (o similar, ajustar en el código si es necesario)

Configuración de MongoDB:
    - URL: mongodb://localhost:27017/
    - Base de datos: traducciones
    - Colección origen: el_quijote (ajustable en COLECCION_NAME)
    - Colección destino: [COLECCION_NAME]_traducido_al_ingles

Estructura de documentos:
    - Origen: {"_id": int, "linea": str}
    - Destino: {"_id": int, "linea": str} (con traducción o contenido original si no traducible)
"""

import requests
import json  # Ya no es necesario aquí, pero se mantiene por si acaso
from pymongo import MongoClient

# Constantes para idiomas
IDIOMA_EN = "en"
IDIOMA_ES = "es"

# Direcciones de traducción
DIRECCION_EN_ES = (IDIOMA_EN, IDIOMA_ES)
DIRECCION_ES_EN = (IDIOMA_ES, IDIOMA_EN)

# Constantes para MongoDB
DATABASE_NAME = "traducciones"
COLECCION_NAME = "el_quijote"  # Puedes cambiar esto por el nombre de tu colección

def traducir_con_ollama(texto: str, idioma_origen: str, idioma_destino: str) -> str:
    """
    Traduce un texto usando Ollama.
    :param texto: Texto de entrada a traducir
    :param idioma_origen: Idioma de origen (ej: 'en' para inglés, 'es' para español)
    :param idioma_destino: Idioma de destino (ej: 'es' para español, 'en' para inglés)
    :return: Traducción como cadena
    """
    url = "http://localhost:11434/api/generate"

    # Crear prompt dinámico basado en los idiomas
    if idioma_origen == IDIOMA_ES and idioma_destino == IDIOMA_EN:
        prompt = f"Translate the following text from Spanish to English. Provide only the English translation, without explanations or additional modifications:\n\n{texto}"
    elif idioma_origen == IDIOMA_EN and idioma_destino == IDIOMA_ES:
        prompt = f"Traduce el siguiente texto del inglés al español. Proporciona únicamente la traducción al español, sin explicaciones ni modificaciones adicionales:\n\n{texto}"
    else:
        raise ValueError(f"Dirección de traducción no soportada: {idioma_origen} -> {idioma_destino}")

    payload = {
        "model": "gemma3:4b",   # Cambia por el modelo que tengas disponible (ej: "mistral")
        "prompt": prompt,
        "stream": False      # False para obtener la salida completa de una vez
    }

    response = requests.post(url, json=payload)

    if response.status_code == 200:
        data = response.json()
        return data.get("response", "").strip()
    else:
        raise Exception(f"Error en la petición: {response.status_code}, {response.text}")


# Ejemplo de uso con MongoDB
if __name__ == "__main__":
    # Conectar a MongoDB
    client = MongoClient("mongodb://localhost:27017/")  # Cambia la URL si es necesario
    db = client[DATABASE_NAME]
    collection_origen = db[COLECCION_NAME]
    collection_traducida = db[f"{COLECCION_NAME}_traducido_al_ingles"]

    # Leer documentos de la colección original
    documentos = collection_origen.find()  # Puedes agregar filtros si es necesario

    for documento in documentos:
        linea_numero = documento["_id"]
        linea_texto = documento["linea"]

        # Saltar líneas vacías o que solo contienen saltos de línea para evitar traducciones innecesarias
        if not linea_texto.strip() or linea_texto.strip() == "\n":
            print(f"Línea {linea_numero}: {repr(linea_texto)} (saltada, no traducible)")
            # Guardar el contenido original en la nueva colección
            collection_traducida.insert_one({"_id": linea_numero, "linea": linea_texto})
            print(f"Contenido original guardado para la línea {linea_numero}")
            continue

        # Traducir la línea del español al inglés
        try:
            traduccion = traducir_con_ollama(linea_texto, *DIRECCION_ES_EN)
            print(f"Línea {linea_numero}: {linea_texto}")
            print(f"Traducción: {traduccion}")
            print("---")

            # Guardar la traducción en la nueva colección
            collection_traducida.insert_one({"_id": linea_numero, "linea": traduccion})
            print(f"Traducción guardada para la línea {linea_numero}")
        except Exception as e:
            print(f"Error al traducir o guardar la línea {linea_numero}: {e}")
