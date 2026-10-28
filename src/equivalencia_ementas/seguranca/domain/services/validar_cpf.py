
import re


def normalizar_cpf(cpf: str) -> str:
    return re.sub(r"\D", "", cpf)


def validar_cpf(cpf: str) -> bool:
    if not isinstance(cpf, str):
        return False

    numeros = normalizar_cpf(cpf)

    if len(numeros) != 11:
        return False

    if len(set(numeros)) == 1:
        return False

    for quantidade in (9, 10):
        soma = sum(
            int(numeros[indice]) * (quantidade + 1 - indice)
            for indice in range(quantidade)
        )

        resto = (soma * 10) % 11
        digito = 0 if resto == 10 else resto

        if digito != int(numeros[quantidade]):
            return False

    return True
