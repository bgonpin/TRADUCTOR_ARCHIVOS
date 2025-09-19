"""

Esta aplicación proporciona una interfaz gráfica para traducir colecciones de libros almacenados en MongoDB utilizando el servicio Ollama.

Funcionalidades:
- Lista las colecciones originales disponibles (sin sufijos de traducción)
- Permite seleccionar múltiples colecciones para traducción
- Muestra progreso del proceso
- Permite cancelar el proceso en cualquier momento
- Registra log de actividades
- Soporte para tradución entre Español, Inglés y Francés

Dependencias:
    - PySide6: Para la interfaz gráfica
    - requests: Para realizar peticiones HTTP a la API de Ollama
    - pymongo: Para la conexión y operaciones con MongoDB
    - Ollama: Debe estar ejecutándose localmente en https://localhost:11434
    - Modelo Ollama: 'gemma3:4b' (o similar, ajustar en el código si es necesario)

Configuración de MongoDB:
    - URL: mongodb://localhost:27017/
    - Base de datos: traducciones
"""

import sys
import requests
from pymongo import MongoClient
from PySide6.QtWidgets import (QApplication, QMainWindow, QListWidget, QListWidgetItem,
                               QPushButton, QProgressBar, QTextEdit, QVBoxLayout, QHBoxLayout,
                               QWidget, QSplitter, QMessageBox, QCheckBox, QLabel, QGroupBox, QComboBox)
from PySide6.QtCore import QThread, Signal, QObject, QTimer
from PySide6.QtGui import QFont, QColor, QPalette

# Constantes para idiomas
IDIOMA_EN = "en"
IDIOMA_ES = "es"
IDIOMA_FR = "fr"

# Nombres de idiomas para prompts
IDIOMA_NAMES = {
    IDIOMA_ES: "español",
    IDIOMA_EN: "inglés",
    IDIOMA_FR: "francés"
}

# Constantes para MongoDB
DATABASE_NAME = "traducciones"
COLECCION_NAME = "el_quijote"  # Puedes cambiar esto por el nombre de tu colección

def traducir_con_ollama(texto: str, idioma_origen: str, idioma_destino: str) -> str:
    """
    Traduce un texto usando Ollama.
    :param texto: Texto de entrada a traducir
    :param idioma_origen: Idioma de origen (ej: 'en' para inglés, 'es' para español, 'fr' para francés)
    :param idioma_destino: Idioma de destino (ej: 'es' para español, 'en' para inglés, 'fr' para francés)
    :return: Traducción como cadena
    """
    url = "http://localhost:11434/api/generate"

    # Crear prompt dinámico basado en los idiomas
    nombre_origen = IDIOMA_NAMES[idioma_origen]
    nombre_destino = IDIOMA_NAMES[idioma_destino]

    # Prompts en inglés para el modelo, alternando según necesidad
    if idioma_origen == IDIOMA_ES:
        prompt = f"Translate the following text from Spanish to {nombre_destino}. Provide only the {nombre_destino} translation, without explanations or additional modifications:\n\n{texto}"
    elif idioma_origen == IDIOMA_EN:
        prompt = f"Translate the following text from English to {nombre_destino}. Provide only the {nombre_destino} translation, without explanations or additional modifications:\n\n{texto}"
    elif idioma_origen == IDIOMA_FR:
        prompt = f"Translate the following text from French to {nombre_destino}. Provide only the {nombre_destino} translation, without explanations or additional modifications:\n\n{texto}"
    else:
        raise ValueError(f"Idioma de origen no soportado: {idioma_origen}")

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


class TraductionWorker(QObject):
    """Worker para ejecutar la traducción en un hilo separado"""
    progress = Signal(int)  # Progreso (0-100)
    log_message = Signal(str)  # Mensajes de log
    finished = Signal()  # Finalización
    error = Signal(str)  # Errores

    def __init__(self, collections_to_translate, source_lang, target_lang):
        super().__init__()
        self.collections_to_translate = collections_to_translate
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.cancelled = False
        self.client = MongoClient("mongodb://localhost:27017/")
        self.db = self.client[DATABASE_NAME]

    def cancel(self):
        self.cancelled = True
        self.log_message.emit("Procesamiento cancelado por el usuario")

    def run(self):
        total_collections = len(self.collections_to_translate)
        processed = 0

        for collection_name in self.collections_to_translate:
            if self.cancelled:
                break

            self.log_message.emit(f"Procesando colección: {collection_name}")

            collection_origen = self.db[collection_name]
            collection_traducida = self.db[f"{collection_name}_traducido_a_{self.target_lang}"]

            # Limpiar colección destino si existe
            collection_traducida.drop()
            # _id es indexado automáticamente por MongoDB

            # Obtener total de documentos para progreso parcial
            total_docs = collection_origen.count_documents({})
            if total_docs == 0:
                self.log_message.emit(f"La colección {collection_name} está vacía")
                continue

            processed_docs = 0

            for documento in collection_origen.find():
                if self.cancelled:
                    break

                linea_numero = documento["_id"]
                linea_texto = documento["linea"]

                # Saltar líneas vacías
                if not linea_texto.strip() or linea_texto.strip() == "\n":
                    try:
                        collection_traducida.insert_one({"_id": linea_numero, "linea": linea_texto})
                        self.log_message.emit(f"Línea {linea_numero}: saltada (vacía)")
                    except Exception as e:
                        self.log_message.emit(f"Error guardando línea {linea_numero}: {e}")
                    processed_docs += 1
                    continue

                # Traducir la línea
                try:
                    traduccion = traducir_con_ollama(linea_texto, self.source_lang, self.target_lang)
                    collection_traducida.insert_one({"_id": linea_numero, "linea": traduccion})
                    self.log_message.emit(f"Línea {linea_numero}: '{traduccion}'")
                    processed_docs += 1
                except Exception as e:
                    self.log_message.emit(f"Error traduciendo línea {linea_numero}: {e}")
                    processed_docs += 1

                # Actualizar progreso de esta colección
                collection_progress = int((processed_docs / total_docs) * 100)
                overall_progress = int(((processed + collection_progress / 100) / total_collections) * 100)
                self.progress.emit(overall_progress)

            if not self.cancelled:
                processed += 1
                self.log_message.emit(f"Finalizada colección {collection_name}")

        self.progress.emit(100)
        self.finished.emit()


class TradutorApp(QMainWindow):
    """Ventana principal de la aplicación"""

    def __init__(self):
        super().__init__()
        self.client = None
        self.db = None
        self.worker = None
        self.thread = None
        self.lang_codes = ['es', 'en', 'fr']
        self.lang_labels = ['Español (es)', 'English (en)', 'Français (fr)']
        self.known_suffixes = [f"_traducido_a_{lang}" for lang in self.lang_codes] + ["_traducido_al_ingles"]  # backward compatibility
        self.setup_ui()
        self.setup_database()
        self.load_collections()

    def setup_ui(self):
        self.setWindowTitle("Traductor de Libros - MongoDB")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Panel lateral para selección de colecciones
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Título
        self.title_label = QLabel("Colecciones Disponibles")
        font = QFont()
        font.setBold(True)
        self.title_label.setFont(font)
        left_layout.addWidget(self.title_label)

        # Lista de colecciones
        self.collections_list = QListWidget()
        self.collections_list.setSelectionMode(QListWidget.MultiSelection)
        self.collections_list.setMaximumWidth(250)
        left_layout.addWidget(self.collections_list)

        # Botones
        buttons_layout = QHBoxLayout()

        self.select_all_btn = QPushButton("Seleccionar Todo")
        self.select_all_btn.clicked.connect(self.select_all_collections)
        buttons_layout.addWidget(self.select_all_btn)

        self.clear_selection_btn = QPushButton("Limpiar Selección")
        self.clear_selection_btn.clicked.connect(self.clear_selection)
        buttons_layout.addWidget(self.clear_selection_btn)

        left_layout.addLayout(buttons_layout)

        # Options for translation
        options_group = QGroupBox("Opciones de Traducción")
        options_layout = QVBoxLayout(options_group)

        # Source language
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("Idioma origen:"))
        self.source_combo = QComboBox()
        self.source_combo.addItems(self.lang_labels)
        self.source_combo.setCurrentIndex(0)
        source_layout.addWidget(self.source_combo)
        options_layout.addLayout(source_layout)

        # Target language
        target_layout = QHBoxLayout()
        target_layout.addWidget(QLabel("Idioma destino:"))
        self.target_combo = QComboBox()
        self.target_combo.addItems(self.lang_labels)
        self.target_combo.setCurrentIndex(1)
        target_layout.addWidget(self.target_combo)
        options_layout.addLayout(target_layout)

        left_layout.addWidget(options_group)

        # Panel derecho para controles y progreso
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Controles
        controls_group = QGroupBox("Controles")
        controls_layout = QVBoxLayout(controls_group)

        self.start_btn = QPushButton("Iniciar Traducción")
        self.start_btn.clicked.connect(self.start_translation)
        self.start_btn.setEnabled(False)
        controls_layout.addWidget(self.start_btn)

        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.clicked.connect(self.cancel_translation)
        self.cancel_btn.setEnabled(False)
        controls_layout.addWidget(self.cancel_btn)

        right_layout.addWidget(controls_group)

        # Progreso
        progress_group = QGroupBox("Progreso")
        progress_layout = QVBoxLayout(progress_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)

        right_layout.addWidget(progress_group)

        # Log
        log_group = QGroupBox("Registro de Actividad")
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(300)  # Increased height for larger font
        log_font = QFont("Monospace", 14, QFont.Weight.Bold)
        self.log_text.setFont(log_font)
        log_layout.addWidget(self.log_text)

        right_layout.addWidget(log_group)

        # Splitter principal
        splitter = QSplitter()
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([250, 550])

        main_layout.addWidget(splitter)

    def setup_database(self):
        try:
            self.client = MongoClient("mongodb://localhost:27017/")
            self.db = self.client[DATABASE_NAME]
            self.client.admin.command('ping')
            self.log_message("Conectado a MongoDB")
        except Exception as e:
            QMessageBox.critical(self, "Error de conexión", f"No se pudo conectar a MongoDB: {e}")
            self.close()

    def load_collections(self):
        try:
            collections = self.db.list_collection_names()
            # Filtrar solo las originales (sin sufijos de traducción)
            original_collections = [coll for coll in collections if all(not coll.endswith(suf) for suf in self.known_suffixes)]

            self.collections_list.clear()
            for coll in sorted(original_collections):
                item = QListWidgetItem(coll)
                self.collections_list.addItem(item)

            self.log_message(f"Encontradas {len(original_collections)} colecciones originales")
            if original_collections:
                self.start_btn.setEnabled(True)

        except Exception as e:
            self.log_message(f"Error cargando colecciones: {e}")

    def select_all_collections(self):
        for i in range(self.collections_list.count()):
            self.collections_list.item(i).setSelected(True)

    def clear_selection(self):
        self.collections_list.clearSelection()

    def start_translation(self):
        selected_items = self.collections_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selección requerida", "Por favor selecciona al menos una colección")
            return

        collections_to_translate = [item.text() for item in selected_items]

        # Get language selections
        source_idx = self.source_combo.currentIndex()
        target_idx = self.target_combo.currentIndex()
        source_lang = self.lang_codes[source_idx]
        target_lang = self.lang_codes[target_idx]
        if source_lang == target_lang:
            QMessageBox.warning(self, "Advertencia", "Los idiomas de origen y destino deben ser diferentes")
            return

        # Crear worker y hilo
        self.thread = QThread()
        self.worker = TraductionWorker(collections_to_translate, source_lang, target_lang)
        self.worker.moveToThread(self.thread)

        # Conectar señales
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.log_message.connect(self.log_message)
        self.worker.finished.connect(self.translation_finished)
        self.worker.error.connect(self.log_message)

        # Estado de botones
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)

        self.thread.start()

    def cancel_translation(self):
        if self.worker:
            self.worker.cancel()

    def translation_finished(self):
        if self.thread:
            self.thread.quit()
            self.thread.wait()
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.log_message("Proceso completado")

    def log_message(self, message):
        if "traducida" in message or "Finalizada" in message or "Conectado" in message:
            self.log_text.setTextColor(QColor(50, 205, 50))  # Lime green
        elif "Error" in message or "cancelado" in message:
            self.log_text.setTextColor(QColor(255, 99, 71))  # Tomato red
        elif "saltada" in message:
            self.log_text.setTextColor(QColor(255, 165, 0))  # Orange
        elif "vacía" in message or "Encontradas" in message:
            self.log_text.setTextColor(QColor(30, 144, 255))  # Dodger blue
        elif "Procesando" in message:
            self.log_text.setTextColor(QColor(138, 43, 226))  # Purple
        else:
            self.log_text.setTextColor(QColor(211, 211, 211))  # Light gray

        self.log_text.append(message)
        # Auto-scroll
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def closeEvent(self, event):
        if self.worker and self.thread:
            self.worker.cancel()
            self.thread.quit()
            self.thread.wait()
        if self.client:
            self.client.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Aplicar tema oscuro formal
    palette = app.palette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.Text, QColor(255, 255, 255))
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
    palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
    app.setPalette(palette)

    window = TradutorApp()
    window.show()
    sys.exit(app.exec())
