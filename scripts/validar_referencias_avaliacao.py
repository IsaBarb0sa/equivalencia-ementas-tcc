from __future__ import annotations

import json
from pathlib import Path

from equivalencia_ementas.equivalencia.application.preparar_ementas import (
    preparar_disciplinas_json,
)
from equivalencia_ementas.equivalencia.application.preparar_trechos import (
    preparar_trechos,
)
from equivalencia_ementas.equivalencia.infrastructure.ia.sentence_transformer import (
    GeradorSentenceTransformer,
)


RAIZ_PROJETO = Path(__file__).resolve().parents[1]

ARQUIVO_REFERENCIAS = (
    RAIZ_PROJETO
    / "tests"
    / "equivalencia"
    / "dados_avaliacao"
    / "referencias_v1.json"
)


def carregar_referencias():
    with ARQUIVO_REFERENCIAS.open(
        "r",
        encoding="utf-8",
    ) as arquivo:
        dados = json.load(arquivo)

    if not isinstance(dados, dict):
        raise ValueError(
            "O arquivo de referências deve conter um objeto JSON."
        )

    referencias = dados.get("referencias")

    if not isinstance(referencias, list):
        raise ValueError(
            "O campo 'referencias' deve conter uma lista."
        )

    return referencias


def localizar_disciplina(disciplinas, nome):
    encontradas = [
        disciplina
        for disciplina in disciplinas
        if disciplina.nome.casefold().strip()
        == nome.casefold().strip()
    ]

    if len(encontradas) != 1:
        raise ValueError(
            f"Esperada uma disciplina chamada '{nome}', "
            f"mas foram encontradas {len(encontradas)}."
        )

    return encontradas[0]


def localizar_trecho(trechos, secao, texto):
    encontrados = [
        trecho
        for trecho in trechos
        if trecho.secao == secao
        and trecho.texto.strip() == texto.strip()
    ]

    if len(encontrados) != 1:
        raise ValueError(
            f"Esperado um trecho único na seção '{secao}', "
            f"mas foram encontrados {len(encontrados)}.\n"
            f"Texto procurado: {texto}"
        )

    return encontrados[0]


def validar_lado(
    dados_lado,
    gerador,
    cache,
):
    caminho = RAIZ_PROJETO / dados_lado["arquivo"]

    if not caminho.is_file():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {caminho}"
        )

    chave_documento = str(caminho.resolve())

    if chave_documento not in cache:
        cache[chave_documento] = preparar_disciplinas_json(
            caminho
        )

    disciplinas = cache[chave_documento]

    disciplina = localizar_disciplina(
        disciplinas,
        dados_lado["disciplina"],
    )

    chave_trechos = (
        chave_documento,
        dados_lado["disciplina"],
    )

    if chave_trechos not in cache:
        cache[chave_trechos] = preparar_trechos(
            disciplina,
            gerador.contar_tokens,
            gerador.limite_tokens,
        )

    trechos = cache[chave_trechos]

    return localizar_trecho(
        trechos,
        dados_lado["secao"],
        dados_lado["texto"],
    )


def main():
    referencias = carregar_referencias()

    gerador = GeradorSentenceTransformer()

    cache = {}

    aprovadas = 0
    problemas = 0
    ids_encontrados = set()

    print("\nVALIDAÇÃO DAS REFERÊNCIAS ACADÊMICAS")
    print("=" * 65)

    for referencia in referencias:
        identificador = referencia.get("id", "SEM_ID")

        print(f"\nReferência: {identificador}")

        try:
            if identificador in ids_encontrados:
                raise ValueError(
                    f"Identificador duplicado: {identificador}"
                )

            ids_encontrados.add(identificador)

            origem = validar_lado(
                referencia["origem"],
                gerador,
                cache,
            )

            destino = validar_lado(
                referencia["destino"],
                gerador,
                cache,
            )

            print("Status: OK")
            print(f"Origem: {origem.texto}")
            print(f"Destino: {destino.texto}")

            aprovadas += 1

        except (
            KeyError,
            TypeError,
            ValueError,
            FileNotFoundError,
        ) as erro:
            problemas += 1

            print("Status: PROBLEMA")
            print(f"Motivo: {erro}")

    print("\n" + "=" * 65)
    print(f"Total de referências: {len(referencias)}")
    print(f"Referências válidas: {aprovadas}")
    print(f"Referências com problemas: {problemas}")
    print("=" * 65)

    if problemas:
        raise SystemExit(1)


if __name__ == "__main__":
    main()