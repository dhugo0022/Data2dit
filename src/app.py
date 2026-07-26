import sys
import random
from typing import List
from dataclasses import dataclass, astuple

from source import SourceTreeNode, SourceTree, generate_sources_from_paths, SourceKind
from data import QT_FILE_DIALOG_NAME_FILTER

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
import pyqtgraph as pg

@dataclass(frozen=True)
class SourceFindSignal:
    kind: SourceKind
    raw_source: list[str]

    def __iter__(self):
        return iter(astuple(self))
class GlobalEventBus(QObject):
    # Define your application-wide events here
    source_sent = Signal(object)

# Create a single instance at the module level
bus = GlobalEventBus()

class MenuBarWidget(QMenuBar):

    def __init__(self, parent = None):
        super().__init__(parent)
        # Menu de arquivos
        self.addFileMenu()

    def _handle_source_files_selection(self, source_paths):
        bus.source_sent.emit(SourceFindSignal(SourceKind.FILE, source_paths))

    # Menu
    def _create_and_show_source_files_selector(self):
        self.import_file_dialog = QFileDialog(self)
        # Coloca o diretorio inicial para ser sempre a "home"
        self.import_file_dialog.setDirectory(QStandardPaths.standardLocations(QStandardPaths.StandardLocation.HomeLocation)[-1])
        self.import_file_dialog.setWindowTitle("Selecão de arquivos fonte")
        self.import_file_dialog.setViewMode(QFileDialog.ViewMode.List)
        self.import_file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        self.import_file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
        self.import_file_dialog.setNameFilter(QT_FILE_DIALOG_NAME_FILTER)
        
        self.import_file_dialog.filesSelected.connect(self._handle_source_files_selection)
        self.import_file_dialog.show()

    def _handle_source_folder_selection(self, source_folder):
        bus.source_sent.emit(SourceFindSignal(SourceKind.FOLDER, source_folder))

    def _create_source_folder_selector(self):
        self.import_folder_dialog = QFileDialog(self)
        self.import_file_dialog.setDirectory(QStandardPaths.standardLocations(QStandardPaths.StandardLocation.HomeLocation)[-1])
        self.import_folder_dialog.setWindowTitle("Selecão de pasta fonte")
        self.import_folder_dialog.setViewMode(QFileDialog.ViewMode.List)
        self.import_folder_dialog.setFileMode(QFileDialog.FileMode.Directory)
        self.import_folder_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
        
        self.import_folder_dialog.filesSelected.connect(self._handle_source_folder_selection)
        self.import_folder_dialog.show()
        
    def addFileMenu(self):
        file_menu = self.addMenu("&Arquivo")

        # Ação de importar arquivos fonte
        import_file_action = QAction("Importar arquivos fonte", self)
        import_file_action.triggered.connect(self._create_and_show_source_files_selector)

        # Ação de importar pasta fonte
        import_folder_action = QAction("Importar pasta fonte", self)
        import_folder_action.triggered.connect(self._create_source_folder_selector)

        # Adicionar as ações no menu
        file_menu.addAction(import_file_action)
        file_menu.addAction(import_folder_action)

class DataGroupViewer(QTreeWidget):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setHeaderLabels(["Name"])
        
        # 1. Enable Drag and Drop
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QTreeWidget.DragDropMode.InternalMove)
        self.setDropIndicatorShown(True)

        bus.source_sent.connect(self._handle_new_sources)

    def _handle_new_sources(self, source_find_signal: SourceFindSignal):
        source_kind, raw_sources = source_find_signal
        sources = generate_sources_from_paths(source_kind, raw_sources)
        source_tree = SourceTree(sources)
        source_tree.grow_tree()
    
        self.add_nested_items(source_tree.root, self.invisibleRootItem())

    def add_nested_items(self, source_node: SourceTreeNode, parent_item):
        """Recursively populates the tree and flags items as editable."""

        item = QTreeWidgetItem(parent_item, [source_node.name])
        item.setFlags(item.flags() | Qt.ItemFlag.Item)

        if source_node.source.kind.is_file():
            item.setToolTip(0, str(source_node.name))
        if source_node.source.kind.is_folder():
            for key, child_node in source_node.children.items():
                self.add_nested_items(child_node, item)
        

class MainContentWidget(QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)

        self.LEFT_PANEL_MIN_SIZE_PERCENTAGE = 0.2
        self.LEFT_PANEL_MAX_SIZE_PERCENTAGE = 0.3

        self.addContentLayout()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.left_panel_container.setMinimumWidth(int(self.width() * self.LEFT_PANEL_MIN_SIZE_PERCENTAGE))
        self.left_panel_container.setMaximumWidth(int(self.width() * self.LEFT_PANEL_MAX_SIZE_PERCENTAGE))

    def createLeftContentPanel(self):
        screen = QApplication.primaryScreen().geometry()

        self.left_panel_container = QWidget()
        self.left_panel_container.setMinimumWidth(int(screen.width() * self.LEFT_PANEL_MIN_SIZE_PERCENTAGE))
        self.left_panel_container.setMaximumWidth(int(screen.width() * self.LEFT_PANEL_MAX_SIZE_PERCENTAGE))

        self.left_panel_layout = QVBoxLayout()

        self.data_group_viewer = DataGroupViewer()

        self.left_panel_layout.addWidget(self.data_group_viewer)

        self.left_panel_container.setLayout(self.left_panel_layout)
        return self.left_panel_container

    def createRightContentPanel(self):
        self.right_panel_container = QWidget()
        self.right_panel_layout = QVBoxLayout() 

        self.right_panel_container.setLayout(self.right_panel_layout)
        return self.right_panel_container
    
    def addContentLayout(self):
        screen = QApplication.primaryScreen().geometry()

        content_layout = QHBoxLayout(self)
        
        content_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Impede que os widgets do splitters se colapsem no canto da tela e sumam 
        content_splitter.setChildrenCollapsible(False)
     
        content_splitter.addWidget(self.createLeftContentPanel())
        content_splitter.addWidget(self.createRightContentPanel())

        # Define o tamanho máximo para o widget da esquerda e da direita
        default_left_panel_size_difference = self.LEFT_PANEL_MAX_SIZE_PERCENTAGE - self.LEFT_PANEL_MIN_SIZE_PERCENTAGE
        initial_left_panel_width = int(screen.width() * (self.LEFT_PANEL_MIN_SIZE_PERCENTAGE + (default_left_panel_size_difference / 2)))

        content_splitter.setSizes([initial_left_panel_width, screen.width() - initial_left_panel_width])

        content_layout.addWidget(content_splitter)

class AppMainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self, None)
        self.set_screen_constraints()

        # Colocar a menubar
        self.setupWidgets()

    def set_screen_constraints(self):
        screen = QApplication.primaryScreen().geometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        w = screen.width() * 0.75
        h = screen.height() * 0.8

        self.setGeometry(x, y, w, h)
        self.setMinimumSize(screen.width() * 0.4, screen.height() * 0.45)

    # Menu bar

    def setupWidgets(self):
        self.menubar = MenuBarWidget()
        self.setMenuBar(self.menubar)

        self.main_content_widget = MainContentWidget()
        self.setCentralWidget(self.main_content_widget)


def generate_random_hex():
    # 0xFFFFFF corresponds to the decimal number 16777215
    return f"#{random.randint(0, 0xFFFFFF):06x}"

"""
pxMode=True: This forces PyQtGraph to pre-render the symbols into a single image cache (an atlas) rather than drawing each point as a separate vector piece.
pen=None or width=1: Straying away from standard pen sizes causes heavy drawing bottlenecks in the Qt framework.
useCache=True: Reuses pre-rendered elements.
"""
def add_graph(data_nodes: tuple[SourceTreeNode]):
    x_data = data_nodes[0].data.x
    y_data = data_nodes[0].data.y

    plot = pg.PlotWidget()
    plot.plot(x_data, y_data)
    plot.showGrid(True)

    return plot


def run_application():
    app = QApplication()
    app.setApplicationName("data2dit")
    app.setApplicationDisplayName("Data2dit")
    
    win = AppMainWindow()
    win.show()

    sys.exit(app.exec()) # Sai do bloco de execução e passa o código status de saída (0 = sucesso, etc) da aplicação para o sistema

