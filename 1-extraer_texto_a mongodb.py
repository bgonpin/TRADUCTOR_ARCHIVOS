"""
Este script extrae texto de un archivo, lo segmenta en frases separadas por puntos,
y almacena cada frase en una colección de MongoDB.

El script lee un archivo de texto (por defecto 'el_quijote.txt'),
segmenta el contenido respetando los saltos de línea y los puntos finales,
y luego conecta a una base de datos MongoDB local para almacenar cada segmento
como un documento separado en una colección nombrada según el archivo.

Uso:
    python 1-extraer_texto_a mongodb.py

Dependencias:
    - pymongo: Para la conexión y operaciones con MongoDB
    - El archivo de texto especificado debe existir en el mismo directorio

Colección MongoDB:
    - Base de datos: traducciones
    - Colección: [nombre_del_archivo_sin_extensión]
    - Documentos: {"_id": int, "linea": str}
"""

import pymongo
import os

def segmentar_frases(ruta_archivo: str):
    """
    Lee un archivo de texto y lo segmenta en frases por '.'.
    Respeta los saltos de línea (\n) como segmentos aparte.
    """
    frases = []

    with open(ruta_archivo, "r", encoding="utf-8") as f:
        contenido = f.read()

    frase_actual = ""
    for caracter in contenido:
        frase_actual += caracter
        if caracter == ".":  # fin de frase
            frases.append(frase_actual.strip("\n"))
            frase_actual = ""
        elif caracter == "\n":  # salto de línea
            if frase_actual.strip("\n"):
                frases.append(frase_actual.strip("\n"))
            frases.append("\n")  # se guarda salto explícitamente
            frase_actual = ""

    # Si queda texto sin punto al final
    if frase_actual.strip():
        frases.append(frase_actual)

    return frases


# Ejemplo de uso
if __name__ == "__main__":
    ruta = "el_quijote.txt"
    resultado = segmentar_frases(ruta)

    # Conectar a MongoDB
    client = pymongo.MongoClient()
    db = client.traducciones
    base = os.path.basename(ruta)
    coleccion_nombre = os.path.splitext(base)[0]
    coleccion = db[coleccion_nombre]

    # Limpiar la colección antes de insertar (opcional, para evitar duplicados)
    coleccion.delete_many({})

    for i, frase in enumerate(resultado, 1):
        coleccion.insert_one({"_id": i, "linea": frase})
        print(f"{i}: {frase}")  # Opcional, para ver en consola
