# testgui.py
# ─────────────────────────────────────────────────────────────────────────────
"""
Dashboard de prueba para WolfSight-PDF con menú lateral desplegable.
Versión definitiva con todas las correcciones de tipado para Pylance.
---------------------------------------------------------------------
• PyQt 6   • Python 3.12   • Windows 10/11 x64
"""

from __future__ import annotations

import sys
import datetime as _dt
from pathlib import Path
# CORRECCIÓN: Se importa 'cast' para ayudar con el tipado si es necesario, aunque isinstance es mejor.
from typing import cast

from PyQt6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QStackedWidget,
    QFileDialog,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QProgressBar,
    QSpacerItem,
    QSizePolicy,
    QMessageBox,
    QScrollArea,
    QGridLayout,
    QFrame,
    QStyle,
)

# ────────────────────────────── Rutas ────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
ICONS_DIR = PROJECT_ROOT / "assets" / "icons"
IMG_DIR = PROJECT_ROOT / "extracted_dni" / "cropped"
LOG_DIR = PROJECT_ROOT / "logs"
QSS_PATH = PROJECT_ROOT / "ui" / "styles" / "style.qss"

# ────────────────── Función de Ayuda para Cargar Íconos (CORREGIDA) ──────────
def get_icon(file_name: str, fallback_icon: QStyle.StandardPixmap) -> QIcon:
    """
    Carga un ícono desde un archivo si existe.
    Si no, utiliza un ícono estándar de PyQt como respaldo.
    """
    path = ICONS_DIR / file_name
    if path.exists():
        return QIcon(str(path))
    
    # CORRECCIÓN: Se verifica que la instancia sea de QApplication (GUI) y no de QCoreApplication (no-GUI).
    # Esto soluciona el error de que ".style()" no existe en "QCoreApplication".
    app = QApplication.instance()
    if isinstance(app, QApplication):
        return app.style().standardIcon(fallback_icon)
    
    return QIcon()

# ───────────────────────── Menú lateral desplegable ─────────────────────────
class SideMenu(QFrame):
    """Menú lateral animado que contiene su propio botón para colapsarse."""
    
    EXPANDED_WIDTH = 220
    COLLAPSED_WIDTH = 60

    PAGES: list[tuple[str, str, str, QStyle.StandardPixmap]] = [
        ("exp.png", "Expedientes", "Explorar expedientes", QStyle.StandardPixmap.SP_DirOpenIcon),
        ("logs.png", "Logs", "Ver registros", QStyle.StandardPixmap.SP_FileIcon),
        ("config.png", "Configuración", "Ajustes de la aplicación", QStyle.StandardPixmap.SP_FileDialogDetailedView),
    ]

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("sideMenu")
        self.setFixedWidth(self.EXPANDED_WIDTH)
        self.is_expanded = True
        self.nav_buttons: list[QPushButton] = []
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Configura la interfaz, incluyendo el botón de menú."""
        self.menu_layout = QVBoxLayout(self)
        self.menu_layout.setContentsMargins(5, 5, 5, 5)
        self.menu_layout.setSpacing(10)
        self.menu_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.toggle_button = QPushButton()
        self.toggle_button.setObjectName("toggleButton")
        self.toggle_button.setIcon(get_icon("menu.png", QStyle.StandardPixmap.SP_TitleBarMenuButton))
        self.toggle_button.setIconSize(QSize(28, 28))
        self.toggle_button.setToolTip("Contraer/Expandir Menú")
        self.menu_layout.addWidget(self.toggle_button)
        
        self.title_label = QLabel("WolfSight")
        self.title_label.setObjectName("menuTitle")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.menu_layout.addWidget(self.title_label)

        for icon_name, text, tooltip, fallback in self.PAGES:
            button = self._create_nav_button(icon_name, text, tooltip, fallback)
            self.nav_buttons.append(button)
            self.menu_layout.addWidget(button)

        self.menu_layout.addSpacerItem(
            QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )
    
    def _connect_signals(self):
        """Conecta la señal del botón de menú a la función de animación."""
        self.toggle_button.clicked.connect(self.toggle_menu)

    def _create_nav_button(self, icon_name: str, text: str, tooltip: str, fallback: QStyle.StandardPixmap) -> QPushButton:
        """Crea un botón de navegación para el menú."""
        button = QPushButton(f"  {text}")
        button.setObjectName("menuButton")
        button.setIcon(get_icon(icon_name, fallback))
        button.setIconSize(QSize(24, 24))
        button.setToolTip(tooltip)
        button.setCheckable(True)
        return button

    def toggle_menu(self):
        """Anima la expansión o colapso del menú."""
        start_width = self.width()
        end_width = self.COLLAPSED_WIDTH if self.is_expanded else self.EXPANDED_WIDTH
        
        self.animation = QPropertyAnimation(self, b"maximumWidth")
        self.animation.setDuration(300)
        self.animation.setStartValue(start_width)
        self.animation.setEndValue(end_width)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.animation.finished.connect(self._on_animation_finished)
        self.animation.start()
        
        self.is_expanded = not self.is_expanded

    def _on_animation_finished(self):
        """Actualiza el texto de los botones y el título al finalizar la animación."""
        self.title_label.setVisible(self.is_expanded)
        for i, button in enumerate(self.nav_buttons):
            text = f"  {self.PAGES[i][1]}" if self.is_expanded else ""
            button.setText(text)

    @pyqtProperty(int)
    def maximumWidth(self) -> int:
        return super().maximumWidth()

    # CORRECCIÓN: Se mantiene el "# type: ignore" como garantía para silenciar el aviso de Pylance.
    @maximumWidth.setter
    def maximumWidth(self, width: int) -> None: # type: ignore
        super().setMaximumWidth(width)
        super().setMinimumWidth(width)


# ──────────────────────── Página de miniaturas ──────────────────────────────
class ThumbGrid(QWidget):
    def __init__(self, source_dir: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.source_dir = source_dir
        self.setObjectName("thumbGridPage")
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        container = QWidget(); self.grid = QGridLayout(container)
        self.grid.setSpacing(12); scroll.setWidget(container)
        layout = QVBoxLayout(self); layout.setContentsMargins(0,0,0,0)
        layout.addWidget(scroll); self.load_images()
    def load_images(self) -> None:
        self.clear_grid()
        if not self.source_dir.exists(): return
        images = sorted(self.source_dir.glob("*.png"))[:60]
        for idx, img_path in enumerate(images):
            row, col = divmod(idx, 6)
            lbl = QLabel(); lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pixmap = QPixmap(str(img_path))
            if not pixmap.isNull():
                pix = pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                lbl.setPixmap(pix)
            lbl.setToolTip(img_path.name); self.grid.addWidget(lbl, row, col)
    def clear_grid(self) -> None:
        while (item := self.grid.takeAt(0)) is not None:
            if (widget := item.widget()) is not None: widget.setParent(None)

# ─────────────────────────── Página de logs ─────────────────────
class LogsTable(QTableWidget):
    """Tabla que enumera archivos de log."""
    def __init__(self, log_dir: Path, parent: QWidget | None = None) -> None:
        super().__init__(0, 3, parent)
        self.log_dir = log_dir
        self.setHorizontalHeaderLabels(["Nombre", "Tamaño (KB)", "Modificado"])
        
        header = self.horizontalHeader()
        assert header is not None
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        v_header = self.verticalHeader()
        assert v_header is not None
        v_header.setVisible(False)
        
        self.populate()
        
    def populate(self) -> None:
        self.setRowCount(0)
        if not self.log_dir.exists(): return
        for file in sorted(self.log_dir.iterdir()):
            if not file.is_file(): continue
            row = self.rowCount(); self.insertRow(row)
            self.setItem(row, 0, QTableWidgetItem(file.name))
            kb = file.stat().st_size / 1024
            self.setItem(row, 1, QTableWidgetItem(f"{kb:.1f}"))
            ts = _dt.datetime.fromtimestamp(file.stat().st_mtime)
            self.setItem(row, 2, QTableWidgetItem(ts.strftime("%Y-%m-%d %H:%M:%S")))


# ───────────────────────── Página de configuración ──────────────────────────
class ConfigPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self); layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        label = QLabel("Ajustes de la aplicación (placeholder)")
        label.setStyleSheet("font-size: 18px; font-weight: 600;"); layout.addWidget(label)
        btn_choose = QPushButton("Cambiar directorio de expedientes…"); btn_choose.clicked.connect(self.change_dir)
        layout.addWidget(btn_choose)
        pb = QProgressBar(); pb.setValue(40); layout.addWidget(pb)
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
    def change_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Elegir carpeta")
        if path: QMessageBox.information(self, "Sin implementar", f"Seleccionado:\n{path}")


# ───────────────────────────── Ventana principal ────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("WolfSight — Dashboard")
        self.resize(1280, 720)
        self.setWindowIcon(get_icon("wolf.png", QStyle.StandardPixmap.SP_ComputerIcon))

        main_widget = QWidget()
        self.main_layout = QHBoxLayout(main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.setCentralWidget(main_widget)

        self.sidebar = SideMenu()
        self.main_layout.addWidget(self.sidebar)

        self.content_widget = QFrame()
        self.content_widget.setObjectName("contentFrame")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(15, 10, 15, 10)
        self.content_layout.setSpacing(10)
        self.main_layout.addWidget(self.content_widget)

        self._setup_header()

        self.stack = QStackedWidget()
        self.content_layout.addWidget(self.stack)

        self._setup_pages()
        self._connect_signals()
        
        self.sidebar.nav_buttons[0].setChecked(True)
        self._update_header_title(0)

        status = self.statusBar()
        if status: status.showMessage("Listo")

        if QSS_PATH.exists():
            with QSS_PATH.open(encoding="utf-8") as qss_file: self.setStyleSheet(qss_file.read())

    def _setup_header(self):
        """Configura la cabecera simple que solo muestra el título."""
        header_widget = QWidget()
        header_widget.setObjectName("headerFrame")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)

        self.header_title = QLabel("Expedientes")
        self.header_title.setObjectName("headerTitle")
        header_layout.addWidget(self.header_title)
        header_layout.addStretch()
        
        self.content_layout.addWidget(header_widget)

    def _setup_pages(self):
        """Crea e inicializa las páginas de la aplicación."""
        self.page_expedientes = ThumbGrid(IMG_DIR)
        self.page_logs = LogsTable(LOG_DIR)
        self.page_config = ConfigPage()

        self.stack.addWidget(self.page_expedientes)
        self.stack.addWidget(self.page_logs)
        self.stack.addWidget(self.page_config)

    def _connect_signals(self):
        """Conecta las señales de los botones de navegación."""
        self.stack.currentChanged.connect(self._update_header_title)
        for i, button in enumerate(self.sidebar.nav_buttons):
            button.clicked.connect(lambda checked, idx=i: self._change_page(idx))

    def _change_page(self, index: int):
        """Cambia la página visible y actualiza el estado de los botones."""
        self.stack.setCurrentIndex(index)
        for i, button in enumerate(self.sidebar.nav_buttons):
            button.setChecked(i == index)

    def _update_header_title(self, index: int):
        """Actualiza el título de la cabecera según la página actual."""
        if 0 <= index < len(self.sidebar.PAGES):
            title = self.sidebar.PAGES[index][1]
            self.header_title.setText(title)


# ───────────────────────────────── Main ─────────────────────────────────────
def main() -> None:
    app = QApplication(sys.argv)
    
    # Se asume que los directorios necesarios existen al correr la app.
    # No es responsabilidad de la GUI crearlos en cada ejecución.
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()