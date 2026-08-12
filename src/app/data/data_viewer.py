
from source import SourceSearch
from data import Node, Data, DataGroup
import utils
from state import state_bus
import resources

import PySide6.QtCore as QtCore
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QAbstractItemView
from PySide6.QtGui import QIcon, QColor
 
class DataTreeItem(QTreeWidgetItem):

    """
    Sistema de sortear por tipo de fonte de dado.
    Onde a prioridade seria o grupo de dadso e o resto são os dados
    """
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

        # Intercepta o sinal de fontes pesquisadas
        state_bus.source_searched.connect(self._handle_new_data)

        # Intercepta o sinal de quando o item sofre um double click
        self.itemDoubleClicked.connect(self._handle_item_double_click)
        # Intercepta o sinal de quando o item sofre um clique simples
        self.itemClicked.connect(self._handle_item_click)
        # Intercepta o sinal de quando o item sofre alguma modificação nas suas propriedades
        self.itemChanged.connect(self._handle_item_changed)

    # Desseleciona completamente a seleção prévia caso o usuário clique
    # em um lugar em branco.
    def mousePressEvent(self, event):
        item = self.itemAt(event.position().toPoint())

        if item is None:
            self.clearSelection()
            self.setCurrentItem(None)

        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        key = event.key()
        selected_items = self.selectedItems()

        # Caso o usário tenho apertado delete e tenha um item selecionado
        if key == QtCore.Qt.Key.Key_Delete and len(selected_items) > 0:
            """
            Para impedir que um grupo seja deletado primeiro que seus dados ou subgrupos
            caso todos eles estejam selecionados, só precisaremos verificar se o grupo pai
            de algo que esteja selecionado, também está na lista de remoção
            """
            deletion_list: list[QTreeWidgetItem] = []
            for selected_item in selected_items:

                current_parent = selected_item.parent()
                mark_for_deletion = True

                while current_parent is not None:
                    if current_parent in selected_items:
                        mark_for_deletion = False
                        break

                    current_parent = current_parent.parent()

                if mark_for_deletion:
                    deletion_list.append(selected_item)
            
            for selected_item in deletion_list:
                data_object: Node = selected_item.data(0, QtCore.Qt.ItemDataRole.UserRole)

                if data_object.is_data():
                    state_bus.data_cluster.remove_data(data_object)
                else:
                    state_bus.data_cluster.remove_group(data_object)

                current_selected_item_parent = selected_item.parent()
                if current_selected_item_parent is None:
                    """
                    Caso ele não tenha pai, ele está na raiz do QTreeWidget. Logo, precisamos
                    remover diretamente dela
                    """
                    root_item_index = self.indexOfTopLevelItem(selected_item)
                    self.takeTopLevelItem(root_item_index)
                else:
                    # Caso contrário, só precisamos remover do pai do item selecionado
                    current_selected_item_parent.removeChild(selected_item)

                # Emite o sinal de que o objeto foi deletado
                state_bus.data_object_deleted.emit(selected_item)

        return super().keyPressEvent(event)

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
            target_data = target_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            """
            Mesmo se colocara a flag de impedir que o item receba itens, ainda assim
            esse evento de drop é ativado caso itens sejam jogados acima ou abaixo de
            outros dados. Neste caso, só precisamos pegar o pai do item de dado.
            De outro modo, é um grupo, então só pegamos ele mesmo.
            """
            new_parent = target_data.parent if isinstance(target_data, Data) else target_data

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
    def _handle_item_double_click(self, pressed_widget_item: QTreeWidgetItem, _: int):
        state_bus.data_object_double_clicked.emit(pressed_widget_item)

    # Usado para lidar com ações de clique simples no widget
    def _handle_item_click(self, pressed_widget_item: QTreeWidgetItem, _: int):
        state_bus.data_object_clicked.emit(pressed_widget_item)

    # Caso o item seja modificado de qualquer forma
    def _handle_item_changed(self, changed_widget_item: QTreeWidgetItem, _: int):
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
            data_item.setForeground(0, QColor(utils.generate_random_hex()))
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
        # Sorteia com respeito ao indicador de tipo de sorteio escolhido no header
        self.sortItems(0, self.header().sortIndicatorOrder())