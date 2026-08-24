import sys
import random

from app.menu.menubar import MenuBarWidget
from app.viewer.data_viewer import DataTreeViewer
from app.graph.data_graphing import DataGraphingLayout

import PySide6.QtCore as QtCore
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
import pyqtgraph as pg

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

        left_panel_layout = QVBoxLayout()

        data_tree_viewer = DataTreeViewer()
        # pipeline_viewer = DataGroupViewer()
        
        left_panel_layout.addWidget(data_tree_viewer)
        # left_panel_layout.addWidget(pipeline_viewer)

        self.left_panel_container.setLayout(left_panel_layout)
        return self.left_panel_container

    def createRightContentPanel(self):
        right_panel_container = QWidget()
        right_panel_layout = QVBoxLayout() 

        data_graphing_layout = DataGraphingLayout()
        right_panel_layout.addWidget(data_graphing_layout)

        right_panel_container.setLayout(right_panel_layout)
        return right_panel_container
    
    def addContentLayout(self):
        screen = QApplication.primaryScreen().geometry()

        content_layout = QHBoxLayout()
        
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

        self.setLayout(content_layout)

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

def run_application():
    app = QApplication()
    app.setApplicationName("data2dit")
    app.setApplicationDisplayName("Data2dit")

    # Adiciona suporte para modo escuro
    app.setStyle("Fusion")

    # Ativa o anti-aliasing do Pyqtgraph
    pg.setConfigOptions(antialias=True)

    win = AppMainWindow()
    win.show()
    
    sys.exit(app.exec()) # Sai do bloco de execução e passa o código status de saída (0 = sucesso, etc) da aplicação para o sistema

