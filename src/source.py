from enum import Enum
from dataclasses import dataclass, astuple
from questionary import Validator, ValidationError
from pathlib import Path
import typing
import os
from data import DATA_EXTENSIONS, DATA_KINDS, Data

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
    path: str

    # Gera uma tupla quando for iterar o objeto de modo a desestruturá-lo
    def __iter__(self):
        return iter(astuple(self))

def generate_sources_from_paths(kind: SourceKind, raw_sources: list[str]):
    if type(kind) == None:
        raise Exception("O tipo de fonte que está sendo convertido não pode ser None.")

    new_sources = map(lambda raw_source: Source(kind, raw_source), raw_sources)
    return new_sources

class SourceKindValidator(Validator):
    def __init__(self, reference_source_kind: SourceKind):
        super().__init__()
        self.reference_source_kind = reference_source_kind

    def validate(self, document):
        
        path_len = len(document.text)
        
        if path_len == 0:
            raise ValidationError(
                message="O caminho da fonte não pode estar vazio",
                cursor_position=path_len,
            )
        
        target_path = Path(document.text)
        
        if not target_path.exists():
            raise ValidationError(
                message="O caminho da fonte não existe",
                cursor_position=path_len,
            )

        if self.reference_source_kind.is_file() and target_path.is_dir():
            raise ValidationError(
                message=f"A fonte {document.text} não é um arquivo, mas sim uma pasta",
                cursor_position=path_len,
            )

        if self.reference_source_kind.is_file() and target_path.suffix[1:] not in DATA_EXTENSIONS:
            raise ValidationError(
                message=f"A fonte {document.text} não possui um formato de arquivo suportado",
                cursor_position=path_len,
            )
        
        if self.reference_source_kind.is_folder() and target_path.is_file():
            raise ValidationError(
                message=f"A fonte {document.text} não é uma pasta, mas sim um arquivo",
                cursor_position=path_len,
            )

class SourceTreeNode():

    def __init__(self, name: str, parent: typing.Self, source: Source, children: dict[str, typing.Self]):
        self.name = name
        self.parent = parent
        self.source = source
        self.children = children

        self.data = None

    @property
    def path(self):
        """Retorna o caminho completo do nó."""
        parts = []
        node = self

        while node.parent is not None:
            parts.append(node.name)
            node = node.parent

        # os.sep = Separador de arquivos padrão do sistema (ex: "/" para linux e "\" para Windows, etc.)
        return os.sep.join(reversed(parts))

    # Gera uma tupla quando for iterar o objeto de modo a desestruturá-lo
    def __iter__(self):
        return iter(astuple(self))

    def has_data(self):
        return self.data is not None
    
    def extract_data(self, kind: str) -> Data:
        if kind not in DATA_KINDS.keys():
            raise Exception(f"Você está tentando extrair os dados com um tipo não suportado: {kind}.")

        data_kind = DATA_KINDS[kind]
        data_path = Path(self.source.path)

        binary_content = data_path.read_bytes()

        self.data = data_kind.extract_data_from_file_content(binary_content)

        return self.data
    
class SourceTree():
    
    def __init__(self, sources: tuple[Source]):
        self.sources = sources
        self.root = SourceTreeNode("root", None, Source(SourceKind.FOLDER, None), {})

    # Procurar por todos os arquivos (cuja a extensão é de um tipo de dado suportado)
    # imediatos dentro da pasta
    def _gather_immediate_node_supported_children(self, node: SourceTreeNode):
        kind, path = node.source

        if not kind.is_folder():
            raise Exception("O nó onde será pesquisado os possiveis sub-nós filhos não é do tipo pasta.")

        wrapped_path = Path(path)

        supported_children_path = [child for child in wrapped_path.rglob("*") if (child.is_file() and child.suffix[1:] in DATA_EXTENSIONS)]

        for supported_child_path in supported_children_path:
            supported_child_path.name
            child_source = Source(SourceKind.FILE, supported_child_path.absolute())
            child_node = SourceTreeNode(supported_child_path.name, node, child_source, {})

            node.children[supported_child_path.name] = child_node

    # Insere um nó em outro, respeitando a ordem dos nos intermediários
    def _insert_child_in_node(self, node: SourceTreeNode, source: Source, expect_last_parent: bool = False):
        kind, path = source
        path_parts = Path(path).parts

        parent = node
        for i, path_part in enumerate(path_parts):
            # Se aquele nó ainda não tiver sido colocado, coloca ele
            if path_part not in parent.children:
                # Cria o nó filho com todas as informações de nome, pai, source e lista de filhos
                child = SourceTreeNode(path_part, parent, source, {})

                # Atualiza o dicinário de filhos do pai com o nó filho que está sendo criado
                parent.children[path_part] = child

                # Se essa nó for do tipo pasta e tiver na última iteração
                if kind.is_folder() and (i == len(path_parts) - 1):
                    self._gather_immediate_node_supported_children(child)

            # Atualiza o pai para o último nó posto ou que já estava lá (e que foi tentado ter sido posto de novo)
            parent = parent.children[path_part]

        if expect_last_parent:
            return parent

    def grow_tree(self):
        """
        Popula a arvore com os devidos nós a partir da lista de todas suas possíveis fontes.
        """

        for source in self.sources:
            self._insert_child_in_node(self.root, source)

    def insert(self, source: Source) -> SourceTreeNode:
        """
        Insere uma fonte avulsa e retorna o nó da fonte adicionada.
        """
        return self._insert_child_in_node(self.root, source, expect_last_parent=True)


    AgnosticPath = str | Source | Path

    def _translate_agnostic_path(self, path: AgnosticPath) -> Path:
        return Path if type(path) is Path else (Path(str) if type(path) is str else Path(path.path))

    def find(self, path: AgnosticPath) -> SourceTreeNode:
        """
        Busca por um nó, pelo caminho especificado, que já existe
        na árvore de nós e retorna ele caso exista.
        """
        parts = self._translate_agnostic_path(path).parts

        node = self.root

        for part in parts:
            if part not in node.children:
                return None
            node = node.children[part]

        return node


    def remove(self, path: AgnosticPath):
        """
        Remove uma fonte a partir do seu caminho de arquivo
        """
        node = self.find(path)

        if node is None:
            return False

        if node.parent is None:
            raise ValueError("Não foi possível encontrar a raiz do nó que você está tentando remover.")

        del node.parent.children[node.name]

        return True

    # ---------------------------------------------------------
    # Caminhamento (DFS)
    # ---------------------------------------------------------
    # def walk(self, node=None):
    #     if node is None:
    #         node = self.root

    #     yield node

    #     for child in node.children.values():
    #         yield from self.walk(child)

    def print(self):
        self._print(self.root, "", True)

    def _print(self, node, prefix, is_last):
        if node != self.root:
            connector = "└── " if is_last else "├── "
            print(prefix + connector + node.name)

        children = list(node.children.values())

        for i, child in enumerate(children):
            last = i == len(children) - 1

            if node == self.root:
                new_prefix = ""
            else:
                new_prefix = prefix + ("    " if is_last else "│   ")

            self._print(child, new_prefix, last) 