from source import SourceSearch
from data import DataCluster

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QTreeWidgetItem

class GlobalEventBus(QObject):
    source_searched = Signal(SourceSearch)

    data_object_clicked = Signal(QTreeWidgetItem)
    data_object_double_clicked = Signal(QTreeWidgetItem)
    data_object_name_changed = Signal(QTreeWidgetItem)
    data_object_deleted = Signal(QTreeWidgetItem)
    data_object_moved = Signal(QTreeWidgetItem)

    filter_object_clicked = Signal(QTreeWidgetItem)
    filter_object_double_clicked = Signal(QTreeWidgetItem)
    filter_object_name_changed = Signal(QTreeWidgetItem)
    filter_object_deleted = Signal(QTreeWidgetItem)
    filter_object_moved = Signal(QTreeWidgetItem)

    def __init__(self):
        super().__init__()
        self.data_cluster = DataCluster()

state_bus = GlobalEventBus()
