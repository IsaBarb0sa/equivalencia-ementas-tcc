from __future__ import annotations

import hashlib
import json
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
    TipoOcorrenciaDisciplina,
)

VERSAO_CACHE_GEMINI = "3"

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

        for disciplina in disciplinas:
            self._validar_carga_horaria_semanal(
                disciplina
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

    @classmethod
    def _mesclar_carga_horaria(
            cls,
            atual: CargaHorariaExtraida,
            nova: CargaHorariaExtraida,
    ) -> CargaHorariaExtraida:

        if cls._cargas_conflitam(atual, nova):
            # Em caso de conflito, não mistura os campos.
            # Mantém o registro de carga horária mais completo.
            if cls._pontuacao_carga_horaria(nova) > cls._pontuacao_carga_horaria(atual):
                return nova

            return atual

        total_hora_aula = (
            atual.total_hora_aula
            if atual.total_hora_aula is not None
            else nova.total_hora_aula
        )

        total_hora_relogio = (
            atual.total_hora_relogio
            if atual.total_hora_relogio is not None
            else nova.total_hora_relogio
        )

        total = (
            atual.total
            if atual.total is not None
            else nova.total
        )

        # Se possuímos explicitamente os dois tipos de total,
        # o campo genérico "total" deixa de ser necessário.
        if (
                total_hora_aula is not None
                and total_hora_relogio is not None
        ):
            total = None

        return CargaHorariaExtraida(
            total=total,

            total_hora_aula=total_hora_aula,

            total_hora_relogio=total_hora_relogio,

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

            teorica_semanal=(
                atual.teorica_semanal
                if atual.teorica_semanal is not None
                else nova.teorica_semanal
            ),

            pratica_semanal=(
                atual.pratica_semanal
                if atual.pratica_semanal is not None
                else nova.pratica_semanal
            ),

            total_semanal=(
                atual.total_semanal
                if atual.total_semanal is not None
                else nova.total_semanal
            ),

            unidade=(
                atual.unidade
                if atual.unidade
                else nova.unidade
            ),

            duracao_hora_aula_minutos=(
                atual.duracao_hora_aula_minutos
                if atual.duracao_hora_aula_minutos is not None
                else nova.duracao_hora_aula_minutos
            ),
        )

    @staticmethod
    def _pontuacao_carga_horaria(
            carga: CargaHorariaExtraida,
    ) -> int:
        pontuacao = 0

        # Totais explicitamente tipados têm prioridade
        # sobre um total genérico.
        if carga.total_hora_aula is not None:
            pontuacao += 3

        if carga.total_hora_relogio is not None:
            pontuacao += 3

        if carga.total is not None:
            pontuacao += 1

        if carga.teorica is not None:
            pontuacao += 2

        if carga.pratica is not None:
            pontuacao += 2

        if carga.teorica_semanal is not None:
            pontuacao += 1

        if carga.pratica_semanal is not None:
            pontuacao += 1

        if carga.total_semanal is not None:
            pontuacao += 1

        if carga.unidade:
            pontuacao += 1

        if carga.duracao_hora_aula_minutos is not None:
            pontuacao += 1

        return pontuacao

    @staticmethod
    def _cargas_conflitam(
            atual: CargaHorariaExtraida,
            nova: CargaHorariaExtraida,
    ) -> bool:

        campos_diretos = (
            "total_hora_aula",
            "total_hora_relogio",
            "teorica",
            "pratica",
            "teorica_semanal",
            "pratica_semanal",
            "total_semanal",
            "duracao_hora_aula_minutos",
        )

        for campo in campos_diretos:
            valor_atual = getattr(atual, campo)
            valor_novo = getattr(nova, campo)

            if (
                    valor_atual is not None
                    and valor_novo is not None
                    and valor_atual != valor_novo
            ):
                return True

        # total genérico contra total genérico
        if (
                atual.total is not None
                and nova.total is not None
                and atual.total != nova.total
        ):
            return True

        # Um bloco pode trazer somente "total",
        # enquanto outro identifica hora-aula/hora-relógio.
        # É compatível somente se o total genérico corresponder
        # a pelo menos um dos totais explicitamente informados.
        pares = (
            (atual.total, nova),
            (nova.total, atual),
        )

        for total_generico, outra in pares:
            if total_generico is None:
                continue

            totais_especificos = [
                valor
                for valor in (
                    outra.total_hora_aula,
                    outra.total_hora_relogio,
                )
                if valor is not None
            ]

            if (
                    totais_especificos
                    and total_generico not in totais_especificos
            ):
                return True

        return False

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
    def _validar_carga_horaria_semanal(
            disciplina: DisciplinaExtraida,
    ) -> None:
        carga = disciplina.carga_horaria

        teorica = carga.teorica_semanal
        pratica = carga.pratica_semanal
        total = carga.total_semanal

        if total is None:
            return

        inconsistente = False

        if (
                teorica is not None
                and pratica is not None
                and teorica + pratica != total
        ):
            inconsistente = True

        elif (
                teorica is not None
                and teorica > total
        ):
            inconsistente = True

        elif (
                pratica is not None
                and pratica > total
        ):
            inconsistente = True

        if not inconsistente:
            return

        # O total semanal é preservado porque foi
        # explicitamente extraído do documento.
        #
        # Como não é possível determinar com segurança
        # qual componente semanal está incorreto,
        # evitamos escolher entre teórica e prática.
        carga.teorica_semanal = None
        carga.pratica_semanal = None

        observacao = (
            "Carga horária semanal inconsistente na extração: "
            "os valores de carga teórica/prática não foram "
            "preservados porque não são compatíveis com o "
            "total semanal informado."
        )

        if observacao not in disciplina.observacoes:
            disciplina.observacoes.append(
                observacao
            )