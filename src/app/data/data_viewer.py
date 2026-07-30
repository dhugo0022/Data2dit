
from source import SourceSearch
from data import Node, Data, DataGroup
import utils
from state import state_bus
import resources

import PySide6.QtCore as QtCore
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QAbstractItemView
from PySide6.QtGui import QIcon, QBrush, QColor

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

        # == Configuração de propriedades do Widget ==
        
        # Ativa o sistema de drag and drop
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        # Impede que outras coisas sejam arrastadas para dentro do visualizador
        self.setDragDropMode(QTreeWidget.DragDropMode.InternalMove) 

        # Faz com que a seleção seja a mesma de um explorador de arquivos visual, como o do Windows
        self.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        # Faz com que so seja possível selecionar items
        self.setSelectionBehavior(QTreeWidget.SelectionBehavior.SelectItems)

        # Faz com que só possa mudar o nome do grupo com a tecla de edição do sistema
        # Padrão: F2
        self.setEditTriggers(QAbstractItemView.EditTrigger.EditKeyPressed)

        # == Lidando com os Signals ==

        # Intercepta o sinal de seleção de item ao dar double click
        self.itemDoubleClicked.connect(self._handle_item_double_click)
        self.itemClicked.connect(self._handle_item_click)
        self.itemChanged.connect(self._handle_item_changed)

        # Intercepta o sinal de fontes pesquisadas
        state_bus.source_searched.connect(self._handle_new_data)

    # Desseleciona completamente a seleção prévia caso o usuário clique
    # em um lugar em branco.
    def mousePressEvent(self, event):
        item = self.itemAt(event.position().toPoint())

        if item is None:
            self.clearSelection()
            self.setCurrentItem(None)

        super().mousePressEvent(event)

    """
    Como o Qt automaticamente toma conta da transferência de pais dos itens
    nós só precisamos lidar com o estado interno (DataCluster), que guarda
    os dados e grupos de dados, de maneira que a mudança desse estado reflita
    a mudança no visualizador de dados.
    """
    def dropEvent(self, event):
        target_item: QTreeWidgetItem = self.itemAt(event.position().toPoint())
        selected_items = self.selectedItems()

        new_parent: DataGroup | None = None

        if target_item is not None:
            """
            Mesmo se colocara a flag de impedir que o item receba itens, ainda assim
            esse evento de drop é ativado. Logo, temos que cuidar desse caso também
            já que não pode ser possível que um item de dado seja jogado dentro de
            outro.
            """
            if isinstance(target_item.data(0, QtCore.Qt.ItemDataRole.UserRole), Data):
                return

            """
            Como só é possível acionar esse evento para o movimento de dados e grupos de dados
            para dentro de outros grupos de dados, não precisamos temos como pegar um "Data" 
            ao invés de um "DataGroup".
            A exceção é quando as coisas são movidas para fora de qualquer outro grupo, porém
            a função de mover do DataCluster já lida com isso.
            """
            new_parent = target_item.data(0, QtCore.Qt.ItemDataRole.UserRole)

        """
        Mesmo que tanto DataGroup, quanto Data, sejam descendentes de Node, ainda assim
        é precisso lidar com os dados de maneira separada. Especialmente porque é preciso
        acessar outras variáveis, além daquela que se refere ao pai, durante a mudança.
        """
        for selected_item in selected_items:
            data_object: DataGroup | Data = selected_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            if isinstance(data_object, DataGroup):
                state_bus.data_cluster.move_group(data_object, new_parent)
            else: # Se for descendente de Data
                state_bus.data_cluster.move_data(data_object, new_parent)

        super().dropEvent(event)

    # Usado para lidar com ações de clique duplo no widget
    def _handle_item_double_click(self, pressed_widget_item: DataTreeItem, _: int):
        state_bus.data_object_double_clicked.emit(pressed_widget_item)

    # Usado para lidar com ações de clique simples no widget
    def _handle_item_click(self, pressed_widget_item: DataTreeItem, _: int):
        state_bus.data_object_clicked.emit(pressed_widget_item)

    def _handle_item_changed(self, changed_widget_item: DataTreeItem, _: int):
        changed_item_name = changed_widget_item.text(0)
        data_object: Node = changed_widget_item.data(0, QtCore.Qt.ItemDataRole.UserRole)

        # Verificação para caso o nome tenha mudado
        old_name = data_object.name
        if old_name != changed_item_name: # Quer dizer que o nome mudou
            """
            Como Data e DataObject são subclasses de Node, não há perigo
            simplesmente chamar a função de mudar de nome. Já que esta
            função é definida no próprio escopo de Node
            """
            data_object.set_name(changed_item_name)
            state_bus.data_object_name_changed.emit(changed_widget_item)
        

    # Lida com a importação de novos dados
    def _handle_new_data(self, source_search: SourceSearch):
        # Desativa e ativa (no final) o sorteamento automático depois da inserção dos itens 
        # Serve para prevenir problemas de performance: https://doc.qt.io/qt-6/qtreeview.html#sortingEnabled-prop
        self.setSortingEnabled(False)

        def add_data_item(parent_widget_item: DataTreeItem, data: Data):
            data_item = DataTreeItem(parent_widget_item, [data.name])
            data_item.setData(0, QtCore.Qt.ItemDataRole.UserRole, data)
            data_item.setIcon(0, QIcon(resources.icon("data_icon.svg")))
            data_item.setForeground(0, QBrush(QColor(utils.generate_random_hex())))
            # Remove a possibilidade de dropar outros itens dentro dele
            data_item.setFlags((data_item.flags() & ~QtCore.Qt.ItemFlag.ItemIsDropEnabled) | QtCore.Qt.ItemFlag.ItemIsEditable)

        def add_data_group_item_recursive(parent_widget_item: DataTreeItem, data_group: DataGroup):
            new_data_group_item = DataTreeItem(parent_widget_item, [data_group.name])
            new_data_group_item.setData(0, QtCore.Qt.ItemDataRole.UserRole, data_group)
            new_data_group_item.setIcon(0, QIcon(resources.icon("data_group_icon.svg")))

            # Permite que o nome do grupo seja editado
            new_data_group_item.setFlags(new_data_group_item.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)

            # Adiciona os items que representam os dados do grupo
            [add_data_item(new_data_group_item, data) for data in data_group.data_list]

            # Inicia uma execução recursiva para adicionar os subgrupos do grupo que iniciou a cadeia de execução
            [add_data_group_item_recursive(new_data_group_item, sub_group) for sub_group in data_group.groups]

        current_parent_widget_item = self.invisibleRootItem()
        current_parent_data_group = None

        if self.currentItem() is not None:
            data_object = self.currentItem().data(0, QtCore.Qt.ItemDataRole.UserRole)
            if isinstance(data_object, DataGroup):
                current_parent_widget_item = self.currentItem()
                current_parent_data_group = data_object

        imported_pair = state_bus.data_cluster.import_source_as_data(
            source_search,
            current_parent_data_group,
            True, # TODO: criar uma opção para deixar a pessoa escolher se ela vai pesquisar os sub-grupos do caminho,
        )

        imported_source_kind, imported_source = imported_pair

        if imported_source_kind.is_file():
            # Distribui os dados importados o grupo selecionado ou dei
            [add_data_item(current_parent_widget_item, data) for data in imported_source]
        else:
            [add_data_group_item_recursive(current_parent_widget_item, data_group) for data_group in imported_source]

        self.setSortingEnabled(True)
        self.sortItems(0, QtCore.Qt.SortOrder.AscendingOrder)