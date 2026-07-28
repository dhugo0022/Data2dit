import sys
import random
from typing import List
from pathlib import Path

from source import *
from data import QT_FILE_DIALOG_NAME_FILTER, Data, DataGroup
from state import state_bus
import utils

import PySide6.QtCore as QtCore
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
import pyqtgraph as pg

class MenuBarWidget(QMenuBar):

    def __init__(self, parent = None):
        super().__init__(parent)
        # Menu de arquivos
        self.addFileMenu()

    def _handle_source_files_selection(self, source_paths: list[Path]):
        state_bus.source_searched.emit(SourceSearch(
                SourceKind.FILE,
                [Path(source_path) for source_path in source_paths]
            )
        )

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

    def _handle_source_folder_selection(self, source_paths: list[Path]):
        state_bus.source_searched.emit(SourceSearch(
                    SourceKind.FOLDER,
                    [Path(source_path) for source_path in source_paths]
                )
            )

    def _create_source_folder_selector(self):
        self.import_folder_dialog = QFileDialog(self)
        self.import_folder_dialog.setDirectory(QStandardPaths.standardLocations(QStandardPaths.StandardLocation.HomeLocation)[-1])
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

class DataTreeItem(QTreeWidgetItem):
    
    def __lt__(self, other):
        self_node = self.data(0, QtCore.Qt.ItemDataRole.UserRole)
        other_node = other.data(0, QtCore.Qt.ItemDataRole.UserRole)

        self_key = (
            0 if isinstance(self_node, DataGroup) else 1,
            utils.natural_key(self.text(0)),
        )

        other_key = (
            0 if isinstance(other_node, DataGroup) else 1,
            utils.natural_key(other.text(0)),
        )

        return self_key < other_key

class DataGroupViewer(QTreeWidget):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setHeaderLabel("Grupos")

        # Ativa o sistema de drag and drop
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QTreeWidget.DragDropMode.InternalMove) # Impede que outras coisas sejam arrastadas para dentro do visualizador

        # Lida com a selecão de items
        self.itemPressed.connect(self._handle_item_pressed)

        # Intercepta o sinal de fontes pesquisadas
        state_bus.source_searched.connect(self._handle_new_data)

    # Guarda um grupo que foi selecionada para que possamos importar uma coisa diretamente nele
    def _handle_item_pressed(self, tree_widget_item, i):
        pass
    
    def _handle_new_data(self, source_search: SourceSearch):

        def add_data_item(parent_widget_item: DataTreeItem, data: Data):
            data_item = DataTreeItem(parent_widget_item, [data.name])
            data_item.setData(0, QtCore.Qt.ItemDataRole.UserRole, data)
            data_item.setFlags(data_item.flags() & ~Qt.ItemFlag.ItemIsDropEnabled)

        def add_data_group_item_recursive(parent_widget_item: DataTreeItem, data_group: DataGroup):
            new_data_group_item = DataTreeItem(parent_widget_item, [data_group.name])
            new_data_group_item.setData(0, QtCore.Qt.ItemDataRole.UserRole, data_group)
            # Permite que o nome do grupo seja editado
            new_data_group_item.setFlags(new_data_group_item.flags() | Qt.ItemFlag.ItemIsEditable)

            # Adiciona os items que representam os dados do grupo
            [add_data_item(new_data_group_item, data) for data in data_group.data_list]

            # Inicia uma execução recusiva para adicionar os subgrupos do grupo que iniciou a cadeia de execução
            [add_data_group_item_recursive(new_data_group_item, sub_group) for sub_group in data_group.groups]

            # Faz com que todas os sub grupos e dados guardados nesse item sejam organizados em: grupo -> dados (em ordem alfabética)
            new_data_group_item.sortChildren(0, QtCore.Qt.SortOrder.AscendingOrder)

        # TODO: mudar para o root selecioando
        current_parent_widget_item = self.invisibleRootItem()

        imported_pair = state_bus.data_cluster.import_source_as_data(
            source_search,
            None, # TODO: se já houver uma pasta pré-selecionada, implementar
            True, # TODO: criar uma opção para deixar a pessoa escolher se ela vai pesquisar os sub-grupos do caminho,
        )

        imported_source_kind, imported_source = imported_pair

        if imported_source_kind.is_file():
            # Distribui os dados importados o grupo selecionado ou dei
            [add_data_item(current_parent_widget_item, data) for data in imported_source]
        else:
            [add_data_group_item_recursive(current_parent_widget_item, data_group) for data_group in imported_source]

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
# def add_graph(data_nodes: tuple[SourceTreeNode]):
#     x_data = data_nodes[0].data.x
#     y_data = data_nodes[0].data.y

#     plot = pg.PlotWidget()
#     plot.plot(x_data, y_data)
#     plot.showGrid(True)

#     return plot


def run_application():
    app = QApplication()
    app.setApplicationName("data2dit")
    app.setApplicationDisplayName("Data2dit")
    
    win = AppMainWindow()
    win.show()

    sys.exit(app.exec()) # Sai do bloco de execução e passa o código status de saída (0 = sucesso, etc) da aplicação para o sistema

