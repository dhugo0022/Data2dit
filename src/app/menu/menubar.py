from pathlib import Path

from data import QT_FILE_DIALOG_NAME_FILTER
from source import SourceKind, SourceSearch
from state import state_bus

from PySide6.QtWidgets import QFileDialog, QMenuBar
from PySide6.QtCore import QStandardPaths
from PySide6.QtGui import QAction

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
