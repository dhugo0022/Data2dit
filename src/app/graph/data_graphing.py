from typing import Dict
from functools import partial

from data import Data, DataGroup
from state import state_bus

from PySide6.QtWidgets import QTreeWidgetItem
import  PySide6.QtGui as QtGui
import PySide6.QtCore as QtCore
import pyqtgraph as pg

"""
pxMode=True: This forces PyQtGraph to pre-render the symbols into a single image cache (an atlas) rather than drawing each point as a separate vector piece.
pen=None or width=1: Straying away from standard pen sizes causes heavy drawing bottlenecks in the Qt framework.
useCache=True: Reuses pre-rendered elements.
"""

class DataGraphingLayout(pg.GraphicsLayoutWidget):
    def __init__(self, parent = None):
        super().__init__(parent)

        self.plots: Dict[QTreeWidgetItem, pg.PlotItem.PlotItem] = {}

        state_bus.data_object_double_clicked.connect(self._handle_item_double_clicked)
        state_bus.data_object_clicked.connect(self._handle_item_clicked)


    # Só deve ser excutado para um só dado
    def _plot_data(self, data_item: QTreeWidgetItem, plot_item: pg.PlotItem.PlotItem = None):
        data: Data = data_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        data_plot_item = plot_item if plot_item is not None else self.addPlot()

        # Desativa o menu do plot
        data_plot_item.setMenuEnabled(False)

        # Pega a cor do nome no item referente ao dado para pintar a linha no gráfico, referente ao mesmo dado
        data_color = data_item.foreground(0).color()

        def _handle_curve_clicked(data_item: QTreeWidgetItem, *args):
            data = data_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            data_item.treeWidget().clearSelection()
            data_item.setSelected(True)

        x, y = data.content
        plotted_data_item = data_plot_item.plot(x, y, pen = data_color)

        # Faz com que a curva seja clickável
        plotted_data_item.setCurveClickable(True)

        # Executa um certo comando ao usuário clicar na curva
        plotted_data_item.sigClicked.connect(partial(_handle_curve_clicked, data_item))

        """
        Caso nenhum PlotItem tenha sido especificado, a Data vai ser
        mostrada de forma standalone. Portanto, ela precisa ser 
        registrada no dicionário de gráficos. Isso defere caso ela
        já esteja sendo posta no gráfico de um grupo, já que o gráfico
        do próprio grupo já ser regsitrado.
        """
        if plot_item is None:
            self.plots[data_item] = data_plot_item

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