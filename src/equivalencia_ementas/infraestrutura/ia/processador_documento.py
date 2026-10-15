from __future__ import annotations

import hashlib
import json
import re
import tempfile
import unicodedata
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from equivalencia_ementas.infraestrutura.ia.cliente_gemini import ExtratorGemini

from equivalencia_ementas.infraestrutura.ia.modelos_extracao import (
    BibliografiaExtraida,
    CargaHorariaExtraida,
    DisciplinaExtraida,
    DocumentoAcademicoExtraido,
    ObjetivosExtraidos,
    TipoOcorrenciaDisciplina,
)

VERSAO_CACHE_GEMINI = "12"

class ProcessadorDocumentoIA:
    def __init__(
        self,
        extrator: ExtratorGemini,
        tamanho_bloco: int = 25,
        sobreposicao: int = 5,
        pasta_cache: Path = Path("data/cache_gemini_blocos"),
    ) -> None:
        if tamanho_bloco <= 0:
            raise ValueError(
                "tamanho_bloco deve ser maior que zero."
            )

        if sobreposicao < 0:
            raise ValueError(
                "sobreposicao não pode ser negativa."
            )

        if sobreposicao >= tamanho_bloco:
            raise ValueError(
                "sobreposicao deve ser menor que tamanho_bloco."
            )

        self._extrator = extrator
        self._tamanho_bloco = tamanho_bloco
        self._sobreposicao = sobreposicao
        self._pasta_cache = pasta_cache

        self._pasta_cache.mkdir(
            parents=True,
            exist_ok=True,
        )

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
        hash_documento = self._calcular_hash(
            caminho_pdf
        )

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

                caminho_cache = self._caminho_cache_bloco(
                    hash_documento=hash_documento,
                    inicio=inicio,
                    fim=fim,
                )

                if caminho_cache.exists():
                    print("    Resultado encontrado no cache.")

                    resultado = self._carregar_cache_bloco(
                        caminho_cache
                    )

                else:
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

                    self._salvar_cache_bloco(
                        caminho_cache=caminho_cache,
                        caminho_pdf=caminho_pdf,
                        hash_documento=hash_documento,
                        inicio=inicio,
                        fim=fim,
                        resultado=resultado,
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


        paginas_nao_curriculares_por_chave: dict[
            str,
            set[int],
        ] = {}

        for resultado in resultados:
            for disciplina in resultado.disciplinas:
                if disciplina.tipo_ocorrencia in {
                    TipoOcorrenciaDisciplina.HISTORICA,
                    TipoOcorrenciaDisciplina.COMPARATIVA,
                    TipoOcorrenciaDisciplina.MENCAO,
                }:
                    chave = self._normalizar_nome(
                        disciplina.nome
                    )

                    paginas = (
                        paginas_nao_curriculares_por_chave
                        .setdefault(chave, set())
                    )

                    paginas.update(
                        pagina
                        for pagina in disciplina.paginas_origem
                        if pagina > 0
                    )

        for resultado in resultados:

            for observacao in resultado.observacoes_documento:
                if observacao not in observacoes_documento:
                    observacoes_documento.append(
                        observacao
                    )

            for disciplina in resultado.disciplinas:

                chave = self._normalizar_nome(
                    disciplina.nome
                )

                if disciplina.tipo_ocorrencia in {
                    TipoOcorrenciaDisciplina.HISTORICA,
                    TipoOcorrenciaDisciplina.COMPARATIVA,
                    TipoOcorrenciaDisciplina.MENCAO,
                }:
                    continue

                paginas_nao_curriculares = (
                    paginas_nao_curriculares_por_chave.get(
                        chave,
                        set(),
                    )
                )

                paginas_disciplina = {
                    pagina
                    for pagina in disciplina.paginas_origem
                    if pagina > 0
                }

                if (
                    paginas_disciplina
                    and paginas_nao_curriculares
                    and paginas_disciplina.issubset(
                        paginas_nao_curriculares
                    )
                    and not self._tem_evidencia_curricular_forte(
                        disciplina
                    )
                ):
                    continue

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
        disciplinas = self._reconciliar_titulos(disciplinas)

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

        observacoes_carga = []
        if self._cargas_conflitam(atual.carga_horaria, nova.carga_horaria):
            observacoes_carga.append(
                "Cargas divergentes ou com unidades incompatíveis entre blocos; "
                "mantido um registro inteiro para revisão. Originais: "
                + json.dumps([atual.carga_horaria.model_dump(),
                              nova.carga_horaria.model_dump()], ensure_ascii=False)
            )

        return DisciplinaExtraida(
            nome=self._preferir_texto(
                atual.nome,
                nova.nome,
            ),

            tipo_ocorrencia=(
                TipoOcorrenciaDisciplina.CURRICULAR
                if (
                        atual.tipo_ocorrencia
                        == TipoOcorrenciaDisciplina.CURRICULAR
                        or nova.tipo_ocorrencia
                        == TipoOcorrenciaDisciplina.CURRICULAR
                )
                else atual.tipo_ocorrencia
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

            conteudo_programatico=self._mesclar_conteudo_programatico(
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
                nova.observacoes + observacoes_carga,
            ),
        )

    @classmethod
    def _mesclar_carga_horaria(
        cls, atual: CargaHorariaExtraida, nova: CargaHorariaExtraida,
    ) -> CargaHorariaExtraida:
        if cls._cargas_conflitam(atual, nova):
            # Não montar uma carga artificial com valores incompatíveis.
            escolhida = (nova if cls._pontuacao_carga_horaria(nova)
                         > cls._pontuacao_carga_horaria(atual) else atual)
            return escolhida.model_copy(deep=True)
        return CargaHorariaExtraida(**{
            campo: (getattr(atual, campo) if getattr(atual, campo) is not None
                    else getattr(nova, campo))
            for campo in ("total", "teorica", "pratica", "unidade")
        })

    @staticmethod
    def _pontuacao_carga_horaria(carga: CargaHorariaExtraida) -> int:
        return sum(getattr(carga, c) is not None
                   for c in ("total", "teorica", "pratica", "unidade"))

    @staticmethod
    def _cargas_conflitam(atual: CargaHorariaExtraida,
                         nova: CargaHorariaExtraida) -> bool:
        campos = ("total", "teorica", "pratica")
        tem_atual = any(getattr(atual, c) is not None for c in campos)
        tem_nova = any(getattr(nova, c) is not None for c in campos)
        # Unidade de outro bloco não deve ser atribuída a números sem evidência.
        if atual.unidade != nova.unidade:
            if tem_atual and tem_nova:
                return True
            if tem_atual and atual.unidade is None and nova.unidade is not None:
                return True
            if tem_nova and nova.unidade is None and atual.unidade is not None:
                return True
        return any(getattr(atual, c) is not None and getattr(nova, c) is not None
                   and getattr(atual, c) != getattr(nova, c) for c in campos)

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
    def _mesclar_conteudo_programatico(atual: str | None, novo: str | None) -> str | None:
        # O prompt retorna um tema por linha. Preservar temas de todos os blocos,
        # em vez de escolher somente o texto mais longo e perder continuações.
        linhas = []
        vistos = set()
        for texto in (atual, novo):
            for linha in (texto or "").splitlines():
                linha = linha.strip()
                chave = " ".join(linha.casefold().split()).rstrip(".;")
                if chave and chave not in vistos:
                    vistos.add(chave)
                    linhas.append(linha)
        return "\n".join(linhas) or None

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

    @staticmethod
    def _calcular_hash(
        caminho_pdf: Path,
    ) -> str:
        sha256 = hashlib.sha256()

        with caminho_pdf.open("rb") as arquivo:
            while bloco := arquivo.read(1024 * 1024):
                sha256.update(bloco)

        return sha256.hexdigest()

    def _caminho_cache_bloco(
        self,
        hash_documento: str,
        inicio: int,
        fim: int,
    ) -> Path:
        nome = (
            f"{hash_documento}"
            f"__{self._extrator.modelo}"
            f"__v{VERSAO_CACHE_GEMINI}"
            f"__pag_{inicio + 1}_{fim}.json"
        )

        return self._pasta_cache / nome

    def _salvar_cache_bloco(
        self,
        caminho_cache: Path,
        caminho_pdf: Path,
        hash_documento: str,
        inicio: int,
        fim: int,
        resultado: DocumentoAcademicoExtraido,
    ) -> None:
        dados = {
            "arquivo": caminho_pdf.name,
            "sha256": hash_documento,
            "modelo": self._extrator.modelo,
            "versao_cache": VERSAO_CACHE_GEMINI,
            "pagina_inicial": inicio + 1,
            "pagina_final": fim,
            "resultado": resultado.model_dump(),
        }

        caminho_cache.write_text(
            json.dumps(
                dados,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    @staticmethod
    def _carregar_cache_bloco(
        caminho_cache: Path,
    ) -> DocumentoAcademicoExtraido:
        dados = json.loads(
            caminho_cache.read_text(
                encoding="utf-8"
            )
        )

        return DocumentoAcademicoExtraido.model_validate(
            dados["resultado"]
        )

    @staticmethod
    def _tem_evidencia_curricular_forte(
            disciplina: DisciplinaExtraida,
    ) -> bool:
        return any(
            (
                disciplina.ementa,
                disciplina.conteudo_programatico,
                disciplina.competencias_habilidades,
                disciplina.objetivos.geral,
                disciplina.objetivos.especificos,
                disciplina.objetivos.nao_classificados,
                disciplina.bibliografia.basica,
                disciplina.bibliografia.complementar,
                disciplina.bibliografia.nao_classificada,
            )
        )

    @staticmethod
    def _retirar_codigo_inicial(nome: str) -> str:
        # Ex.: "NF2 - Título" ou "INF101: Título".
        # Não remove números finais nem palavras do título.
        return re.sub(
            r"^\s*[A-Za-z]{1,10}\s*\d+\s*[-–—:]\s*",
            "",
            nome,
        ).strip()

    def _reconciliar_titulos(
        self, disciplinas: list[DisciplinaExtraida],
    ) -> list[DisciplinaExtraida]:
        grupos: dict[str, list[DisciplinaExtraida]] = {}

        for original in disciplinas:
            disciplina = original.model_copy(deep=True)
            titulo = self._retirar_codigo_inicial(disciplina.nome)
            chave = self._normalizar_nome(titulo)
            grupos.setdefault(chave, []).append(disciplina)

        saida: list[DisciplinaExtraida] = []

        for chave, grupo in grupos.items():
            if len(grupo) == 1:
                saida.extend(grupo)
                continue

            motivo = None

            # Esses títulos dependem de contexto: eixo, módulo, matriz.
            generico = re.match(
                r"^(extensao|atividade|atividades|optativa|optativo|"
                r"eletiva|eletivo|estagio|topicos especiais)\b",
                chave,
            )

            if generico:
                motivo = "Título dependente de contexto curricular."

            elif len(grupo) != 2:
                motivo = "Mais de duas ocorrências candidatas à associação."

            else:
                a, b = grupo

                sem_codigo = [
                    d for d in grupo
                    if self._retirar_codigo_inicial(d.nome) == d.nome.strip()
                ]

                if len(sem_codigo) != 1:
                    motivo = (
                        "Não há um único título sem código para associação."
                    )

                elif a.tipo_ocorrencia != b.tipo_ocorrencia:
                    motivo = "Classificações de ocorrência diferentes."

                elif self._cargas_conflitam(
                    a.carga_horaria, b.carga_horaria
                ):
                    motivo = (
                        "Cargas horárias divergentes ou unidades incompatíveis."
                    )

                else:
                    for campo in ("ementa", "conteudo_programatico"):
                        x = getattr(a, campo)
                        y = getattr(b, campo)

                        if (
                            x and y
                            and self._normalizar_nome(x)
                            != self._normalizar_nome(y)
                        ):
                            motivo = (
                                "Textos diferentes; confirmar a identidade."
                            )
                            break

                if motivo is None:
                    unido = self._mesclar_disciplinas(a, b)
                    unido.nome = sem_codigo[0].nome.strip()

                    unido.observacoes = self._mesclar_listas(
                        unido.observacoes,
                        [
                            "Associação por título idêntico após retirar código "
                            f"inicial: {a.nome!r} / {b.nome!r}. "
                            "Confirmar o contexto curricular na revisão."
                        ],
                    )

                    saida.append(unido)
                    continue

            aviso = (
                "Possível duplicidade não unificada: "
                f"{' / '.join(d.nome for d in grupo)}. {motivo}"
            )

            for disciplina in grupo:
                disciplina.observacoes = self._mesclar_listas(
                    disciplina.observacoes,
                    [aviso],
                )

            saida.extend(grupo)

        return saida

