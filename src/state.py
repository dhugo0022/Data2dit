from typing import Dict

from source import SourceSearch
from data import DataCluster

from PySide6.QtCore import *
from PySide6.QtWidgets import *

class GlobalEventBus(QObject):
    source_searched = Signal(object)

    def __init__(self):
        super().__init__()
        self.data_cluster = DataCluster()
        self.selected_data_group: QTreeWidgetItem | None = None

state_bus = GlobalEventBus()
