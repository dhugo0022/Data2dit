from abc import abstractmethod
import utils

import PySide6.QtCore as QtCore
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QAbstractItemView
from PySide6.QtGui import QIcon, QColor

class TreeAdapter[T]:

    @abstractmethod
    def name(self, obj: T) -> str:
        pass

    @abstractmethod
    def children(self, obj: T) -> list[T]:
        pass

    @abstractmethod
    def parent(self, obj: T) -> T | None:
        pass

    @abstractmethod
    def is_container(self, obj: T) -> bool:
        pass

    @abstractmethod
    def move(self, obj: T, new_parent: T | None) -> None:
        pass

    @abstractmethod
    def remove(self, obj: T) -> None:
        pass

    @abstractmethod
    def rename(self, obj: T, name: str) -> None:
        pass

class TreeAppearance[T]:

    @abstractmethod
    def icon(self, obj: T, adapter: TreeAdapter[T]) -> QIcon | None:
        pass

    @abstractmethod
    def foreground(self, obj: T, adapter: TreeAdapter[T]) -> QColor | None:
        pass

    @abstractmethod
    def configure_item(self, item: AgnosticTreeItem, obj: T, adapter: TreeAdapter[T]) -> None:
        pass


class AgnosticTreeItem(QTreeWidgetItem):

    def __lt__(self, other):
        self_obj = self.data(0,QtCore.Qt.ItemDataRole.UserRole,)

        other_obj = other.data(0, QtCore.Qt.ItemDataRole.UserRole,)

        # Esse adaptador é definido durante a criação do widget AbstractTreeViewer
        adapter = self.treeWidget().adapter

        self_key = (not adapter.is_container(self_obj), utils.natural_key(adapter.name(self_obj)))

        other_key = (not adapter.is_container(other_obj), utils.natural_key(adapter.name(other_obj)))

        return self_key < other_key

class AbstractTreeViewer[T](QTreeWidget):

    def __init__(
            self,
            adapter: TreeAdapter[T],
            appearance: TreeAppearance[T],
            parent = None,
            header_label: str = None,
            # Signals padrões
            item_clicked_signal: QtCore.SignalInstance = None,
            item_double_clicked_signal: QtCore.SignalInstance = None,
            item_name_changed_signal: QtCore.SignalInstance = None,
            item_deleted_signal: QtCore.SignalInstance = None,
            item_moved_signal: QtCore.SignalInstance = None,
        ):
        super().__init__(parent)

        self.adapter = adapter
        self.appearance = appearance

        self.setHeaderLabel(header_label)

        self.item_clicked_signal = item_clicked_signal
        self.item_double_clicked_signal = item_double_clicked_signal
        self.item_name_changed_signal = item_name_changed_signal
        self.item_deleted_signal = item_deleted_signal
        self.item_moved_signal = item_moved_signal

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

        # Intercepta o sinal de quando o item sofre um clique simples
        self.itemClicked.connect(self._handle_item_click)
        # Intercepta o sinal de quando o item sofre um double click
        self.itemDoubleClicked.connect(self._handle_item_double_click)
        # Intercepta o sinal de quando o item sofre alguma modificação nas suas propriedades
        self.itemChanged.connect(self._handle_item_changed)

    def create_item(self, parent: AgnosticTreeItem | None, obj: T) -> AgnosticTreeItem:
        item = AgnosticTreeItem(parent, [self.adapter.name(obj)])

        item.setData(0, QtCore.Qt.ItemDataRole.UserRole, obj)

        icon = self.appearance.icon(obj, self.adapter)

        if icon is not None:
            item.setIcon(0, icon)

        foreground = self.appearance.foreground(obj, self.adapter)

        if foreground is not None:
            item.setForeground(0, foreground)
        
        self.appearance.configure_item(item, obj, self.adapter)

        return item

    def populate_item(self, item: AgnosticTreeItem, obj: T):
        for child in self.adapter.children(obj):
            child_item = self.create_item(item, child)

            if self.adapter.is_container(child):
                self.populate_item(child_item, child)

   
    # Desseleciona completamente a seleção prévia caso o usuário clique
    # em um lugar em branco.
    def mousePressEvent(self, event):
        try:
            item = self.itemAt(event.position().toPoint())
            
            if item is None:
                self.clearSelection()
                self.setCurrentItem(None)
            
            return super().mousePressEvent(event)
        except Exception as e:
            print(f"Houve um erro no click do mouse no painel de seleção: {e}")
       
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
                obj = selected_item.data(0, QtCore.Qt.ItemDataRole.UserRole)

                self.adapter.remove(obj)
                
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
                if self.item_deleted_signal is not None:
                    self.item_deleted_signal.emit(selected_item)
                # state_bus.data_object_deleted.emit(selected_item)

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

        new_parent = None

        if target_item is not None:
            obj = target_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            """
            Mesmo se colocara a flag de impedir que o item receba itens, ainda assim
            esse evento de drop é ativado caso itens sejam jogados acima ou abaixo de
            outros dados. Neste caso, só precisamos pegar o pai do item de dado.
            De outro modo, é um grupo, então só pegamos ele mesmo.
            """
            new_parent = obj if self.adapter.is_container(obj) else obj.parent

        """
        Deixa o Qt processar o novo pai do QTreeWidgetItem e depois nós lidamos com
        a informação atualizada. Isso é necessário por conta do tratameno do Signal
        de mudança de item, já que necessário ter a informação do pai atualizada
        ao mexer no sinal.
        """
        super().dropEvent(event)

        """
        Mesmo que tanto DataGroup, quanto Data, sejam descendentes de Node, ainda assim
        é precisso lidar com os dados de maneira separada. Especialmente porque é preciso
        acessar outras variáveis, além daquela que se refere ao pai, durante a mudança.
        """
        for selected_item in selected_items:
            obj = selected_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            self.adapter.move(obj, new_parent)

            if self.item_moved_signal is not None:
                self.item_moved_signal.emit(selected_item)


    # Usado para lidar com ações de clique simples no widget
    def _handle_item_click(self, pressed_widget_item: QTreeWidgetItem, _: int):
        if self.item_clicked_signal is not None:
            self.item_clicked_signal.emit(pressed_widget_item)
        # state_bus.data_object_clicked.emit(pressed_widget_item)

    # Usado para lidar com ações de clique duplo no widget
    def _handle_item_double_click(self, pressed_widget_item: QTreeWidgetItem, _: int):
        if self.item_double_clicked_signal is not None:
            self.item_double_clicked_signal.emit(pressed_widget_item)
        # state_bus.data_object_double_clicked.emit(pressed_widget_item)

    # Caso o item seja modificado de qualquer forma
    def _handle_item_changed(self, changed_widget_item: QTreeWidgetItem, _: int):
        changed_item_name = changed_widget_item.text(0)
        obj = changed_widget_item.data(0, QtCore.Qt.ItemDataRole.UserRole)

        # Verificação para caso o nome tenha mudado
        old_name = self.adapter.name(obj)
        if old_name != changed_item_name: # Quer dizer que o nome mudou
            """
            Como Data e DataObject são subclasses de Node, não há perigo
            simplesmente chamar a função de mudar de nome. Já que esta
            função é definida no próprio escopo de Node
            """
            self.adapter.rename(obj, changed_item_name)

            if self.item_name_changed_signal is not None:
                self.item_name_changed_signal.emit(changed_widget_item)
            # state_bus.data_object_name_changed.emit(changed_widget_item)

