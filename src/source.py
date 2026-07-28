from enum import Enum
from dataclasses import dataclass, astuple
from pathlib import Path
import typing
import os

class SourceKind(Enum):
    FILE = 0,
    FOLDER = 1
      
    def is_file(self) -> bool:
        return self == SourceKind.FILE
    
    def is_folder(self) -> bool:
        return self == SourceKind.FOLDER

"""
Foi utilizado dataclass nessa classe para poder gerar os códigos boilerplate para
garantir a capacidade de desestruturação dos valores ao acessá-los e imutabilidade
dos valores definidos ao criar uma istância.
"""
@dataclass(frozen=True) # Impede que os valores das variáveis sejam mudadas depois da instância ser criada
class Source:
    kind: SourceKind
    path: Path

    # Gera uma tupla quando for iterar o objeto de modo a desestruturá-lo
    def __iter__(self):
        return iter(astuple(self))

"""
Essa classe tem o propósito de limitar os edge-cases na lógica de importação de fontes.
Anteriormente era passado uma lista de caminhos em string e as fontes eram extraidas.
Porém, como é preciso organizar as fontes em grupos de dados, é mais fácil, e menos pro
penso a erros, saber exatamente que tipo de dados esperar de uma caminho de dados.

Tecnicamente, seria abrir mão de uma abordagem agnóstica, mas obter uma capacidade de 
organização e implementação de funcionalidades mais direta.
"""
@dataclass(frozen=True)
class SourceSearch():
    kind: SourceKind
    source_paths: list[Path]

    def __iter__(self):
        return iter(astuple(self))
