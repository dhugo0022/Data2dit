import numpy as np
from numpy.typing import NDArray
from dataclasses import dataclass, astuple

@dataclass(frozen=True)
class Data:
    x: NDArray[np.float64]
    y: NDArray[np.float64]

    def __iter__(self):
        return iter(astuple(self))
    
class DataKind():

    def __init__(self, name: str, file_extension: str):
        self.name = name
        self.file_extension = file_extension

    def extract_data_from_file_content(content: bytes) -> Data:
        pass

class XY_DataKind(DataKind):
    def __init__(self):
        super().__init__("XY", "txt")

    def extract_data_from_file_content(self, content: bytes):
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
        
        return Data(x_axis, y_axis)
    
class CSV_DataKind(DataKind):
    def __init__(self):
        super().__init__("CSV", "csv")

DATA_KINDS = {
    "XY": XY_DataKind(),
    "CSV": CSV_DataKind(),
}

DATA_EXTENSIONS = (*map(lambda data_kind: data_kind.file_extension, DATA_KINDS.values()),)

QT_FILE_DIALOG_NAME_FILTER = " ".join(map(lambda extension: f"*.{extension}", DATA_EXTENSIONS))