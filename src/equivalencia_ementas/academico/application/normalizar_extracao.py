from __future__ import annotations

import re
import unicodedata

from equivalencia_ementas.infraestrutura.ia.modelos_extracao import (
    BibliografiaExtraida,
    DisciplinaExtraida,
    DocumentoAcademicoExtraido,
    ObjetivosExtraidos,
)


_EXPRESSOES_AUSENCIA = {
    "nao ha",
    "nao possui",
    "nao se aplica",
    "sem bibliografia",
    "sem informacao",
    "nao informado",
    "nao informada",
    "-",
}


def normalizar_extracao(
    documento: DocumentoAcademicoExtraido,
) -> DocumentoAcademicoExtraido:
    return DocumentoAcademicoExtraido(
        instituicao=normalizar_texto(documento.instituicao),
        curso=normalizar_texto(documento.curso),
        disciplinas=[
            normalizar_disciplina(disciplina)
            for disciplina in documento.disciplinas
        ],
        observacoes_documento=normalizar_lista_textos(
            documento.observacoes_documento
        ),
    )


def normalizar_disciplina(
    disciplina: DisciplinaExtraida,
) -> DisciplinaExtraida:
    return DisciplinaExtraida(
        nome=normalizar_texto_obrigatorio(
            disciplina.nome
        ),
        tipo_ocorrencia=disciplina.tipo_ocorrencia,
        carga_horaria=disciplina.carga_horaria,
        objetivos=ObjetivosExtraidos(
            geral=normalizar_texto(
                disciplina.objetivos.geral
            ),
            especificos=normalizar_texto(
                disciplina.objetivos.especificos
            ),
            nao_classificados=normalizar_texto(
                disciplina.objetivos.nao_classificados
            ),
        ),
        competencias_habilidades=normalizar_texto(
            disciplina.competencias_habilidades
        ),
        ementa=normalizar_texto(
            disciplina.ementa
        ),
        conteudo_programatico=normalizar_texto(
            disciplina.conteudo_programatico
        ),
        bibliografia=BibliografiaExtraida(
            basica=normalizar_texto(
                disciplina.bibliografia.basica
            ),
            complementar=normalizar_texto(
                disciplina.bibliografia.complementar
            ),
            nao_classificada=normalizar_texto(
                disciplina.bibliografia.nao_classificada
            ),
        ),
        paginas_origem=sorted(
            set(
                pagina
                for pagina in disciplina.paginas_origem
                if pagina > 0
            )
        ),
        observacoes=normalizar_lista_textos(
            disciplina.observacoes
        ),
    )


def normalizar_texto(
    valor: str | None,
) -> str | None:
    if valor is None:
        return None

    texto = valor.strip()

    if not texto:
        return None

    texto = re.sub(
        r"[ \t]+",
        " ",
        texto,
    )

    texto = re.sub(
        r"\n[ \t]+",
        "\n",
        texto,
    )

    texto = re.sub(
        r"\n{3,}",
        "\n\n",
        texto,
    )

    if _eh_expressao_ausencia(texto):
        return None

    return texto


def normalizar_texto_obrigatorio(
    valor: str,
) -> str:
    texto = normalizar_texto(valor)

    if texto is None:
        raise ValueError(
            "Nome da disciplina não pode ficar vazio "
            "após a normalização."
        )

    return texto


def normalizar_lista_textos(
    valores: list[str],
) -> list[str]:
    resultado: list[str] = []
    vistos: set[str] = set()

    for valor in valores:
        texto = normalizar_texto(valor)

        if texto is None:
            continue

        chave = _normalizar_para_comparacao(texto)

        if chave in vistos:
            continue

        vistos.add(chave)
        resultado.append(texto)

    return resultado


def _eh_expressao_ausencia(
    texto: str,
) -> bool:
    normalizado = _normalizar_para_comparacao(
        texto
    )

    normalizado = normalizado.rstrip(
        ".:;"
    ).strip()

    if normalizado in _EXPRESSOES_AUSENCIA:
        return True

    finais_de_ausencia = (
        ": nao ha",
        ": nao se aplica",
        ": nao possui",
        ": sem bibliografia",
    )

    return normalizado.endswith(
        finais_de_ausencia
    )


def _normalizar_para_comparacao(
    texto: str,
) -> str:
    texto = unicodedata.normalize(
        "NFKD",
        texto,
    )

    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(
            caractere
        )
    )

    texto = texto.casefold()

    texto = re.sub(
        r"\s+",
        " ",
        texto,
    )

    return texto.strip()