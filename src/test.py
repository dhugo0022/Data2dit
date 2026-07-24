from prompt import ask_for_source_path
from source import SourceTree, Source, SourceKind
from app import run_application

def test():
    # selected_source_list =  ask_for_source_path()

    # source_tree = SourceTree([Source(SourceKind.FOLDER, "/home/alisson/Downloads/em_h20/Export20%/")])
    # source_tree.grow_tree()
    # source_tree.print()

    # first_folder_source = [source for source in source_tree.sources if source.kind.is_folder()].pop(0)
    # tree_node = source_tree.find(first_folder_source)

    # data_nodes = (*tree_node.children.values(),)
    # [data_node.extract_data("XY") for data_node in data_nodes]

    run_application()
    
if __name__ == "__main__":
    test()