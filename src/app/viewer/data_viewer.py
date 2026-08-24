
from source import SourceSearch
from data import Data, DataGroup
import utils
from state import state_bus
import resources
from app.viewer.abstract_viewer import TreeAppearance, TreeAdapter, AbstractTreeViewer

import PySide6.QtCore as QtCore
from PySide6.QtGui import QIcon, QColor

class DataTreeAppearence(TreeAppearance[Data]):

    def icon(self, obj, adapter) -> QIcon | None:
        return QIcon(resources.icon("data_group_icon.svg" if adapter.is_container(obj) else "data_icon.svg"))

    def foreground(self, obj, adapter) -> QColor | None:
        if not adapter.is_container(obj):
            return QColor(utils.generate_random_hex())

    def configure_item(self, item, obj, adapter) -> None:
        if adapter.is_container(obj):
            item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)
        else:
            item.setFlags((item.flags() & ~QtCore.Qt.ItemFlag.ItemIsDropEnabled) | QtCore.Qt.ItemFlag.ItemIsEditable)
    
class DataTreeAdapter(TreeAdapter[Data]):

    def name(self, obj: Data) -> str:
        return obj.name

    def children(self, obj: Data) -> list[Data]:
        if isinstance(obj, DataGroup):
            return [
                *obj.data_list,
                *obj.groups,
            ]

        return []

    def parent(self, obj: Data) -> DataGroup | None:
        return obj.parent

    def is_container(self, obj: Data) -> bool:
        return isinstance(obj, DataGroup)

    def move(self, obj: Data, new_parent: DataGroup | None) -> None:
        if self.is_container(obj):
            state_bus.data_cluster.move_group(obj, new_parent)
        else:
            state_bus.data_cluster.move_data(obj, new_parent)

    def remove(self, obj: Data) -> None:
        if self.is_container(obj):
            state_bus.data_cluster.remove_group(obj)
        else:
            state_bus.data_cluster.remove_data(obj)

    def rename(self, obj: Data, name: str) -> None:
        obj.set_name(name)

class DataTreeViewer(AbstractTreeViewer):
    def __init__(self):
        super().__init__(
            DataTreeAdapter(), 
            DataTreeAppearence(), 
            None, 
            "Grupos",
            item_clicked_signal=state_bus.data_object_clicked,
            item_double_clicked_signal=state_bus.data_object_double_clicked,
            item_name_changed_signal=state_bus.data_object_name_changed,
            item_deleted_signal=state_bus.data_object_deleted,
            item_moved_signal=state_bus.data_object_moved
        )

        # Intercepta o sinal de fontes pesquisadas
        state_bus.source_searched.connect(self._handle_new_data)

    # Lida com a importação de novos dados
    def _handle_new_data(self, source_search: SourceSearch):
        # Desativa e ativa (no final) o sorteamento automático depois da inserção dos itens 
        # Serve para prevenir problemas de performance: https://doc.qt.io/qt-6/qtreeview.html#sortingEnabled-prop
        self.setSortingEnabled(False)

        current_parent_widget_item = self.invisibleRootItem()
        current_parent_data_group = None

        if self.currentItem() is not None:
            obj = self.currentItem().data(0, QtCore.Qt.ItemDataRole.UserRole)
            if self.adapter.is_container(obj):
                current_parent_widget_item = self.currentItem()
                current_parent_data_group = obj

        # TODO: agnostic import method
        imported_pair = state_bus.data_cluster.import_source_as_data(
            source_search,
            current_parent_data_group,
            True, # TODO: criar uma opção para deixar a pessoa escolher se ela vai pesquisar os sub-grupos do caminho,
        )

        imported_source_kind, imported_source = imported_pair

        if imported_source_kind.is_file():
            # Distribui os dados importados o grupo selecionado ou dei
            [self.create_item(current_parent_widget_item, data) for data in imported_source]
        else:
            [self.populate_item(current_parent_widget_item, data_group) for data_group in imported_source]

        self.setSortingEnabled(True)
        # Sorteia com respeito ao indicador de tipo de sorteio escolhido no header
        self.sortItems(0, self.header().sortIndicatorOrder())