"""
Este script extrae texto de un archivo, lo segmenta en frases separadas por puntos,
y almacena cada frase en una colección de MongoDB.
Interfaz GUI con PySide6.

El script lee un archivo de texto seleccionado por el usuario,
segmenta el contenido respetando los saltos de línea y los puntos finales,
y luego conecta a una base de datos MongoDB local para almacenar cada segmento
como un documento separado en una colección nombrada según el archivo.

Uso:
    python 1-extraer_texto_a mongodb_con_gui.py

Dependencias:
    - pymongo: Para la conexión y operaciones con MongoDB
    - PySide6: Para la interfaz gráfica
    - El archivo de texto especificado debe existir

Colección MongoDB:
    - Base de datos: traducciones
    - Colección: [nombre_del_archivo_sin_extensión]
    - Documentos: {"_id": int, "linea": str}
"""

import sys
import os
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QProgressBar, QFileDialog, QMessageBox
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import QThread, Signal
import pymongo


class WorkerThread(QThread):
    """
    Hilo de trabajo para procesar el archivo sin bloquear la GUI.
    """
    progress = Signal(int)
    finished_signal = Signal(bool, str)

    def __init__(self, ruta_archivo):
        super().__init__()
        self.ruta_archivo = ruta_archivo
        self.is_cancelled = False

    def run(self):
        try:
            resultado = self.segmentar_frases(self.ruta_archivo)

            # Conectar a MongoDB
            client = pymongo.MongoClient()
            db = client.traducciones
            base = os.path.basename(self.ruta_archivo)
            coleccion_nombre = os.path.splitext(base)[0]
            coleccion = db[coleccion_nombre]

            # Limpiar la colección antes de insertar
            coleccion.delete_many({})

            total = len(resultado)
            for i, frase in enumerate(resultado, 1):
                if self.is_cancelled:
                    self.finished_signal.emit(False, "Operación cancelada por el usuario.")
                    return

                coleccion.insert_one({"_id": i, "linea": frase})
                self.progress.emit(int((i / total) * 100))

            self.finished_signal.emit(True, f"Proceso completado. {total} frases insertadas en '{coleccion_nombre}'.")
        except Exception as e:
            self.finished_signal.emit(False, f"Error: {str(e)}")

    def cancel(self):
        self.is_cancelled = True

    def segmentar_frases(self, ruta_archivo: str):
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


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Extractor de Texto a MongoDB")
        self.setGeometry(300, 300, 500, 250)
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
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #303030;
            }
            QLabel {
                color: #ffffff;
                font-size: 12px;
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
        """)

        # Widgets
        self.label_archivo = QLabel("Seleccionar archivo de texto:")
        self.btn_seleccionar = QPushButton("Seleccionar archivo")
        self.btn_seleccionar.clicked.connect(self.seleccionar_archivo)

        self.label_progreso = QLabel("Progreso:")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        self.btn_procesar = QPushButton("Procesar")
        self.btn_procesar.clicked.connect(self.procesar_archivo)
        self.btn_procesar.setEnabled(False)

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.clicked.connect(self.cancelar_proceso)
        self.btn_cancelar.setEnabled(False)

        self.status_label = QLabel("Seleccione un archivo y presione 'Procesar' para iniciar.")

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.label_archivo)
        layout.addWidget(self.btn_seleccionar)

        layout_h = QHBoxLayout()
        layout_h.addWidget(self.btn_procesar)
        layout_h.addWidget(self.btn_cancelar)
        layout.addLayout(layout_h)

        layout.addWidget(self.label_progreso)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)

        self.setLayout(layout)

        self.ruta_archivo = None
        self.worker = None

    def seleccionar_archivo(self):
        self.ruta_archivo, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo de texto", "", "Archivos de texto (*.txt)")
        if self.ruta_archivo:
            self.btn_procesar.setEnabled(True)
            self.status_label.setText(f"Archivo seleccionado: {os.path.basename(self.ruta_archivo)}")
        else:
            self.btn_procesar.setEnabled(False)
            self.status_label.setText("Ningún archivo seleccionado.")

    def procesar_archivo(self):
        if not self.ruta_archivo:
            QMessageBox.warning(self, "Advertencia", "Por favor, seleccione un archivo primero.")
            return

        self.btn_procesar.setEnabled(False)
        self.btn_cancelar.setEnabled(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Procesando...")

        self.worker = WorkerThread(self.ruta_archivo)
        self.worker.progress.connect(self.progress_bar.setValue)
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
        self.status_label.setText(message)
        if success:
            QMessageBox.information(self, "Éxito", message)
            self.progress_bar.setValue(100)
        else:
            QMessageBox.warning(self, "Error", message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
