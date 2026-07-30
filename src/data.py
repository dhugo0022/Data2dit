import numpy as np
from numpy.typing import NDArray
from dataclasses import dataclass, astuple, field
from pathlib import Path

from source import Source, SourceSearch, SourceKind
@dataclass(frozen=True)
class DataContent:
    x: NDArray[np.float64]
    y: NDArray[np.float64]

    def __iter__(self):
        return iter(astuple(self))

class DataExtractor():

    def __init__(self, name: str, file_extension: str):
        self.name = name
        self.file_extension = file_extension

    def extract_data(content: bytes) -> list[NDArray[np.float64]]:
        pass

class XY_DataExtractor(DataExtractor):
    def __init__(self):
        super().__init__("XY", "txt")

    def extract_data(self, content: bytes):
        xy_data = content.decode("utf-8")

        # Se houver ocorrências de números com "," para separar decimais, converte para "."
        xy_data = xy_data.replace(",", ".")

        split_xy_data = xy_data.splitlines()
        axis_length = len(split_xy_data)

        x_axis = np.zeros(axis_length)
        y_axis = np.zeros(axis_length)

        for index, line in enumerate(xy_data.splitlines()):
            x, y = line.split("\u0009") # Esse código unicode é do Tab[    ]

            x_axis[index] = np.float64(x)
            y_axis[index] = np.float64(y)
        
        return DataContent(x_axis, y_axis)
    
DATA_EXTRACTORS = {
    "XY": XY_DataExtractor(),
}

DATA_EXTENSIONS = (*map(lambda data_extractor: data_extractor.file_extension, DATA_EXTRACTORS.values()),)

DATA_EXTRACTORS_BY_EXTENSION = dict(zip(
    DATA_EXTENSIONS,
    DATA_EXTRACTORS.values()
))

QT_FILE_DIALOG_NAME_FILTER = " ".join(map(lambda extension: f"*.{extension}", DATA_EXTENSIONS))

@dataclass
class Node():
    name: str
    parent: DataGroup | None = None

    def set_name(self, new_name: str):
        self.name = new_name

    def set_parent(self, new_parent: DataGroup):
        self.parent = new_parent
        
@dataclass
class Data(Node):
    source: Source | None = None
    content: DataContent | None = None

    def extract_content(self) -> bool:
        """
        Retorna verdadeiro se os dados foram extraídos da fonte e convertidos com sucesso
        e false, caso contrário.
        """
        path = self.source.path
        
        if not path.exists():
            return False
        
        content = path.read_bytes()

        source_extension = path.suffix[1:]
        data_extractor = DATA_EXTRACTORS_BY_EXTENSION[source_extension]

        if data_extractor is None:
            return False

        self.content = data_extractor.extract_data(content)
        return True

@dataclass
class DataGroup(Node):
    data_list: list[Data] = field(default_factory=list)
    groups: list[DataGroup] = field(default_factory=list)

    def has_data(self):
        return len(self.data_list) > 0

    def extract_data(self, recursive: bool = False):
        """
        Executa a extração do conteúdo de todos os estados que estão na lista de dados dele.
        Caso recursive esteja ativado, fará o mesmo para todos os seu sub grupos de maneira
        recursiva.
        """
        all([data.extract_content() for data in self.data_list])

        if recursive:
            [sub_group.extract_data(recursive) for sub_group in self.groups]

@dataclass
class DataCluster:
    root_groups: list[DataGroup] = field(default_factory=list, init=False, )
    ungrouped_data: list[DataContent] = field(default_factory=list, init=False)

    def add_group(self, group: DataGroup, parent: DataGroup | None = None):
        if group.parent is not None:
            raise ValueError("O grupo que você está tentando adicionar já possui um pai.")
        
        if parent is None:
            self.root_groups.append(group)
        else:
            parent.groups.append(group)
            group.parent = parent
        
    def add_data(self, data: Data, parent: DataGroup | None = None):
        if data.parent is not None:
            raise ValueError("O dado que você está tentando adicionar já possui um pai.")
          
        if parent is None:
            self.ungrouped_data.append(data)
        else:
            parent.data_list.append(data)
            data.parent = parent

    def move_group(self, group: DataGroup, destination: DataGroup | None):
        if destination is group:
            return ValueError("Você não pode mover um grupo para ele mesmo.")

        if destination is not None and self._is_descendant(destination, group):
            return ValueError("Você não pode mover um grupo para um de seus descendentes.")

        # Remove do pai antigo

        if group.parent is None:
            self.root_groups.remove(group)
        else:
            group.parent.groups.remove(group)

        # Adiciona ao pai de destino

        group.parent = destination

        if destination is None:
            self.root_groups.append(group)
        else:
            destination.groups.append(group)

    def move_data(self, data: Data, destination: DataGroup | None):
        if data.parent is None:
            self.ungrouped_data.remove(data)
        else:
            data.parent.data_list.remove(data)

        data.parent = destination

        if destination is None:
            self.ungrouped_data.append(data)
        else:
            destination.data_list.append(data)
        
    def remove_data(self, data: Data):
        if data.parent is None:
            self.ungrouped_data.remove(data)
        else:
            data.parent.data_list.remove(data)

        data.parent = None
            
    def remove_group(self, group: DataGroup):
        for subgroups in list(group.groups):
            self.remove_group(subgroups)

        for data in list(group.data_list):
            self.remove_data(data)

        if group.parent is None:
            self.root_groups.remove(group)
        else:
            group.parent.groups.remove(group)

        group.parent = None

    def rename_group(self, group: DataGroup, new_name: str):
        group.name = new_name

    def rename_data(self, data: Data, new_name: str):
        data.name = new_name

    def _is_descendant(self, group: DataGroup, ancestor: DataGroup,) -> bool:
        current = group.parent

        while current is not None:

            if current is ancestor:
                return True

            current = current.parent

        return False

    def _insert_imported_data(self, file_path: Path, parent: DataGroup | None):
        path_extension = file_path.suffix[1:]
        
        # Tecnicamente, com o seletor de arquivos funcionando corretamente, esse erro nem deve ser alcançado.
        if path_extension not in DATA_EXTENSIONS:
            raise ValueError(f"O formato \"{path_extension}\" do arquivo não é suportado: ${file_path.absolute}")

        sanitized_data_name = file_path.name.removesuffix(file_path.suffix)
        data = Data(sanitized_data_name, source = Source(SourceKind.FILE, file_path))
        data.extract_content()
        self.add_data(data, parent)

        return data
        

    def _insert_imported_data_group(self, group_path: Path, parent: DataGroup, recursive_group_insert: bool) -> DataGroup:
        data_group = DataGroup(group_path.name)
        self.add_group(data_group, parent)
        
        # Pega todos os descendentes diretos da pasta, seja arquivo ou outras sub-pastas
        sub_entities = list(group_path.glob("*"))

        # Pega todas os arquivos que são descendentes diretos da pasta e que estão com a extensões suportadas
        direct_file_paths = [file_path for file_path in sub_entities if (file_path.is_file() and (file_path.suffix[1:] in DATA_EXTENSIONS))]
        [self._insert_imported_data(file_path, data_group) for file_path in direct_file_paths]
        
        if recursive_group_insert:
            sub_folder_paths = [sub_folder for sub_folder in sub_entities if sub_folder.is_dir()]

            [self._insert_imported_data_group(sub_folder_path, data_group, recursive_group_insert) for sub_folder_path in sub_folder_paths]

        return data_group
    
    def import_source_as_data(
        self,
        source_search: SourceSearch,
        parent: DataGroup | None = None,
        recursive_group_insert: bool = False,
   
    ) -> tuple[SourceKind, list[Data] | list[DataGroup]]:
        kind, source_paths = source_search
        
        if kind.is_file():
            inserted_data = [self._insert_imported_data(source_path, parent) for source_path in source_paths]
            return (kind, inserted_data)
        else:
            inserted_groups = [self._insert_imported_data_group(source_path, parent, recursive_group_insert) for source_path in source_paths]
            return (kind, inserted_groups)
