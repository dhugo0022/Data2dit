import sys
import random

from source import SourceTreeNode
from data import QT_FILE_DIALOG_NAME_FILTER

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMenu
import pyqtgraph as pg

class AppMainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self, None)
        self._set_max_screen_dimension()

        # Colocar a menubar
        self.createMenuBar()

    def _center_screen(self):
        screen = QApplication.primaryScreen().geometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)

    def _set_max_screen_dimension(self):
        screen = QApplication.primaryScreen().geometry()
        self.resize(screen.width(), screen.height())

    def _handle_source_files_selection(self, source_paths):
        print(f"Arquivos fonte: {source_paths}")

    def _create_and_show_source_files_selector(self):
        self.import_file_dialog = QFileDialog(self)
        self.import_file_dialog.setWindowTitle("Selecão de arquivos fonte")
        self.import_file_dialog.setViewMode(QFileDialog.ViewMode.List)
        self.import_file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        self.import_file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
        self.import_file_dialog.setNameFilter(QT_FILE_DIALOG_NAME_FILTER)
        
        self.import_file_dialog.filesSelected.connect(self._handle_source_files_selection)
        self.import_file_dialog.show()

    def _handle_source_folder_selection(self, source_folder):
        print(f"Pasta fonte: {source_folder}")

    def _create_source_folder_selector(self):
        self.import_folder_dialog = QFileDialog(self)
        self.import_folder_dialog.setWindowTitle("Selecão de pasta fonte")
        self.import_folder_dialog.setViewMode(QFileDialog.ViewMode.List)
        self.import_folder_dialog.setFileMode(QFileDialog.FileMode.Directory)
        self.import_folder_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
        
        self.import_folder_dialog.filesSelected.connect(self._handle_source_folder_selection)
        self.import_folder_dialog.show()
        
    def implementFileMenu(self, file_menu: QMenu):
        # Ação de importar arquivos fonte
        import_file_action = QAction("Importar arquivos fonte", self)
        import_file_action.triggered.connect(self._create_and_show_source_files_selector)

        # Ação de importar pasta fonte
        import_folder_action = QAction("Importar pasta fonte", self)
        import_folder_action.triggered.connect(self._create_source_folder_selector)

        # Adicionar as ações no menu
        file_menu.addAction(import_file_action)
        file_menu.addAction(import_folder_action)

    def createMenuBar(self):
        menubar = self.menuBar()

        # Menu de arquivos
        file_menu = menubar.addMenu("&Arquivo")

        # Adicionando os menus na menubar
        self.implementFileMenu(file_menu)

    def createGraphWidget(self):
        pass


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

