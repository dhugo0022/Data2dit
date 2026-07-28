import re

"""
Cria uma chave especial, separando números de letras, para
possiblitar uma comparação de "maior que" e "menor que"
mais precisa e que respeita as diferencas de número no nome
"""
def natural_key(text: str):
    return [
        int(part) if part.isdigit() else part.casefold()
        for part in re.split(r"(\d+)", text)
    ]