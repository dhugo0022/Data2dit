from dataclasses import dataclass
from abc import abstractmethod

import numpy as np
from numpy.typing import NDArray
from scipy import sp

from data import DataContent

@dataclass
class Filter():
    name: str

    @abstractmethod
    def filter(data_content: DataContent) -> DataContent:
        pass


@dataclass
class FilterGroup():
    filters: list[Filter]

    def addFilter(self, filter: Filter):
        self.filters.append(filter)

    def insertFilter(self, index: int, filter: Filter):
        self.filters.insert(index, filter)

    def removeFilter(self, index: int) -> Filter:
        return self.filters.pop(index)

    def run(self, data_content: DataContent) -> DataContent:
        buffer_data = data_content
        i = 0
        while i < len(self.filters):
            current_filter = self.filters[i]
            new_data = current_filter.filter(buffer_data)
            buffer_data = new_data
            i+=1

        return buffer_data

## Filters

@dataclass
class SavitzkyGolayFilter(Filter):
    convolution_width: int
    polyorder: int
    
    def filter(self, data_content):
        y_smooth = sp.signal.savgol_filter(data_content.y, window_length=self.convolution_width, polyorder=self.polyorder)
        return DataContent(data_content.x.copy(), y_smooth)
