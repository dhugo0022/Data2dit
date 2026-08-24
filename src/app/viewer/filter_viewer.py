from app.viewer.abstract_viewer import AbstractTreeViewer, TreeAdapter, TreeAppearance
from filter import Filter

class FilterTreeAdapter(TreeAdapter[Filter]):
    def __init__(self):
        super().__init__()

    

class FilterTreeView(AbstractTreeViewer):

    def __init__():
        super().__init__(
            adapter, 
            appearance, 
            parent, 
            header_label, 
            item_clicked_signal, 
            item_double_clicked_signal, 
            item_name_changed_signal, 
            item_deleted_signal, 
            item_moved_signal
        )