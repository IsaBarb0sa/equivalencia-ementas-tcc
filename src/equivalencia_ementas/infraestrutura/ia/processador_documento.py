from __future__ import annotations

import re
import tempfile
import unicodedata
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from equivalencia_ementas.infraestrutura.ia.cliente_gemini import (
    ExtratorGemini,
)
from equivalencia_ementas.infraestrutura.ia.modelos_extracao import (
    BibliografiaExtraida,
    CargaHorariaExtraida,
    DisciplinaExtraida,
    DocumentoAcademicoExtraido,
    ObjetivosExtraidos,
)


class ProcessadorDocumentoIA:
    def __init__(
        self,
        extrator: ExtratorGemini,
        tamanho_bloco: int = 25,
        sobreposicao: int = 5,
    ) -> None:
        if tamanho_bloco <= 0:
            raise ValueError("tamanho_bloco deve ser maior que zero.")

        if sobreposicao < 0:
            raise ValueError("sobreposicao não pode ser negativa.")

        if sobreposicao >= tamanho_bloco:
            raise ValueError(
                "sobreposicao deve ser menor que tamanho_bloco."
            )

        self._extrator = extrator
        self._tamanho_bloco = tamanho_bloco
        self._sobreposicao = sobreposicao

    def processar(
        self,
        caminho_pdf: Path,
    ) -> DocumentoAcademicoExtraido:
        caminho_pdf = Path(caminho_pdf)

        if not caminho_pdf.exists():
            raise FileNotFoundError(
                f"Arquivo não encontrado: {caminho_pdf}"
            )

        reader = PdfReader(str(caminho_pdf))
        total_paginas = len(reader.pages)

        print(f"Total de páginas: {total_paginas}")
        print(
            f"Blocos de {self._tamanho_bloco} páginas "
            f"com sobreposição de {self._sobreposicao}."
        )
        print()

        resultados: list[DocumentoAcademicoExtraido] = []

        with tempfile.TemporaryDirectory(
            prefix="ementas_ia_"
        ) as diretorio_temp:

            pasta_temp = Path(diretorio_temp)

            blocos = self._gerar_blocos(total_paginas)

            total_blocos = len(blocos)

            for indice, (inicio, fim) in enumerate(
                blocos,
                start=1,
            ):
                print(
                    f"[{indice}/{total_blocos}] "
                    f"Processando páginas "
                    f"{inicio + 1}-{fim}..."
                )

                caminho_bloco = (
                    pasta_temp
                    / f"bloco_{inicio + 1}_{fim}.pdf"
                )

                self._criar_pdf_bloco(
                    reader=reader,
                    inicio=inicio,
                    fim=fim,
                    destino=caminho_bloco,
                )

                resultado = self._extrator.extrair(
                    caminho_bloco
                )

                self._corrigir_paginas(
                    resultado=resultado,
                    deslocamento=inicio,
                )

                resultados.append(resultado)

                print(
                    f"    Disciplinas encontradas: "
                    f"{len(resultado.disciplinas)}"
                )
                print()

        return self._consolidar(resultados)

    def _gerar_blocos(
        self,
        total_paginas: int,
    ) -> list[tuple[int, int]]:
        blocos: list[tuple[int, int]] = []

        passo = (
            self._tamanho_bloco
            - self._sobreposicao
        )

        inicio = 0

        while inicio < total_paginas:
            fim = min(
                inicio + self._tamanho_bloco,
                total_paginas,
            )

            blocos.append((inicio, fim))

            if fim == total_paginas:
                break

            inicio += passo

        return blocos

    @staticmethod
    def _criar_pdf_bloco(
        reader: PdfReader,
        inicio: int,
        fim: int,
        destino: Path,
    ) -> None:
        writer = PdfWriter()

        for numero_pagina in range(inicio, fim):
            writer.add_page(
                reader.pages[numero_pagina]
            )

        with destino.open("wb") as arquivo:
            writer.write(arquivo)

    @staticmethod
    def _corrigir_paginas(
        resultado: DocumentoAcademicoExtraido,
        deslocamento: int,
    ) -> None:
        for disciplina in resultado.disciplinas:
            disciplina.paginas_origem = sorted(
                {
                    pagina + deslocamento
                    for pagina in disciplina.paginas_origem
                    if pagina > 0
                }
            )

    def _consolidar(
        self,
        resultados: list[DocumentoAcademicoExtraido],
    ) -> DocumentoAcademicoExtraido:

        instituicao = self._primeiro_texto(
            resultado.instituicao
            for resultado in resultados
        )

        curso = self._primeiro_texto(
            resultado.curso
            for resultado in resultados
        )

        disciplinas_por_chave: dict[
            str,
            DisciplinaExtraida,
        ] = {}

        observacoes_documento: list[str] = []

        for resultado in resultados:

            for observacao in (
                resultado.observacoes_documento
            ):
                if observacao not in observacoes_documento:
                    observacoes_documento.append(
                        observacao
                    )

            for disciplina in resultado.disciplinas:

                chave = self._normalizar_nome(
                    disciplina.nome
                )

                existente = disciplinas_por_chave.get(
                    chave
                )

                if existente is None:
                    disciplinas_por_chave[chave] = disciplina
                    continue

                disciplinas_por_chave[chave] = (
                    self._mesclar_disciplinas(
                        existente,
                        disciplina,
                    )
                )

        disciplinas = list(
            disciplinas_por_chave.values()
        )

        disciplinas.sort(
            key=lambda d: (
                min(d.paginas_origem)
                if d.paginas_origem
                else 999999,
                d.nome.casefold(),
            )
        )

        return DocumentoAcademicoExtraido(
            instituicao=instituicao,
            curso=curso,
            disciplinas=disciplinas,
            observacoes_documento=observacoes_documento,
        )

    @staticmethod
    def _normalizar_nome(nome: str) -> str:
        texto = unicodedata.normalize(
            "NFKD",
            nome,
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
            r"[^a-z0-9]+",
            " ",
            texto,
        )

        return " ".join(
            texto.split()
        )

    def _mesclar_disciplinas(
        self,
        atual: DisciplinaExtraida,
        nova: DisciplinaExtraida,
    ) -> DisciplinaExtraida:

        return DisciplinaExtraida(
            nome=self._preferir_texto(
                atual.nome,
                nova.nome,
            ),

            carga_horaria=self._mesclar_carga_horaria(
                atual.carga_horaria,
                nova.carga_horaria,
            ),

            objetivos=self._mesclar_objetivos(
                atual.objetivos,
                nova.objetivos,
            ),

            competencias_habilidades=self._preferir_texto(
                atual.competencias_habilidades,
                nova.competencias_habilidades,
            ),

            ementa=self._preferir_texto(
                atual.ementa,
                nova.ementa,
            ),

            conteudo_programatico=self._preferir_texto(
                atual.conteudo_programatico,
                nova.conteudo_programatico,
            ),

            bibliografia=self._mesclar_bibliografia(
                atual.bibliografia,
                nova.bibliografia,
            ),

            paginas_origem=sorted(
                set(
                    atual.paginas_origem
                    + nova.paginas_origem
                )
            ),

            observacoes=self._mesclar_listas(
                atual.observacoes,
                nova.observacoes,
            ),
        )

    @staticmethod
    def _mesclar_carga_horaria(
        atual: CargaHorariaExtraida,
        nova: CargaHorariaExtraida,
    ) -> CargaHorariaExtraida:

        return CargaHorariaExtraida(
            total=(
                atual.total
                if atual.total is not None
                else nova.total
            ),
            teorica=(
                atual.teorica
                if atual.teorica is not None
                else nova.teorica
            ),
            pratica=(
                atual.pratica
                if atual.pratica is not None
                else nova.pratica
            ),
            unidade=(
                atual.unidade
                if atual.unidade
                else nova.unidade
            ),
            duracao_hora_aula_minutos=(
                atual.duracao_hora_aula_minutos
                if atual.duracao_hora_aula_minutos
                is not None
                else nova.duracao_hora_aula_minutos
            ),
        )

    def _mesclar_objetivos(
        self,
        atual: ObjetivosExtraidos,
        nova: ObjetivosExtraidos,
    ) -> ObjetivosExtraidos:

        return ObjetivosExtraidos(
            geral=self._preferir_texto(
                atual.geral,
                nova.geral,
            ),
            especificos=self._preferir_texto(
                atual.especificos,
                nova.especificos,
            ),
            nao_classificados=self._preferir_texto(
                atual.nao_classificados,
                nova.nao_classificados,
            ),
        )

    def _mesclar_bibliografia(
        self,
        atual: BibliografiaExtraida,
        nova: BibliografiaExtraida,
    ) -> BibliografiaExtraida:

        return BibliografiaExtraida(
            basica=self._preferir_texto(
                atual.basica,
                nova.basica,
            ),
            complementar=self._preferir_texto(
                atual.complementar,
                nova.complementar,
            ),
            nao_classificada=self._preferir_texto(
                atual.nao_classificada,
                nova.nao_classificada,
            ),
        )

    @staticmethod
    def _preferir_texto(
        atual: str | None,
        novo: str | None,
    ) -> str | None:

        if not atual:
            return novo

        if not novo:
            return atual

        # Normalmente o texto maior contém
        # a versão mais completa do campo.
        if len(novo.strip()) > len(atual.strip()):
            return novo

        return atual

    @staticmethod
    def _mesclar_listas(
        atual: list[str],
        nova: list[str],
    ) -> list[str]:

        resultado: list[str] = []

        for item in atual + nova:
            if item not in resultado:
                resultado.append(item)

        return resultado

    @staticmethod
    def _primeiro_texto(
        valores,
    ) -> str | None:

        for valor in valores:
            if valor:
                return valor

        return None