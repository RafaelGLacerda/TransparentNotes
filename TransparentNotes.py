import sys, os 

# --- Fixar ícone na barra de tarefas (Windows) ---
if sys.platform == "win32":
    import ctypes
    myappid = "TransparentNotepad.App"  # identificador único
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

try:
    from PyQt6 import QtWidgets, QtCore, QtGui
    from PyQt6.QtCore import Qt
    qt_lib = "PyQt6"
except Exception:
    from PyQt5 import QtWidgets, QtCore, QtGui
    from PyQt5.QtCore import Qt
    qt_lib = "PyQt5"


class TransparentNotepad(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        # --- Ícone do app ---
        icon_path = os.path.join(os.path.dirname(__file__), "icone.ico")
        self.setWindowIcon(QtGui.QIcon(icon_path))
        
        self.resize(900, 550)
        self.setMinimumSize(300, 200)

        # Transparência e sem moldura
        if qt_lib == "PyQt6":
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        else:
            self.setWindowFlags(Qt.FramelessWindowHint)
            self.setAttribute(Qt.WA_TranslucentBackground, True)

        self.drag_pos = None
        self.toolbar_visible = True
        self.current_file = None  # caminho do arquivo atual

        # --- Layout principal ---
        main_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout(main_widget)
        main_layout.setContentsMargins(6, 6, 6, 6)
        self.setCentralWidget(main_widget)

        # --- Barra de título ---
        title_bar = QtWidgets.QHBoxLayout()
        title_bar.setSpacing(6)

        title_label = QtWidgets.QLabel("TransparentNotes")
        title_label.setStyleSheet("color:white; font-weight:bold; font-size:14px;")

        minimize_btn = QtWidgets.QPushButton("–")
        minimize_btn.setFixedSize(28, 28)
        minimize_btn.setStyleSheet(self.btn_style())
        minimize_btn.clicked.connect(self.showMinimized)

        close_btn = QtWidgets.QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet(self.btn_style(red=True))
        close_btn.clicked.connect(self.close)

        title_bar.addWidget(title_label)
        title_bar.addStretch(1)
        title_bar.addWidget(minimize_btn)
        title_bar.addWidget(close_btn)

        title_container = QtWidgets.QWidget()
        title_container.setLayout(title_bar)
        title_container.setStyleSheet("background: rgba(0,0,0,0.25); border-radius:8px; padding:4px;")
        main_layout.addWidget(title_container)

        # --- Barra de caminhos ---
        self.path_bar = QtWidgets.QHBoxLayout()
        self.path_bar.setSpacing(4)
        self.path_container = QtWidgets.QWidget()
        self.path_container.setLayout(self.path_bar)
        self.path_container.setStyleSheet("background: rgba(0,0,0,0.25); border-radius:8px; padding:4px;")
        main_layout.addWidget(self.path_container)
        self.update_path_bar(os.path.expanduser("~"))  # caminho inicial

        # --- Barra de formatação + recolher ---
        self.toolbar_container = QtWidgets.QWidget()
        toolbar_layout = QtWidgets.QHBoxLayout(self.toolbar_container)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(4)

        self.toolbar = QtWidgets.QToolBar()
        self.toolbar.setIconSize(QtCore.QSize(18, 18))
        self.toolbar.setStyleSheet("""
            QToolBar { background: rgba(0,0,0,0.25); border-radius:8px; }
            QToolButton { color:white; padding:4px; }
            QToolButton:hover { background: rgba(255,255,255,0.15); }
        """)

        toolbar_layout.addWidget(self.toolbar)
        toolbar_layout.addStretch(1)

        # Botão recolher/expandir
        self.toggle_btn = QtWidgets.QPushButton("▴")
        self.toggle_btn.setFixedSize(28, 28)
        self.toggle_btn.setStyleSheet(self.btn_style())
        self.toggle_btn.clicked.connect(self.toggle_toolbar)
        toolbar_layout.addWidget(self.toggle_btn)
        main_layout.addWidget(self.toolbar_container)

        # --- Editor ---
        self.editor = QtWidgets.QTextEdit()
        self.editor.setStyleSheet("""
            QTextEdit {
                background: rgba(255,255,255,0.07);
                color: white;
                border-radius: 8px;
                padding: 12px;
                font-size: 14pt;
            }
        """)
        self.editor.setFont(QtGui.QFont("Segoe UI", 12))
        main_layout.addWidget(self.editor, 1)

        # --- Ações ---
        self.setup_toolbar()

        # Atalhos padrão
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+S"), self, self.save_file)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+O"), self, self.open_file)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Z"), self, self.editor.undo)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Y"), self, self.editor.redo)

        # --- Carregar texto anterior ---
        self.last_path = os.path.join(os.path.expanduser('~'), ".transparent_notepad_last.txt")
        if os.path.exists(self.last_path):
            with open(self.last_path, "r", encoding="utf-8") as f:
                self.editor.setPlainText(f.read())

        # Redimensionamento
        self.resizing = False
        self.edge_margin = 8

    # =====================================================
    # BARRA DE PASTAS
    # =====================================================
    def update_path_bar(self, folder_path):
        # limpar barra
        for i in reversed(range(self.path_bar.count())):
            widget = self.path_bar.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        parts = folder_path.split(os.sep)
        path_acc = ""
        for part in parts:
            if not part:
                continue
            path_acc = os.path.join(path_acc, part)
            btn = QtWidgets.QPushButton(part)
            btn.setStyleSheet(self.btn_style())
            btn.clicked.connect(lambda checked, p=path_acc: self.update_path_bar(p))
            self.path_bar.addWidget(btn)

        # botão + para salvar como
        plus_btn = QtWidgets.QPushButton("+")
        plus_btn.setFixedSize(28, 28)
        plus_btn.setStyleSheet(self.btn_style())
        plus_btn.clicked.connect(self.save_file_as)
        self.path_bar.addWidget(plus_btn)

    def save_file_as(self):
        default_name = self.editor.toPlainText().splitlines()[0] if self.editor.toPlainText() else "novo_arquivo"
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Salvar como", os.path.join(os.path.expanduser("~"), f"{default_name}.txt"), "Text Files (*.txt)"
        )
        if path:
            self.current_file = path
            self.save_file()

    # =====================================================
    # TOOLBAR E FORMATOS
    # =====================================================
    def btn_style(self, red=False):
        if red:
            return """QPushButton { color: white; background: rgba(255,0,0,0.4); border: none; border-radius: 6px; }
                      QPushButton:hover { background: rgba(255,0,0,0.8); }"""
        else:
            return """QPushButton { color: white; background: rgba(255,255,255,0.15); border: none; border-radius: 6px; }
                      QPushButton:hover { background: rgba(255,255,255,0.25); }"""

    def setup_toolbar(self):
        def add_action(text, func):
            act = QtGui.QAction(text, self)
            act.setCheckable(True)
            act.triggered.connect(func)
            self.toolbar.addAction(act)
            return act

        self.bold_act = add_action("B", self.set_bold)
        self.italic_act = add_action("I", self.set_italic)
        self.underline_act = add_action("U", self.set_underline)

        self.toolbar.addSeparator()

        color_act = QtGui.QAction("🎨", self)
        color_act.triggered.connect(self.set_color)
        self.toolbar.addAction(color_act)

        font_box = QtWidgets.QFontComboBox()
        font_box.currentFontChanged.connect(self.set_font_family)
        self.toolbar.addWidget(font_box)

        size_box = QtWidgets.QComboBox()
        for i in range(8, 41, 2):
            size_box.addItem(str(i))
        size_box.currentIndexChanged.connect(self.set_font_size)
        self.toolbar.addWidget(size_box)

        self.toolbar.addSeparator()

        for sym, align in [
            ("⯇", Qt.AlignmentFlag.AlignLeft),
            ("⯈⯇", Qt.AlignmentFlag.AlignCenter),
            ("⯈", Qt.AlignmentFlag.AlignRight),
            ("☰", Qt.AlignmentFlag.AlignJustify),
        ]:
            act = QtGui.QAction(sym, self)
            act.triggered.connect(lambda checked, a=align: self.editor.setAlignment(a))
            self.toolbar.addAction(act)

        self.toolbar.addSeparator()

        open_act = QtGui.QAction("📂", self)
        open_act.triggered.connect(self.open_file)
        self.toolbar.addAction(open_act)

        save_act = QtGui.QAction("💾", self)
        save_act.triggered.connect(self.save_file)
        self.toolbar.addAction(save_act)

    def toggle_toolbar(self):
        self.toolbar_visible = not self.toolbar_visible
        self.toolbar.setVisible(self.toolbar_visible)
        self.toggle_btn.setText("▴" if self.toolbar_visible else "▾")

    def set_bold(self):
        fmt = QtGui.QTextCharFormat()
        current_weight = self.editor.fontWeight()
        new_weight = QtGui.QFont.Weight.Normal if current_weight > QtGui.QFont.Weight.Normal else QtGui.QFont.Weight.Bold
        fmt.setFontWeight(new_weight)
        self.merge_format(fmt)
        self.bold_act.setChecked(new_weight == QtGui.QFont.Weight.Bold)

    def set_italic(self):
        fmt = QtGui.QTextCharFormat()
        current_italic = self.editor.fontItalic()
        fmt.setFontItalic(not current_italic)
        self.merge_format(fmt)
        self.italic_act.setChecked(not current_italic)

    def set_underline(self):
        fmt = QtGui.QTextCharFormat()
        current_under = self.editor.fontUnderline()
        fmt.setFontUnderline(not current_under)
        self.merge_format(fmt)
        self.underline_act.setChecked(not current_under)

    def set_font_family(self, font):
        fmt = QtGui.QTextCharFormat()
        fmt.setFontFamily(font.family())
        self.merge_format(fmt)

    def set_font_size(self, index):
        size = int(self.sender().currentText())
        fmt = QtGui.QTextCharFormat()
        fmt.setFontPointSize(size)
        self.merge_format(fmt)

    def set_color(self):
        color = QtWidgets.QColorDialog.getColor(QtGui.QColor("white"), self, "Escolher cor do texto")
        if color.isValid():
            fmt = QtGui.QTextCharFormat()
            fmt.setForeground(color)
            self.merge_format(fmt)

    def merge_format(self, fmt):
        cursor = self.editor.textCursor()
        if not cursor.hasSelection():
            cursor.select(QtGui.QTextCursor.SelectionType.WordUnderCursor)
        cursor.mergeCharFormat(fmt)
        self.editor.mergeCurrentCharFormat(fmt)

    # =====================================================
    # SALVAR / ABRIR ARQUIVO
    # =====================================================
    def open_file(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Abrir arquivo", os.path.expanduser("~"), "Text Files (*.txt)"
        )
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.editor.setPlainText(f.read())
                self.current_file = path
                self.setWindowTitle(f"Transparent Notepad - {os.path.basename(path)}")
                self.update_path_bar(os.path.dirname(path))
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Erro", f"Não foi possível abrir o arquivo:\n{e}")

    def save_file(self):
        if not self.current_file:
            self.save_file_as()
            return

        try:
            with open(self.current_file, "w", encoding="utf-8") as f:
                f.write(self.editor.toPlainText())
            self.setWindowTitle(f"Transparent Notepad - {os.path.basename(self.current_file)}")
            self.update_path_bar(os.path.dirname(self.current_file))
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Erro", f"Não foi possível salvar o arquivo:\n{e}")

        # salvar cópia local
        with open(self.last_path, "w", encoding="utf-8") as f:
            f.write(self.editor.toPlainText())

    # =====================================================
    # MOVER / REDIMENSIONAR
    # =====================================================
    def mousePressEvent(self, event):
        try:
            left = event.button() == Qt.MouseButton.LeftButton if hasattr(Qt, "MouseButton") else event.button() == Qt.LeftButton
        except Exception:
            left = event.button() == Qt.LeftButton
        if not left:
            return super().mousePressEvent(event)

        local = event.pos()
        self._mouse_global = event.globalPosition().toPoint() if hasattr(event, "globalPosition") else event.globalPos()
        rect = self.rect()

        if local.x() >= rect.width() - self.edge_margin and local.y() >= rect.height() - self.edge_margin:
            self.resizing = True
            self._resize_start_pos = self._mouse_global
            self._resize_start_geo = self.geometry()
        else:
            self.drag_pos = self._mouse_global
            self._start_geo = self.frameGeometry()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        cur_global = event.globalPosition().toPoint() if hasattr(event, "globalPosition") else event.globalPos()

        if hasattr(Qt, "CursorShape"):
            CUR_SIZE_FDIAG = Qt.CursorShape.SizeFDiagCursor
            CUR_SIZE_H = Qt.CursorShape.SizeHorCursor
            CUR_SIZE_V = Qt.CursorShape.SizeVerCursor
        else:
            CUR_SIZE_FDIAG = Qt.SizeFDiagCursor
            CUR_SIZE_H = Qt.SizeHorCursor
            CUR_SIZE_V = Qt.SizeVerCursor

        if getattr(self, "resizing", False):
            dx = cur_global.x() - self._resize_start_pos.x()
            dy = cur_global.y() - self._resize_start_pos.y()
            new_w = max(self.minimumWidth(), self._resize_start_geo.width() + dx)
            new_h = max(self.minimumHeight(), self._resize_start_geo.height() + dy)
            self.resize(new_w, new_h)
            return

        if getattr(self, "drag_pos", None):
            diff = cur_global - self.drag_pos
            self.setGeometry(self._start_geo.translated(diff))
            return

        local = event.pos()
        rect = self.rect()
        on_right = (local.x() >= rect.width() - self.edge_margin)
        on_bottom = (local.y() >= rect.height() - self.edge_margin)

        if on_right and on_bottom:
            self.setCursor(CUR_SIZE_FDIAG)
        elif on_right:
            self.setCursor(CUR_SIZE_H)
        elif on_bottom:
            self.setCursor(CUR_SIZE_V)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor if hasattr(Qt, "CursorShape") else Qt.ArrowCursor)

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.drag_pos = None
        self.resizing = False
        self.setCursor(Qt.CursorShape.ArrowCursor if hasattr(Qt, "CursorShape") else Qt.ArrowCursor)
        super().mouseReleaseEvent(event)


def main():
    app = QtWidgets.QApplication(sys.argv)
    icon_path = os.path.join(os.path.dirname(__file__), "icone.ico")
    app.setWindowIcon(QtGui.QIcon(icon_path))

    win = TransparentNotepad()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
