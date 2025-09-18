# TRADUCTOR ARCHIVOS

Una aplicación completa para extraer, procesar, traducir texto de archivos y reconstruir los contenidos traducidos. Utiliza MongoDB para almacenamiento persistente y IA local con Ollama para traducciones eficientes. Ideal para traducción masiva de textos literarios del español al inglés, manteniendo la estructura original del contenido.

## 🚀 Características Principales

- **Extracción Inteligente de Texto**: Segmenta archivos de texto en frases respetando puntos y saltos de línea
- **Almacenamiento en MongoDB**: Persistencia de datos segmentados en colecciones de MongoDB
- **Traducción con IA**: Traducción automática español-inglés usando modelos Ollama locales
- **Dos Interfaces**: Versiones CLI (línea de comandos) y GUI (interfaz gráfica)
- **Reconstrucción de Texto**: Composición automática de archivos traducidos desde MongoDB
- **Exportación Múltiple**: Soporte para archivos de texto (.txt) y PDF
- **Procesamiento Masivo**: Soporte para múltiples archivos y colecciones
- **Progreso Visual**: Barras de progreso y registro de actividad detallado
- **Manejo de Errores Robusto**: Continúa procesamiento ante fallos individuales
- **Tema Oscuro**: Interfaz gráfica moderna y profesional

## 📁 Estructura del Proyecto

```
TRADUCTOR_ARCHIVOS/
├── 1-extraer_texto_a mongodb.py              # CLI: Extracción de texto
├── 1-extraer_texto_a mongodb_con_gui.py      # GUI: Extracción con interfaz gráfica
├── 2-traducir_desde_mongodb.py               # CLI: Traducción automática
├── 2-traducir_desde_mongodb_con_gui.py       # GUI: Traducción masiva con GUI
├── 3-componer.py                            # GUI: Composición de texto traducido
├── el_quijote.txt                           # Archivo de ejemplo (Don Quijote)
├── el_quijote_traducido_al_ingles.txt        # Archivo generado (Don Quijote traducido)
├── el_quijote_traducido_al_ingles.pdf        # Archivo generado (Don Quijote traducido en PDF)
├── manual_traductor_texto.html              # Manual detallado en HTML
├── .gitignore                              # Archivos ignorados por Git
└── README.md                               # Este archivo
```

## 🔧 Requisitos del Sistema

### Dependencias Generales
- **Python 3.x**
- **MongoDB** corriendo localmente en `mongodb://localhost:27017/`
- **Ollama** ejecutándose en `http://localhost:11434` con modelo `gemma3:4b`

### Dependencias Python (CLI)
```
pymongo>=4.0
requests>=2.25
```

### Dependencias Python (GUI)
```
pymongo>=4.0
requests>=2.25
PySide6>=6.0
reportlab>=4.0
```

### Instalación de Dependencias
```bash
# Instalar dependencias para versión CLI
pip install pymongo requests

# Instalar dependencias para versión GUI
pip install pymongo requests PySide6 reportlab
```

## 📋 Configuración Inicial

### 1. Instalar MongoDB
```bash
# Ubuntu/Debian
sudo apt-get install mongodb

# macOS con Homebrew
brew install mongodb-community

# Windows: Descargar e instalar desde https://www.mongodb.com/
```

### 2. Instalar Ollama
```bash
# Descargar desde https://ollama.com/
# Instalar el modelo requerido
ollama pull gemma3:4b
```

### 3. Verificar Servicios
```bash
# Verificar MongoDB
mongosh --eval "db.adminCommand('ping')"

# Verificar Ollama
curl http://localhost:11434/api/tags
```

## 🚀 Uso del Proyecto

### Orden de Ejecución Recomendado
1. **Primero**: Ejecutar script de extracción para procesar archivos
2. **Segundo**: Ejecutar script de traducción para traducir el contenido
3. **Tercero**: Ejecutar script de composición para reconstruir archivos traducidos

### Versión CLI

#### Extracción de Texto
```bash
python 1-extraer_texto_a mongodb.py
```
- Procesa automáticamente `el_quijote.txt`
- Crea colección `el_quijote` en base de datos `traducciones`

#### Traducción Automática
```bash
python 2-traducir_desde_mongodb.py
```
- Lee de colección `el_quijote`
- Crea colección `el_quijote_traducido_al_ingles`
- Manejo individual de errores por línea

### Versión GUI

#### Extracción con Interfaz Gráfica
```bash
python 1-extraer_texto_a mongodb_con_gui.py
```

Características:
- **Selección de archivos**: Diálogo nativo del sistema operativo
- **Barra de progreso**: Visualización del procesamiento en tiempo real
- **Cancelación**: Botón para detener el proceso
- **Tema oscuro**: Interfaz profesional y moderna

#### Traducción Masiva con GUI
```bash
python 2-traducir_desde_mongodb_con_gui.py
```

Características avanzadas:
- **Detección automática**: Lista todas las colecciones disponibles
- **Selección múltiple**: Checkbox para elegir qué traducir
- **Progreso global**: Barra de progreso por colección individual
- **Log coloreado**: Registro de actividad con colores diferenciados
- **Procesamiento en paralelo**: Mantenimiento de interfaz responsiva
- **Selección rápida**: Botones "Seleccionar Todo" y "Limpiar Selección"

#### Composición de Texto Traducido
```bash
python 3-componer.py
```

Características avanzadas:
- **Detección automática**: Lista colecciones con '_traducido_' en MongoDB
- **Selección múltiple**: Checkbox para elegir qué colecciones procesar
- **Generación de archivos**: Crea automáticamente archivos .txt y opcionalmente .pdf
- **Progreso visual**: Barra de progreso por colección procesada
- **Log detallado**: Registro de actividad y confirmación de archivos creados
- **Tema oscuro**: Interfaz profesional y moderna

## 🗂️ Estructuras de Datos

### MongoDB - Base de Datos: `traducciones`

#### Colección Original (Extraída)
```javascript
{
  "_id": 1,
  "linea": "En un lugar de la Mancha..."
}
```

#### Colección Traducida
```javascript
{
  "_id": 1,
  "linea": "In a place of La Mancha..."
}
```

### Configuración por Defecto
- **Base de datos**: `traducciones`
- **Colección por defecto**: `el_quijote`
- **Modelo Ollama**: `gemma3:4b`
- **Dirección traducción**: Español → Inglés

## 🔍 Funcionamiento Detallado

### Algoritmo de Segmentación
El sistema divide textos en frases considerando:
- **Puntos (.)**: Fin de frase completa
- **Saltos de línea (\n)**: Segmentos independientes
- **Preservación de formato**: Mantiene estructura original

### Manejo de Traducción
- **Procesamiento línea por línea**: Cada frase se traduce individualmente
- **Omisión inteligente**: Líneas vacías se copian sin traducir
- **Gestión de errores**: Fallos en traducción no detienen el proceso
- **Prompt optimizado**: Instrucciones específicas para calidad de traducción

### Arquitectura de GUI
- **Hilos separados**: Procesamiento en background mantiene UI responsiva
- **Señales Qt**: Comunicación segura entre hilos y interfaz
- **Tema consistente**: Paleta oscura aplicada globalmente

## 🛠️ Personalización

### Cambiar Modelo Ollama
```python
# En los scripts de traducción
payload = {
    "model": "mistral",  # Cambiar por modelo disponible
    "prompt": prompt,
    "stream": False
}
```

### Modificar Idiomas
```python
# Direcciones disponibles
DIRECCION_EN_ES = ("en", "es")  # Inglés → Español
DIRECCION_ES_EN = ("es", "en")  # Español → Inglés
```

### Configurar MongoDB
```python
# URL personalizada
client = MongoClient("mongodb://user:pass@host:port/")
```

## 🐛 Solución de Problemas

### Problemas Comunes

#### MongoDB no conecta
```bash
# Verificar estado
sudo systemctl status mongodb

# Reiniciar servicio
sudo systemctl restart mongodb
```

#### Ollama no responde
```bash
# Verificar modelos
ollama list

# Iniciar servidor
ollama serve
```

#### Dependencias faltantes
```bash
pip install --upgrade pymongo requests PySide6 reportlab
```

#### Errores de codificación
- Asegurar archivos estén en **UTF-8**
- Verificar ruta completa de archivos

### Mensajes de Error Frecuentes

- **Connection refused**: Verificar MongoDB/Ollama ejecutándose
- **Module not found**: Instalar dependencias faltantes
- **File not found**: Usar rutas absolutas o verificar existencia
- **Empty translations**: Normal para líneas con solo saltos de línea

### Logs y Depuración
Los scripts GUI muestran en detalle:
- ✅ Operaciones exitosas (verde)
- ⚠️ Líneas saltadas (naranja)
- ❌ Errores (rojo)
- 🔄 Progreso (azul/púrpura)

## 📚 Documentación Adicional

- **`manual_traductor_texto.html`**: Manual completo con ejemplos detallados
- **Archivos fuente**: Código bien documentado con docstrings
- **Comentarios inline**: Explicaciones detalladas en funciones críticas

## 🤝 Contribución

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/NuevaCaracteristica`)
3. Commit tus cambios (`git commit -am 'Agrega nueva característica'`)
4. Push a la rama (`git push origin feature/NuevaCaracteristica`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo LICENSE para detalles.

## 👨‍💻 Autor

**bgonpin** - [bgonpin.github.io](https://bgonpin.github.io/)

## 🙏 Agradecimientos

- **Ollama**: Por proporcionar modelos de IA accesibles localmente
- **MongoDB**: Por la base de datos NoSQL robusta
- **PySide6**: Por el framework de interfaz gráfica moderna
- **Don Quijote**: Archivo de ejemplo icónico de la literatura española

---

*Proyecto desarrollado para facilitar la traducción automática de textos literarios utilizando tecnologías modernas de IA y bases de datos.*
