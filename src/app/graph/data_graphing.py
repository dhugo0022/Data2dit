from typing import Dict, cast
from functools import partial

from data import Node, Data, DataGroup
from state import state_bus

from PySide6.QtWidgets import QTreeWidgetItem, QGraphicsSceneHoverEvent
import PySide6.QtGui as QtGui
import PySide6.QtCore as QtCore
import pyqtgraph as pg
import numpy as np

# Referência: https://stackoverflow.com/questions/68847398/hover-tool-for-plots-in-pyqtgraph
class HoverableCurveItem(pg.PlotCurveItem):
    sigCurveHovered = QtCore.Signal(object, object)
    sigCurveNotHovered = QtCore.Signal(object, object)

    def __init__(self, *args, **kwargs):
        super(HoverableCurveItem, self).__init__(*args, **kwargs)
        self.setAcceptHoverEvents(True)

    def hoverEvent(self, event):
        """
        Por algum motivo, quando você entra ou sai rapidamente da tela,
        o atributo _scenePos não está presente. O que leva a um erro.
        Aparentemente a biblioteca terá que corrigir isso. Até lá
        faremos um paliativo.
        """
        if not hasattr(event, "_scenePos"):
            return

        # event.pos() pega a posição relativa ao PlotItem onde a curva está

        if self.acceptHoverEvents():
            if self.mouseShape().contains(event.pos()):
                self.sigCurveHovered.emit(self, event)
            else:
                self.sigCurveNotHovered.emit(self, event)


class DataGraphingLayout(pg.GraphicsLayoutWidget):
    def __init__(self, parent = None):
        super().__init__(parent)

        self.plots: Dict[QTreeWidgetItem, pg.PlotItem.PlotItem] = {}

        state_bus.data_object_double_clicked.connect(self._handle_item_double_clicked)
        state_bus.data_object_clicked.connect(self._handle_item_clicked)
        state_bus.data_object_name_changed.connect(self._handle_item_name_changed)
        state_bus.data_object_deleted.connect(self._handle_item_deleted)


    # Só deve ser excutado para um só dado
    def _plot_data(self, data_item: QTreeWidgetItem, parent_plot_item: pg.PlotItem.PlotItem = None):
        data: Data = data_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        plot_item = parent_plot_item if parent_plot_item is not None else self.addPlot()

        # Desativa o menu do plot
        plot_item.setMenuEnabled(False)

        # Pega a cor do nome no item referente ao dado para pintar a linha no gráfico, referente ao mesmo dado
        data_color = data_item.foreground(0).color()

        color_bright_factor = 140 # 100 = 100% do valor original
        hover_data_color = data_color.lighter(color_bright_factor)

        default_pen_width = 1

        def _handle_curve_hovered(curve_item: HoverableCurveItem, event):
            curve_item.setPen(pg.mkPen(hover_data_color, width = default_pen_width))

        def _handle_curve_uvhovered(curve_item: HoverableCurveItem, event):
            curve_item.setPen(pg.mkPen(data_color, width = default_pen_width))

        def _handle_curve_clicked(data_item: QTreeWidgetItem, *args):
            data_item.treeWidget().clearSelection()
            
            if data_item.parent() is not None and not data_item.parent().isExpanded():
                data_item.parent().setExpanded(True)

            data_item.setSelected(True)
            
        x, y = data.content

        # Coloca o nome do próprio dado para o caso do gráfico de um dado standalone
        if parent_plot_item is None:
            plot_item.setTitle(data.name)

        
        # plotted_data_item = plot_item.plot(x, y, pen = data_color, hoverPen = hover_data_color, hoverable = True)
        plotted_data_item = HoverableCurveItem(x, y, pen = pg.mkPen(data_color, width = default_pen_width))
        plotted_data_item.setClickable(True, width = default_pen_width)
        plotted_data_item.sigCurveHovered.connect(_handle_curve_hovered)
        plotted_data_item.sigCurveNotHovered.connect(_handle_curve_uvhovered)

        # Injeta um QTreeWidgetItem para comparações posteriores. d2d = sufixo da aplicação
        plotted_data_item.d2d_data_item = data_item

        # Executa um certo comando ao usuário clicar na curva
        plotted_data_item.sigClicked.connect(partial(_handle_curve_clicked, data_item))

        # Adiciona a curva ao gráfico
        plot_item.addItem(plotted_data_item)

        """
        Caso nenhum PlotItem tenha sido especificado, a Data vai ser
        mostrada de forma standalone. Portanto, ela precisa ser 
        registrada no dicionário de gráficos. Isso difere ela caso
        já esteja sendo posta no gráfico de um grupo, já que o gráfico
        do próprio grupo já vai ser registrado.
        """
        if parent_plot_item is None:
            self.plots[data_item] = plot_item

    # Só deve ser executado para um grupo de dados
    def _plot_data_group(self, selected_item: QTreeWidgetItem):
        data_group: DataGroup = selected_item.data(0, QtCore.Qt.ItemDataRole.UserRole)

        child_items = [selected_item.child(child_index) for child_index in range(0, selected_item.childCount())]
        data_child_items = [child_item for child_item in child_items if isinstance(child_item.data(0, QtCore.Qt.ItemDataRole.UserRole), Data)]
        group_child_items = [child_item for child_item in child_items if isinstance(child_item.data(0, QtCore.Qt.ItemDataRole.UserRole), DataGroup)]

        # Cria um PlotItem para todos os dados da data_list
        if len(data_child_items) > 0:
            group_plot_item: pg.PlotItem.PlotItem = self.addPlot() 
            group_plot_item.setTitle(data_group.name)

            [self._plot_data(data_child_item, group_plot_item) for data_child_item in data_child_items]

            self.plots[selected_item] = group_plot_item

        # Faz o mesmo para todos os subgrupos
        [self._plot_data_group(group_child_item) for group_child_item in group_child_items]

    def _handle_item_double_clicked(self, selected_item: QTreeWidgetItem):
        data_object = selected_item.data(0, QtCore.Qt.ItemDataRole.UserRole)

        if not isinstance(data_object, Data):
            return
        
        # Limpa todo os gráficos antes de colocar os novos
        self.clear()
        # Limpa o dicionário que guarda o últimos gráficos que foram mostrados
        self.plots.clear()

        self._plot_data(selected_item)

    def _handle_item_clicked(self, selected_item: QTreeWidgetItem):
        data_object: Data | DataGroup = selected_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        
        if not isinstance(data_object, DataGroup):
            return
        
        modifiers = QtGui.QGuiApplication.keyboardModifiers()

        if not (modifiers & QtGui.Qt.KeyboardModifier.AltModifier):
            return

        self.clear()
        self.plots.clear()
        self._plot_data_group(selected_item)

    def _handle_item_name_changed(self, changed_name_item: QTreeWidgetItem):
        """
        Se esse item tiver um gráfico próprio dele, então teremos duas opções:
        - O gráfico de grupo que está mostrando os seus dados
        - O gráfico de um dado standalone que está mostrando seu próprio dado
        Independente do que seja, só precisamos mudar o nome do gráfico
        """
        plot_item = self.plots.get(changed_name_item)

        # Caso não haja nenhum gráfico para aquele item, não precisa mudar
        if plot_item == None:
            return

        # O item retornado no parâmetro da função já é o item atualizado
        plot_item.setTitle(changed_name_item.text(0))

    def _handle_item_deleted(self, deleted_item: QTreeWidgetItem):

        data_object: Data | DataGroup = deleted_item.data(0, QtCore.Qt.ItemDataRole.UserRole)

        if data_object.is_data():

            # Se o dado está sendo mostrado de maneira standalone
            if self.plots.get(deleted_item) is not None:
                self.clear()
                self.plots.clear()
                return

            # A partir daqui, o dado pode estar em um grupo
            for tree_widget_item, plot_item in self.plots.items():
                tree_widget_item_data: Node = tree_widget_item.data(0, QtCore.Qt.ItemDataRole.UserRole)

                """
                Atualmente, isso aqui não pode chegar a ser verdade, já que não foi implementado
                visualização de um standalone e um grupo ainda. Mas já estaremos suportado esse
                caso de antemão
                """
                if tree_widget_item_data.is_data():
                    continue
                
                for plot_item_child in plot_item.listDataItems():
                    data_item = plot_item_child.d2d_data_item # Este é o atributo injetado durante o _plot_data

                    if deleted_item is data_item:
                        plot_item.removeItem(plot_item_child)
                        break
        else:
            group_plot_item = self.plots.get(deleted_item)

            if group_plot_item is None:
                return

            self.removeItem(group_plot_item)
            self.plots.pop(deleted_item)

