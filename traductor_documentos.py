"""
Traductor Completo: Extraer, Traducir y Componer en una sola interfaz GUI con PySide6.

Este script integra las funcionalidades de:
1. Extraer texto de archivos PDF/TXT y almacenarlo en MongoDB
2. Traducir colecciones de MongoDB utilizando Ollama
3. Componer archivos finales (TXT y PDF) desde las traducciones

Uso:
    python traductor_completo_gui.py

Dependencias:
    - pymongo: Para MongoDB
    - PySide6: Para la interfaz GUI
    - PyPDF2: Para leer PDFs
    - requests: Para API de Ollama
    - reportlab: Para generar PDFs
    - Ollama: Debe estar corriendo localmente en http://localhost:11434
"""
# (El encabezado y las importaciones las mantuve iguales que en tu versión)
import sys
import os
import re
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
                               QProgressBar, QTextEdit, QMessageBox, QFileDialog, QGroupBox,
                               QListWidget, QListWidgetItem, QComboBox, QCheckBox, QSplitter, QTabWidget, QLineEdit)
from PySide6.QtGui import QPalette, QColor, QFont
from PySide6.QtCore import QThread, Signal, QObject
import pymongo
import PyPDF2
import requests
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak


# Constantes
DATABASE_NAME = "traducciones"
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "gemma3:4b"

IDIOMA_CODES = ["es", "en", "fr"]
IDIOMA_NAMES = {
    "es": "Español",
    "en": "English",
    "fr": "Français"
}

IDIOMA_NAMES_PROMPT = {
    "es": "español",
    "en": "inglés",
    "fr": "francés"
}


# Funciones auxiliares
def traducir_con_ollama(texto: str, idioma_origen: str, idioma_destino: str) -> str:
    """Traduce texto usando Ollama."""
    nombre_origen = IDIOMA_NAMES_PROMPT[idioma_origen]
    nombre_destino = IDIOMA_NAMES_PROMPT[idioma_destino]

    prompt = ""
    if idioma_origen == "es":
        prompt = f"Translate the following text from Spanish to {nombre_destino}. Provide only the {nombre_destino} translation, without explanations or additional modifications:\n\n{texto}"
    elif idioma_origen == "en":
        prompt = f"Translate the following text from English to {nombre_destino}. Provide only the {nombre_destino} translation, without explanations or additional modifications:\n\n{texto}"
    elif idioma_origen == "fr":
        prompt = f"Translate the following text from French to {nombre_destino}. Provide only the {nombre_destino} translation, without explanations or additional modifications:\n\n{texto}"

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(OLLAMA_URL, json=payload)
    if response.status_code == 200:
        data = response.json()
        return data.get("response", "").strip()
    else:
        raise Exception(f"Error en petición Ollama: {response.status_code}")


def segmentar_frases(ruta_archivo: str):
    """Segmenta archivo PDF o TXT en frases."""
    frases = []
    contenido = ""

    ext = os.path.splitext(ruta_archivo)[1].lower()
    if ext == ".txt":
        with open(ruta_archivo, "r", encoding="utf-8") as f:
            contenido = f.read()
        frases = contenido.split('\n')
    elif ext == ".pdf":
        with open(ruta_archivo, "rb") as f:
            pdf_reader = PyPDF2.PdfReader(f)
            for page in pdf_reader.pages:
                contenido += (page.extract_text() or "") + "\n"

        # Para PDFs, reemplazar saltos de línea que no están precedidos por un punto con espacios
        contenido = re.sub(r'(?<!\.)\n', ' ', contenido)

        frases = contenido.split('\n')
    else:
        raise ValueError("Formato no soportado. Solo .txt y .pdf.")

    return frases


# Hilos de trabajo
class ExtractionWorker(QObject):
    progress = Signal(int)
    log = Signal(str)
    finished = Signal(bool, str)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
        self.cancelled = False

    def run(self):
        try:
            frases = segmentar_frases(self.file_path)

            client = pymongo.MongoClient()
            db = client[DATABASE_NAME]
            base = os.path.basename(self.file_path)
            coleccion_nombre = os.path.splitext(base)[0]
            coleccion = db[coleccion_nombre]
            coleccion.delete_many({})

            total = len(frases)
            for i, frase in enumerate(frases, 1):
                if self.cancelled:
                    client.close()
                    self.finished.emit(False, "Extracción cancelada.")
                    return
                coleccion.insert_one({"_id": i, "linea": frase})
                self.progress.emit(int((i / total) * 100))
                self.log.emit(f"Línea {i} procesada.")

            client.close()
            self.finished.emit(True, f"Extracción completada. {total} líneas guardadas en '{coleccion_nombre}'.")
        except Exception as e:
            self.finished.emit(False, f"Error extracción: {str(e)}")

    def cancel(self):
        self.cancelled = True


class TranslationWorker(QObject):
    progress = Signal(int)
    log = Signal(str)
    finished = Signal(bool, str)

    def __init__(self, collections, source_lang, target_lang):
        super().__init__()
        self.collections = collections
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.cancelled = False

    def run(self):
        try:
            client = pymongo.MongoClient()
            db = client[DATABASE_NAME]
            total_collections = len(self.collections)
            processed = 0

            for collection_name in self.collections:
                if self.cancelled:
                    client.close()
                    self.finished.emit(False, "Traducción cancelada.")
                    return

                self.log.emit(f"Traduciendo colección: {collection_name}")
                collection_origen = db[collection_name]
                collection_destino = db[f"{collection_name}_traducido_a_{self.target_lang}"]
                collection_destino.drop()

                total_docs = collection_origen.count_documents({})
                processed_docs = 0

                for documento in collection_origen.find():
                    if self.cancelled:
                        client.close()
                        self.finished.emit(False, "Traducción cancelada.")
                        return

                    linea_numero = documento["_id"]
                    linea_texto = documento["linea"]

                    if not linea_texto.strip():
                        collection_destino.insert_one({"_id": linea_numero, "linea": linea_texto})
                        processed_docs += 1
                        self.log.emit(f"Línea {linea_numero}: SKIP (vacía)")
                    elif linea_texto.strip():
                        traduccion = traducir_con_ollama(linea_texto, self.source_lang, self.target_lang)
                        collection_destino.insert_one({"_id": linea_numero, "linea": traduccion})
                        processed_docs += 1
                        # Truncate long translations for display
                        display_traduccion = traduccion[:80] + "..." if len(traduccion) > 80 else traduccion
                        self.log.emit(f"Línea {linea_numero}: '{display_traduccion}'")

                        # Emit progress after each translation
                        collection_progress = int((processed_docs / total_docs) * 100) if total_docs > 0 else 100
                        overall_progress = min(100, int((processed * 100 + collection_progress) / total_collections))
                        self.progress.emit(overall_progress)
                    # Handle empty lines too
                    if not linea_texto.strip():
                        processed_docs += 1
                        # Emit progress after each processed document
                        collection_progress = int((processed_docs / total_docs) * 100) if total_docs > 0 else 100
                        overall_progress = min(100, int((processed * 100 + collection_progress) / total_collections))
                        self.progress.emit(overall_progress)

                processed += 1
                self.log.emit(f"Finalizada colección {collection_name}")

                # Emit final progress for completed collection
                overall_progress = min(100, int((processed * 100) / total_collections))
                self.progress.emit(overall_progress)

            client.close()
            self.finished.emit(True, "Traducción completada.")
        except Exception as e:
            self.finished.emit(False, f"Error traducción: {str(e)}")

    def cancel(self):
        self.cancelled = True


class CompositionWorker(QObject):
    progress = Signal(int)
    log = Signal(str)
    finished = Signal(bool, str)

    def __init__(self, collections, save_dir, export_pdf):
        super().__init__()
        self.collections = collections
        self.save_dir = save_dir
        self.export_pdf = export_pdf
        self.cancelled = False

    def run(self):
        try:
            client = pymongo.MongoClient()
            db = client[DATABASE_NAME]
            total = len(self.collections)

            for i, coll_name in enumerate(self.collections, 1):
                if self.cancelled:
                    client.close()
                    self.finished.emit(False, "Composición cancelada.")
                    return

                self.log.emit(f"Procesando colección: {coll_name}")
                collection = db[coll_name]
                all_docs = list(collection.find(sort=[("_id", 1)]))

                output_file = os.path.join(self.save_dir, f"{coll_name}.txt")
                try:
                    with open(output_file, 'w', encoding='utf-8') as f:
                        for doc in all_docs:
                            if self.cancelled:
                                client.close()
                                self.finished.emit(False, "Composición cancelada.")
                                return
                            if 'linea' in doc:
                                linea_content = str(doc['linea'])
                                f.write(linea_content + '\n')
                    self.log.emit(f"Archivo TXT creado: {output_file}")
                except Exception as e:
                    self.log.emit(f"Error creando TXT '{output_file}': {str(e)}")
                    # continue to try PDF creation (or next collection)

                if self.export_pdf:
                    try:
                        pdf_file = os.path.join(self.save_dir, f"{coll_name}.pdf")

                        # Crear un estilo personalizado con justificación (no sobrescribimos el stylesheet global)
                        styles = getSampleStyleSheet()
                        body_style = ParagraphStyle(
                            'CustomBody',
                            parent=styles['BodyText'],
                            fontName="Helvetica",
                            fontSize=12,
                            alignment=TA_JUSTIFY,
                            leading=14
                        )

                        # Función para dibujar el número de página en el footer
                        def draw_page_number(canvas, doc):
                            try:
                                canvas.setFont('Helvetica', 10)
                                page_num = canvas.getPageNumber()
                                text = f"Página {page_num}"
                                canvas.drawRightString(letter[0] - 0.5 * inch, 0.75 * inch, text)
                            except Exception as e:
                                # Logger del hilo (no arrojar excepción a ReportLab)
                                self.log.emit(f"Error en draw_page_number: {str(e)}")

                        # Crear el documento con SimpleDocTemplate (callbacks se pasan a build)
                        pdf_template = SimpleDocTemplate(
                            pdf_file,
                            pagesize=letter,
                            leftMargin=0.5*inch,
                            rightMargin=0.5*inch,
                            topMargin=0.75*inch,
                            bottomMargin=1*inch
                        )

                        story = []

                        # Add some space at the top
                        story.append(Spacer(1, 0.25*inch))

                        num_paragraphs = 0
                        for doc in all_docs:
                            if 'linea' in doc:
                                linea_content = str(doc['linea']).strip()
                                if linea_content:
                                    p = Paragraph(linea_content, body_style)
                                    story.append(p)
                                    story.append(Spacer(1, 0.1*inch))
                                    num_paragraphs += 1

                        if num_paragraphs == 0:
                            # Agregar mensaje por defecto si no hay contenido
                            p = Paragraph("No hay contenido disponible.", body_style)
                            story.append(p)

                        self.log.emit(f"Preparado PDF con {num_paragraphs} párrafos.")
                        self.log.emit(f"Generando PDF - export_pdf: {self.export_pdf}, len(story): {len(story)}")

                        # Aquí pasamos los callbacks a build (corrección clave)
                        pdf_template.build(story, onFirstPage=draw_page_number, onLaterPages=draw_page_number)

                        # Verificar que el archivo exista y tenga tamaño
                        if os.path.exists(pdf_file) and os.path.getsize(pdf_file) > 0:
                            self.log.emit(f"Archivo PDF creado: {pdf_file}")
                        else:
                            self.log.emit(f"PDF creado pero está vacío o no existe: {pdf_file}")

                    except Exception as e:
                        self.log.emit(f"Error generando PDF para '{coll_name}': {str(e)}")

                self.progress.emit(int((i / total) * 100))

            client.close()
            self.finished.emit(True, "Composición completada.")
        except Exception as e:
            self.finished.emit(False, f"Error composición: {str(e)}")

    def cancel(self):
        self.cancelled = True


# (El resto de la UI y MainWindow queda exactamente igual que tu versión; lo incluyo aquí para que el archivo sea ejecutable)
# Main Window
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Traductor Completo - Extraer, Traducir y Componer")
        self.setGeometry(100, 100, 900, 700)
        self.apply_dark_theme()
        self.setup_ui()
        self.connect_signals()
        self.load_collections()

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                font-family: Arial, sans-serif;
            }
            QPushButton {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #606060;
                padding: 8px;
                border-radius: 4px;
                height: 35px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #303030;
            }
            QPushButton:disabled {
                background-color: #303030;
                color: #666666;
            }
            QLabel {
                color: #ffffff;
                font-size: 12px;
            }
            QListWidget {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #606060;
                border-radius: 4px;
                selection-background-color: #4CAF50;
            }
            QTextEdit {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #606060;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                font-size: 11px;
            }
            QProgressBar {
                background-color: #404040;
                border: 1px solid #606060;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
            }
            QComboBox {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #606060;
                border-radius: 4px;
                padding: 4px;
            }
            QLineEdit, QCheckBox {
                color: #ffffff;
                font-size: 12px;
            }
            QCheckBox::indicator {
                width: 15px;
                height: 15px;
                border: 1px solid #606060;
                background-color: #404040;
            }
            QCheckBox::indicator:checked {
                background-color: #4CAF50;
            }
            QGroupBox {
                color: #ffffff;
                font-weight: bold;
                border: 2px solid #606060;
                border-radius: 5px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)

    def setup_ui(self):
        main_layout = QVBoxLayout()

        # Tabs
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.setup_extraction_tab(), "1. Extraer Texto")
        self.tab_widget.addTab(self.setup_translation_tab(), "2. Traducir")
        self.tab_widget.addTab(self.setup_composition_tab(), "3. Componer Archivos TXT y PDF")

        main_layout.addWidget(self.tab_widget)

        # Activity Log
        self.log_group = QGroupBox("Registro de Actividad")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)

        main_layout.addWidget(self.log_group)

        self.setLayout(main_layout)

        self.worker = None
        self.thread = None

    def setup_extraction_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        # File selection
        file_group = QGroupBox("Seleccionar Archivo")
        file_layout = QVBoxLayout()
        self.extraction_file_label = QLabel("Archivo seleccionado: Ninguno")
        self.select_file_btn = QPushButton("Seleccionar Archivo (TXT/PDF)")
        file_layout.addWidget(self.extraction_file_label)
        file_layout.addWidget(self.select_file_btn)
        file_group.setLayout(file_layout)

        # Controls
        controls_group = QGroupBox("Controles")
        controls_layout = QVBoxLayout()
        self.extract_btn = QPushButton("Extraer Texto")
        self.extract_btn.setEnabled(False)
        controls_layout.addWidget(self.extract_btn)
        controls_group.setLayout(controls_layout)

        layout.addWidget(file_group)
        layout.addWidget(controls_group)
        layout.addStretch()

        tab.setLayout(layout)
        return tab

    def setup_translation_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        # Collections
        collections_group = QGroupBox("Colecciones por Traducir")
        collections_layout = QVBoxLayout()
        self.translation_list = QListWidget()
        self.translation_list.setSelectionMode(QListWidget.MultiSelection)
        self.refresh_btn = QPushButton("Actualizar Colecciones")
        collections_layout.addWidget(self.translation_list)
        collections_layout.addWidget(self.refresh_btn)
        collections_group.setLayout(collections_layout)

        # Language selection
        language_group = QGroupBox("Idiomas")
        language_layout = QVBoxLayout()
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("Desde:"))
        self.source_combo = QComboBox()
        self.source_combo.addItems([f"{code} - {name}" for code, name in IDIOMA_NAMES.items()])
        self.source_combo.setCurrentIndex(0)
        source_layout.addWidget(self.source_combo)

        target_layout = QHBoxLayout()
        target_layout.addWidget(QLabel("Hasta:"))
        self.target_combo = QComboBox()
        self.target_combo.addItems([f"{code} - {name}" for code, name in IDIOMA_NAMES.items()])
        self.target_combo.setCurrentIndex(1)
        target_layout.addWidget(self.target_combo)

        language_layout.addLayout(source_layout)
        language_layout.addLayout(target_layout)
        language_group.setLayout(language_layout)

        # Controls
        controls_group = QGroupBox("Controles")
        controls_layout = QVBoxLayout()
        self.translate_btn = QPushButton("Traducir Seleccionadas")
        self.translate_btn.setEnabled(False)
        self.translate_cancel_btn = QPushButton("Cancelar")
        self.translate_cancel_btn.setEnabled(False)
        controls_layout.addWidget(self.translate_btn)
        controls_layout.addWidget(self.translate_cancel_btn)
        controls_group.setLayout(controls_layout)

        # Translation Progress and Log
        progress_group = QGroupBox("Progreso de Traducción")
        progress_layout = QVBoxLayout()
        self.translation_progress = QProgressBar()
        self.translation_progress.setRange(0, 100)
        self.translation_progress.setValue(0)
        progress_layout.addWidget(self.translation_progress)

        translation_log_label = QLabel("Registro de Traducción:")
        self.translation_log = QTextEdit()
        self.translation_log.setMaximumHeight(300)
        self.translation_log.setFont(QFont("Monospace", 9))
        progress_layout.addWidget(translation_log_label)
        self.translation_log.setReadOnly(True)
        progress_layout.addWidget(self.translation_log)

        progress_group.setLayout(progress_layout)

        layout.addWidget(collections_group)
        layout.addWidget(language_group)
        layout.addWidget(controls_group)
        layout.addWidget(progress_group)

        tab.setLayout(layout)
        return tab

    def setup_composition_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        # Collections
        collections_group = QGroupBox("Colecciones Traducidas")
        collections_layout = QVBoxLayout()
        self.composition_list = QListWidget()
        self.composition_list.setSelectionMode(QListWidget.MultiSelection)
        self.refresh_translation_btn = QPushButton("Actualizar Colecciones Traducidas")
        collections_layout.addWidget(self.composition_list)
        collections_layout.addWidget(self.refresh_translation_btn)
        collections_group.setLayout(collections_layout)

        # Controls
        controls_group = QGroupBox("Controles")
        controls_layout = QVBoxLayout()
        self.compose_btn = QPushButton("Componer Archivos TXT y PDF")
        self.compose_btn.setEnabled(False)
        controls_layout.addWidget(self.compose_btn)
        controls_group.setLayout(controls_layout)

        layout.addWidget(collections_group)
        layout.addWidget(controls_group)
        layout.addStretch()

        tab.setLayout(layout)
        return tab

    def connect_signals(self):
        # Extraction
        self.select_file_btn.clicked.connect(self.select_file)
        self.extract_btn.clicked.connect(self.start_extraction)

        # Translation
        self.refresh_btn.clicked.connect(self.load_collections)
        self.translate_btn.clicked.connect(self.start_translation)
        self.translate_cancel_btn.clicked.connect(self.cancel_translation)

        # Composition
        self.refresh_translation_btn.clicked.connect(self.load_translated_collections)
        self.compose_btn.clicked.connect(self.start_composition)

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo", "", "Archivos de texto (*.txt);;PDF (*.pdf)")
        if file_path:
            self.extraction_file_path = file_path
            self.extraction_file_label.setText(f"Archivo seleccionado: {os.path.basename(file_path)}")
            self.extract_btn.setEnabled(True)
            self.log(f"Archivo seleccionado: {os.path.basename(file_path)}")
        else:
            self.extract_btn.setEnabled(False)
            self.extraction_file_label.setText("Archivo seleccionado: Ninguno")
            QMessageBox.warning(self, "Error", "No se pudo seleccionar el archivo.")

    def load_collections(self):
        try:
            client = pymongo.MongoClient()
            db = client[DATABASE_NAME]
            collections = db.list_collection_names()

            # Filter original collections (no translated ones)
            known_suffixes = [f"_traducido_a_{lang}" for lang in IDIOMA_CODES]
            original_collections = [coll for coll in collections if not any(coll.endswith(suf) for suf in known_suffixes)]

            self.translation_list.clear()
            for coll in sorted(original_collections):
                item = QListWidgetItem(coll)
                self.translation_list.addItem(item)

            if original_collections:
                self.translate_btn.setEnabled(True)
            else:
                self.translate_btn.setEnabled(False)

            client.close()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo cargar colecciones: {str(e)}")

    def load_translated_collections(self):
        try:
            client = pymongo.MongoClient()
            db = client[DATABASE_NAME]
            collections = db.list_collection_names()

            # Filter translated collections
            translated_collections = [coll for coll in collections if '_traducido_' in coll]

            self.composition_list.clear()
            for coll in sorted(translated_collections):
                item = QListWidgetItem(coll)
                self.composition_list.addItem(item)

            if translated_collections:
                self.compose_btn.setEnabled(True)
            else:
                self.compose_btn.setEnabled(False)

            client.close()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo cargar colecciones traducidas: {str(e)}")

    def check_ollama_connection(self):
        """Simple check for Ollama connection"""
        try:
            payload = {
                "model": MODEL_NAME,
                "prompt": "Hello",
                "stream": False
            }
            response = requests.post(OLLAMA_URL, json=payload, timeout=5)
            return response.status_code == 200
        except:
            return False

    def start_extraction(self):
        if not hasattr(self, 'extraction_file_path'):
            QMessageBox.warning(self, "Error", "Seleccione un archivo primero.")
            return

        # Check if thread is running
        if self.thread and self.thread.isRunning():
            return

        self.worker = ExtractionWorker(self.extraction_file_path)
        self.worker.finished.connect(self.on_worker_finished)

        from PySide6.QtCore import QThread
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)

        self.extract_btn.setText("Extrayendo...")
        self.extract_btn.setEnabled(False)
        self.thread.start()

    def start_translation(self):
        selected_items = self.translation_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Error", "Seleccione al menos una colección.")
            return

        if not self.check_ollama_connection():
            QMessageBox.warning(self, "Error", "No se puede conectar a Ollama. Asegúrese de que esté ejecutándose.")
            return

        collections = [item.text() for item in selected_items]
        source_idx = self.source_combo.currentIndex()
        target_idx = self.target_combo.currentIndex()
        source_lang = IDIOMA_CODES[source_idx]
        target_lang = IDIOMA_CODES[target_idx]

        if source_lang == target_lang:
            QMessageBox.warning(self, "Error", "Los idiomas deben ser diferentes.")
            return

        # Check if thread is running
        if self.thread and self.thread.isRunning():
            return

        self.worker = TranslationWorker(collections, source_lang, target_lang)
        self.worker.progress.connect(self.translation_progress.setValue)
        self.worker.log.connect(self.log_translation)
        self.worker.finished.connect(self.on_worker_finished)

        from PySide6.QtCore import QThread
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.thread.finished.connect(self.thread.quit)

        # Clear translation log and reset progress
        self.translation_log.clear()
        self.translation_progress.setValue(0)

        self.translate_btn.setText("Traduciendo...")
        self.translate_btn.setEnabled(False)
        self.translate_cancel_btn.setEnabled(True)
        self.thread.start()

    def cancel_translation(self):
        if self.worker and isinstance(self.worker, TranslationWorker) and self.thread and self.thread.isRunning():
            self.worker.cancel()
            self.translate_cancel_btn.setText("Cancelando...")
            self.translate_cancel_btn.setEnabled(False)

    def start_composition(self):
        selected_items = self.composition_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Error", "Seleccione al menos una colección.")
            return

        collections = [item.text() for item in selected_items]
        save_dir = QFileDialog.getExistingDirectory(self, "Seleccionar directorio para guardar archivos")
        if not save_dir:
            save_dir = os.getcwd()

        # Check if thread is running
        if self.thread and self.thread.isRunning():
            return

        self.worker = CompositionWorker(collections, save_dir, True)
        self.worker.log.connect(self.log)
        self.worker.finished.connect(self.on_worker_finished)

        from PySide6.QtCore import QThread
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.thread.finished.connect(self.thread.quit)

        self.compose_btn.setText("Componiendo...")
        self.compose_btn.setEnabled(False)
        self.thread.start()

    def on_worker_finished(self, success, message):
        # Reset buttons
        self.extract_btn.setText("Extraer Texto")
        self.extract_btn.setEnabled(True)
        self.translate_btn.setText("Traducir Seleccionadas")
        self.translate_btn.setEnabled(True)
        self.translate_cancel_btn.setText("Cancelar")
        self.translate_cancel_btn.setEnabled(False)
        self.compose_btn.setText("Componer Archivos")
        self.compose_btn.setEnabled(True)

        if self.thread:
            self.thread.quit()
            self.thread.wait()

        if success:
            QMessageBox.information(self, "Éxito", message)
        else:
            QMessageBox.warning(self, "Error", message)

        # Refresh collections if needed
        self.load_collections()
        self.load_translated_collections()

        # Reset worker and thread
        self.worker = None
        self.thread = None

    def log(self, message):
        self.log_text.append(message)
        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def log_translation(self, message):
        self.translation_log.append(message)
        # Auto-scroll to bottom
        scrollbar = self.translation_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())




if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
