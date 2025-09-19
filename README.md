# TRADUCTOR ARCHIVOS

Una aplicación completa integrada para extraer, procesar, traducir texto de archivos y reconstruir los contenidos traducidos en una sola interfaz gráfica intuitiva. Utiliza MongoDB para almacenamiento persistente y IA local con Ollama para traducciones eficientes. Perfecta para traducción masiva de textos literarios entre múltiples idiomas, manteniendo la estructura original del contenido.

## 🚀 Características Principales

### Aplicación Unificada - `traductor_documentos.py`
- **Interfaz Completa (GUI Unificada)**: Una sola aplicación con tres pestañas para extracción, traducción y composición
- **Extracción Inteligente de Texto**: Segmenta archivos de texto (.txt) y PDF en frases preservando la estructura original
- **Almacenamiento en MongoDB**: Persistencia de datos segmentados en colecciones estructuradas de MongoDB
- **Traducción con IA Avanzada**: Traducción automática entre español, inglés y francés usando modelos Ollama locales (gemma3:4b)
- **Reconstrucción Profesionaassl**: Composición automática de archivos traducidos en formato .txt y PDF con formato tipográfico
- **Procesamiento Masivo**: Soporte para múltiples archivos, colecciones y traducciones simultáneas
- **Progreso Visual Completo**: Barras de progreso individuales por pestaña y registro de actividad global
- **Procesamiento Asíncrono**: Arquitectura con hilos para mantener la interfaz responsiva durante operaciones
- **Tema Oscuro Moderno**: Interfaz gráfica profesional con paleta oscura consistente
- **Manejo de Errores Robusto**: Sistema de recuperación que continúa procesamiento ante fallos individuales
- **Cancelación de Operaciones**: Control total sobre procesos en ejecución con botones de cancelación
- **Validación Inteligente**: Verificación de conexiones, archivos compatibles y estados de MongoDB

## 📁 Estructura del Proyecto

### Archivo Principal
```
TRADUCTOR_ARCHIVOS/
├── traductor_documentos.py                  # ✅ APLICACIÓN COMPLETA UNIFICADA (PySide6)
```

### Scripts de Desarrollo y Debugging
```
TRADUCTOR_ARCHIVOS/
├── debugeo/
│   ├── 1-extraer_texto_a mongodb_con_gui.py   # Desarrollo: Extracción con GUI
│   ├── 1-extraer_texto_a mongodb.py           # Desarrollo: Extracción CLI
│   ├── 2-traducir_desde_mongodb_con_gui.py    # Desarrollo: Traducción con GUI
│   ├── 2-traducir_desde_mongodb.py            # Desarrollo: Traducción CLI
│   └── 3-componer.py                         # Desarrollo: Composición GUI
```

### Archivos de Ejemplo y Resultados
```
TRADUCTOR_ARCHIVOS/
├── el_quijote.txt                           # 📖 Archivo de ejemplo (Don Quijote completo)
├── el_quijote_traducido_al_ingles.txt        # ✅ Archivo generado (traducción completa)
├── Caperucita Roja/
│   ├── caperucita_roja_traducido_a_en.pdf    # ✅ Archivo generado (PDF traducción)
│   └── caperucita_roja_traducido_a_en.txt    # ✅ Archivo generado (TXT traducción)
├── El_Quijote/
│   ├── el_quijote_traducido_al_ingles.pdf    # ✅ Archivo generado (PDF organizado)
│   └── el_quijote_traducido_al_ingles.txt    # ✅ Archivo generado (TXT organizado)
```

### Documentación y Configuración
```
TRADUCTOR_ARCHIVOS/
├── manual_traductor_texto.html              # 📚 Manual detallado en HTML
├── .gitignore                              # ⚙️ Archivos ignorados por Git
└── README.md                               # 📋 Este archivo
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
```bash
# Para versiones GUI con interfaz gráfica
pip install pymongo requests PySide6 PyPDF2 reportlab
```

### Dependencias específicas:
- **General GUI**: pymongo, requests, PySide6
- **Extracción GUI**: PyPDF2 (soporte para archivos .txt y .pdf)
- **Composición GUI**: reportlab (generación de archivos .pdf)

### Instalación de Dependencias
```bash
# Instalar dependencias para versión CLI
pip install pymongo requests

# Instalar dependencias para versión GUI completa
pip install pymongo requests PySide6 PyPDF2 reportlab
```

### Instalación Detallada por Componente
```bash
# Base para todas las operaciones
pip install pymongo requests

# Para interfaces gráficas (todos los scripts *con_gui.py)
pip install PySide6

# Para soporte de PDF en extracción (1-extraer_texto_a mongodb_con_gui.py)
pip install PyPDF2

# Para generación de PDF en composición (3-componer.py)
pip install reportlab
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

### 🏆 Aplicación Unificada Recomendada - `traductor_documentos.py`

Esta es la opción más recomendable por su interfaz completa y facilidad de uso:

```bash
# Ejecutar la aplicación completa integrada
python traductor_documentos.py
```

**Características de la aplicación unificada:**
- **Tres pestañas integradas**: Una interfaz completa para todo el proceso
- **Flujo de trabajo secuencial**: Desde extracción hasta composición final
- **Progreso global**: Barra de progreso y log unificado
- **Selección de idiomas**: Soporte completo para español, inglés y francés
- **Tema oscuro profesional**: Interfaz moderna y consistente
- **Procesamiento asíncrono**: Mantén la interfaz responsiva durante operaciones

**Flujo de uso típico:**
1. **Pestaña 1 - Extraer**: Seleccionar archivo .txt o .pdf para procesar

   ![Extraer Texto](imagenes/1-Extraer%20Texto.png)

2. **Pestaña 2 - Traducir**: Elegir idiomas y colecciones a traducir

   ![Traducir](imagenes/2-Traducir.png)

3. **Pestaña 3 - Componer**: Generar archivos finales .txt y .pdf

   ![Componer](imagenes/3-Componer.png)

### Orden de Ejecución Recomendado (Scripts Individuales)
Para usuarios que prefieren scripts separados o necesitan personalización avanzada:

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
- **Selección de archivos**: Diálogo nativo del sistema operativo para .txt y .pdf
- **Soporte múltiple**: Extrae texto de archivos de texto (.txt) y PDF (.pdf)
- **Barra de progreso**: Visualización del procesamiento en tiempo real
- **Cancelación**: Botón para detener el proceso
- **Tema oscuro**: Interfaz profesional y moderna
- **Validación**: Verificación de archivos compatibles antes del procesamiento

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
# Interfaz gráfica
python 3-componer.py

# Modo de prueba/consola (para depuración)
python 3-componer.py --test
```

Características avanzadas:
- **Detección automática**: Lista colecciones con '_traducido_' en MongoDB
- **Selección múltiple**: Checkbox para elegir qué colecciones procesar
- **Generación de archivos**: Crea automáticamente archivos .txt y opcionalmente .pdf
- **Progreso visual**: Barra de progreso por colección procesada
- **Log detallado**: Registro de actividad y confirmación de archivos creados
- **Tema oscuro**: Interfaz profesional y moderna
- **Modo de prueba**: Verificación de conexiones y diagnóstico vía consola

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
- **Colección por defecto**: Derivada del nombre del archivo
- **Modelos Ollama**: `gemma3:4b` (recomendado)
- **Idiomas soportados**: Español (es), Inglés (en), Francés (fr)
- **Dirección traducción**: Configurable entre cualquier par de idiomas

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

## 📈 Estado Actual del Proyecto

### ✅ Progreso Completado
- **🎯 Archivo Principal Unificado**: `traductor_documentos.py` integra todas las funcionalidades en una sola aplicación GUI con tres pestañas
- **🔧 Scripts de Desarrollo**: Los archivos en la carpeta `debugeo/` representan el desarrollo modular original que ha sido consolidado
- **📚 Archivos de Ejemplo**: Contenido literario procesado y traducido (Don Quijote, Caperucita Roja) disponible para pruebas
- **🎨 Interfaz Completa**: Tema oscuro profesional aplicado consistentemente en toda la aplicación
- **🌐 Soporte Multiidioma**: Traducción completa entre español, inglés y francés
- **📄 Formatos Avanzados**: Generación automática de archivos .txt y .pdf con formato tipográfico profesional

### 🚧 Arquitectura Evolutiva
El proyecto evolucionó desde scripts separados (`debugeo/*.py`) hacia una **aplicación unificada** que mantiene todas las funcionalidades pero con una interfaz integrada más intuitiva y eficiente.

### 🔄 Compatibilidad
Los scripts en `debugeo/` siguen siendo funcionales y útiles para:
- Desarrollo y debugging específicos
- Personalización avanzada
- Interfaces de línea de comandos
- Integración con otros sistemas

## 🛠️ Personalización

### Configuración de la Aplicación Unificada
```python
# traductor_documentos.py - Constantes principales
DATABASE_NAME = "traducciones"
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "gemma3:4b"  # Cambiar por modelo Ollama disponible

IDIOMA_CODES = ["es", "en", "fr"]  # Idiomas soportados
IDIOMA_NAMES = {
    "es": "Español",
    "en": "English",
    "fr": "Français"
}
```

### Opciones de Modelo Ollama
```python
# Modelos recomendados para traducción
MODEL_NAME = "gemma3:4b"        # Recomendado: Mejor rendimiento
MODEL_NAME = "mistral"          # Alternativo: Más rápido
MODEL_NAME = "llama3.2:3b"      # Ligero: Menos recursos
```

### Idiomas Disponibles
```python
# Todas las combinaciones posibles
IDIOMA_CODES = ["es", "en", "fr"]
# Ejemplos de direcciones:
# "es" → "en": Español → Inglés
# "en" → "fr": Inglés → Francés
# "fr" → "es": Francés → Español
```

### Configuración Avanzada de MongoDB
```python
# URL personalizada para MongoDB
mongo_url = "mongodb://user:pass@host:port/"

# Base de datos alternativa
DATABASE_NAME = "mis_traducciones"
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
pip install --upgrade pymongo requests PySide6 PyPDF2 reportlab
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
