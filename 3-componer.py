"""
Script para componer texto desde colecciones MongoDB traducidas.
Interfaz GUI con PySide6.

Este script extrae datos de colecciones de MongoDB que contienen "_traducido_" en su nombre,
lee el campo "linea" de cada documento y genera archivos de texto con el contenido.

Uso:
    python 3-componer.py

Dependencias:
    - pymongo: Para la conexión y operaciones con MongoDB
    - PySide6: Para la interfaz gráfica
"""

import sys
import os
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QProgressBar, QListWidget, QTextEdit, QMessageBox, QCheckBox
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import QThread, Signal
from pymongo import MongoClient
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph


class WorkerThread(QThread):
    """
    Hilo de trabajo para procesar las colecciones sin bloquear la GUI.
    """
    progress = Signal(int)
    log = Signal(str)
    finished_signal = Signal(bool, str)

    def __init__(self, collections, db_name='traducciones', export_pdf=False):
        super().__init__()
        self.collections = collections
        self.db_name = db_name
        self.export_pdf = export_pdf
        self.is_cancelled = False

    def run(self):
        try:
            # Conectar a MongoDB
            client = MongoClient('mongodb://localhost:27017/')

            # Buscar la base de datos correcta
            dbs = client.list_database_names()
            possible_dbs = ['traduciones', 'traducciones', 'translations']
            target_db = None
            for db_name in possible_dbs:
                if db_name in dbs:
                    target_db = db_name
                    break

            if not target_db:
                raise Exception("No se encontró ninguna base de datos de traducciones")

            db = client[target_db]

            total = len(self.collections)
            for i, coll_name in enumerate(self.collections, 1):
                if self.is_cancelled:
                    self.log.emit("Operación cancelada por el usuario.")
                    self.finished_signal.emit(False, "Operación cancelada por el usuario.")
                    return

                self.log.emit(f"Procesando colección: {coll_name}")
                collection = db[coll_name]

                # Obtener todos los documentos
                documents = collection.find()

                # Crear un archivo de texto con el nombre de la colección
                output_file = f"{coll_name}.txt"
                line_count = 0
                with open(output_file, 'w', encoding='utf-8') as f:
                    for doc in documents:
                        if self.is_cancelled:
                            self.log.emit("Operación cancelada por el usuario.")
                            self.finished_signal.emit(False, "Operación cancelada por el usuario.")
                            return

                        if 'linea' in doc:
                            linea_content = str(doc['linea'])
                            if linea_content.strip():  # Has actual content
                                f.write(linea_content + '\n')
                            else:  # Empty field = newline
                                f.write('\n')
                            line_count += 1

                self.log.emit(f"Archivo {output_file} creado con {line_count} líneas.")

                if self.export_pdf:
                    self.log.emit(f"Generando PDF para {coll_name}...")
                    try:
                        pdf_file = f"{coll_name}.pdf"
                        doc = SimpleDocTemplate(pdf_file, pagesize=letter)
                        styles = getSampleStyleSheet()
                        story = []
                        lines = []  # Assuming content is saved, but since not, we need to read
                        with open(output_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        lines = content.split('\n')
                        for line in lines:
                            if line.strip():
                                p = Paragraph(line, styles["Normal"])
                                story.append(p)
                        if story:
                            doc.build(story)
                            self.log.emit(f"Archivo PDF {pdf_file} creado.")
                        else:
                            self.log.emit("No hay contenido para el PDF.")
                    except Exception as e:
                        self.log.emit(f"Error generando PDF: {str(e)}")

                self.progress.emit(int((i / total) * 100))

            self.log.emit("Procesamiento completado.")
            self.finished_signal.emit(True, f"Se procesaron {total} colecciones exitosamente.")
        except Exception as e:
            self.log.emit(f"Error: {str(e)}")
            self.finished_signal.emit(False, f"Error: {str(e)}")
        finally:
            client.close()

    def cancel(self):
        self.is_cancelled = True


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Componer Texto desde MongoDB")
        self.setGeometry(300, 300, 600, 400)
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
            QCheckBox {
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
        """)

        # Widgets
        self.label_colecciones = QLabel("Colecciones disponibles para procesar:")
        self.list_colecciones = QListWidget()
        self.list_colecciones.setSelectionMode(QListWidget.SelectionMode.MultiSelection)

        self.btn_actualizar = QPushButton("Actualizar Lista")
        self.btn_actualizar.clicked.connect(self.actualizar_lista)

        self.btn_procesar = QPushButton("Procesar Seleccionadas")
        self.btn_procesar.clicked.connect(self.procesar_colecciones)
        self.btn_procesar.setEnabled(False)

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.clicked.connect(self.cancelar_proceso)
        self.btn_cancelar.setEnabled(False)

        self.checkbox_pdf = QCheckBox("Exportar también a PDF")
        self.checkbox_pdf.setChecked(False)

        self.label_log = QLabel("Registro de procesamiento:")
        self.text_log = QTextEdit()
        self.text_log.setReadOnly(True)

        self.label_progreso = QLabel("Progreso:")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        # Layout
        layout = QVBoxLayout()

        layout_h_colecciones = QHBoxLayout()
        layout_h_colecciones.addWidget(self.label_colecciones)
        layout_h_colecciones.addWidget(self.btn_actualizar)
        layout.addLayout(layout_h_colecciones)
        layout.addWidget(self.list_colecciones)

        layout_h_botones = QHBoxLayout()
        layout_h_botones.addWidget(self.btn_procesar)
        layout_h_botones.addWidget(self.btn_cancelar)
        layout_h_botones.addWidget(self.checkbox_pdf)
        layout.addLayout(layout_h_botones)

        layout.addWidget(self.label_log)
        layout.addWidget(self.text_log)

        layout.addWidget(self.label_progreso)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)

        self.worker = None
        self.actualizar_lista()  # Cargar colecciones al iniciar

    def actualizar_lista(self):
        try:
            client = MongoClient('mongodb://localhost:27017/')
            dbs = client.list_database_names()

            # Buscar la base de datos correcta
            possible_dbs = ['traduciones', 'traducciones', 'translations']
            target_db = None
            for db_name in possible_dbs:
                if db_name in dbs:
                    target_db = db_name
                    break

            if not target_db:
                raise Exception("No se encontró ninguna base de datos de traducciones")

            db = client[target_db]
            collections = db.list_collection_names()
            translated_collections = [coll for coll in collections if '_traducido_' in coll]

            self.list_colecciones.clear()
            if translated_collections:
                for coll in sorted(translated_collections):
                    self.list_colecciones.addItem(coll)
                self.btn_procesar.setEnabled(True)
                self.text_log.append(f"Lista actualizada desde BD '{target_db}'. {len(translated_collections)} colecciones disponibles.")
            else:
                self.list_colecciones.addItem("No se encontraron colecciones para procesar")
                self.btn_procesar.setEnabled(False)
                self.text_log.append(f"BD '{target_db}' conectada, pero no hay colecciones con '_traducido_'.")
                client.close()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo conectar a MongoDB:\n{str(e)}")
            self.btn_procesar.setEnabled(False)
            self.text_log.append(f"Error al conectar a MongoDB: {str(e)}")
            if 'client' in locals():
                client.close()

    def procesar_colecciones(self):
        selected_items = self.list_colecciones.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Información", "Seleccione al menos una colección para procesar.")
            return

        collections = [item.text() for item in selected_items]

        self.btn_procesar.setEnabled(False)
        self.btn_cancelar.setEnabled(True)
        self.btn_actualizar.setEnabled(False)
        self.checkbox_pdf.setEnabled(False)
        self.progress_bar.setValue(0)
        self.text_log.clear()
        self.text_log.append("Iniciando procesamiento...")

        self.worker = WorkerThread(collections, export_pdf=self.checkbox_pdf.isChecked())
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.log.connect(self.text_log.append)
        self.worker.finished_signal.connect(self.proceso_finalizado)
        self.worker.start()

    def cancelar_proceso(self):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.btn_cancelar.setText("Cancelando...")
            self.btn_cancelar.setEnabled(False)

    def proceso_finalizado(self, success, message):
        self.btn_procesar.setEnabled(True)
        self.btn_cancelar.setEnabled(False)
        self.btn_cancelar.setText("Cancelar")
        self.btn_actualizar.setEnabled(True)
        self.checkbox_pdf.setEnabled(True)

        if success:
            QMessageBox.information(self, "Éxito", message)
            self.progress_bar.setValue(100)
        else:
            QMessageBox.warning(self, "Error", message)


# Modo de prueba para depuración
def test_mode():
    """Versión de consola para testing"""
    try:
        print("=== MODO DE PRUEBA ===")
        print("Conectando a MongoDB...")

        # Verificar conexión básica
        client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
        print(f"Cliente conectado: {client}")

        # Listar bases de datos disponibles
        dbs = client.list_database_names()
        print(f"Bases de datos disponibles: {dbs}")

        # Buscar variaciones del nombre de la base de datos
        possible_dbs = ['traduciones', 'traducciones', 'translations']
        target_db = None
        for db_name in possible_dbs:
            if db_name in dbs:
                target_db = db_name
                break

        if not target_db:
            print("¡ADVERTENCIA! No se encontró ninguna base de datos de traducciones.")
            print("Bases de datos encontradas:", [db for db in dbs if db != 'admin' and db != 'config' and db != 'local'])
            client.close()
            return

        print(f"✅ Base de datos encontrada: '{target_db}'")

        # Usar la base de datos encontrada
        db = client[target_db]
        print(f"Base de datos conectada: {db}")

        # Obtener todas las colecciones
        collections = db.list_collection_names()
        print(f"Colecciones encontradas: {collections}")

        # Filtrar colecciones que contienen "_traducido_" en el nombre
        translated_collections = [coll for coll in collections if '_traducido_' in coll]
        print(f"Colecciones traducidas: {translated_collections}")

        if not translated_collections:
            print("No se encontraron colecciones con '_traducido_' en el nombre.")
            print("Colecciones disponibles:", collections)
            client.close()
            return

        print(f"\n=== Encontradas {len(translated_collections)} colecciones para procesar ===")

        # Mostrar contenido de las primeras 2 colecciones
        for coll_name in translated_collections[:2]:
            print(f"\n=== Inspeccionando colección: {coll_name} ===")
            collection = db[coll_name]

            # Contar documentos
            doc_count = collection.count_documents({})
            print(f"Número de documentos: {doc_count}")

            if doc_count == 0:
                print("¡ADVERTENCIA! La colección está vacía.")
                continue

            print(f"\n📄 Patrón de contenido (primeros 5 documentos):")
            total_content_lines = 0
            for i, doc in enumerate(collection.find().limit(5)):
                print(f"  Documento {i+1}: ID={doc.get('_id', 'N/A')}")
                if 'linea' in doc:
                    content = str(doc['linea']).strip()
                    if content:
                        content_lines = len(content.split('\n'))
                        total_content_lines += content_lines
                        print(f"    Líneas en contenido: {content_lines}")
                        print(f"    Contenido: '{content[:70]}{'...' if len(content) > 70 else ''}'")
                    else:
                        print("    Contenido vacío o solo espacios")
                else:
                    print("    ¡Campo 'linea' no encontrado!")

            print(f"\n📊 Resumen colección '{coll_name}':")
            print(f"  - Total documentos: {doc_count}")
            print(f"  - Contenido aproximado: ~{total_content_lines} líneas (basado en primeros 5 docs)")

            # Calcular cuán grande debería ser viendo si hay documentos vacíos
            empty_docs = 0
            non_empty_docs = 0
            for doc in collection.find():
                if 'linea' in doc and str(doc['linea']).strip():
                    non_empty_docs += 1
                else:
                    empty_docs += 1
            print(f"  - Documentos con contenido: {non_empty_docs}")
            print(f"  - Documentos vacíos: {empty_docs}")

            if doc_count < 100 and 'el_quijote' in coll_name.lower():
                print(f"  ⚠️  ADVERTENCIA: Esperaría más documentos para '{coll_name}' (original tenía 2186 líneas)")
                print("        ¿El proceso de traducción se completó completamente?")

        client.close()
        print("\n=== PRUEBA COMPLETADA ===")

    except Exception as e:
        print(f"Error en modo de prueba: {e}")
        print(f"Tipo de error: {type(e)}")
        print("Sugerencias:")
        print("  1. Asegúrate de que MongoDB esté ejecutándose")
        print("  2. Verifica que la base de datos 'traduciones' existe")
        print("  3. Comprueba que hay colecciones con '_traducido_' en el nombre")
        print("  4. Asegúrate de que los documentos tienen el campo 'linea'")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_mode()
    else:
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
