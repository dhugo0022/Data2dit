from source import Source, SourceKind, SourceKindValidator
import questionary
 
def ask_for_source_path() -> tuple[Source]:
    """
    Cria um prompt para requerer do usuário o caminho para uma fonte de dados.

    Returns:
        source_result (Source): um objeto contendo o tipo e o caminho da fonte escolhida.
    """

    sources = []

    selecting = True

    while selecting:
        source_kind = questionary.select(
            "A fonte que você quer adicionar é um arquivo ou uma pasta?",
            choices = [
                questionary.Choice("Arquivo", SourceKind.FILE),
                questionary.Choice("Pasta", SourceKind.FOLDER),
            ]
        ).ask()

        source_path = questionary.path(
            "Selecione o caminho para o tipo de fonte escolhida: ",
            validate=SourceKindValidator(source_kind)
        ).ask()

        sources.append(Source(source_kind, source_path))

        selecting = questionary.select(
            "Você ainda quer continuar selecionando fontes?",
            choices = [
                questionary.Choice("Sim", True),
                questionary.Choice("Não", False),
            ]
        ).ask()

    # Converte o resultado obtido para uma tuple e retorna o valor
    return (*sources,)