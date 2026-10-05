from typing import Protocol

from equivalencia_ementas.academico.domain.entities import (
    Curso,
    Disciplina,
    Instituicao,
    MatrizCurricular,
    MatrizDisciplina,
    Ementa,
)


class InstituicaoRepository(Protocol):
    def adicionar(self, instituicao: Instituicao) -> None: ...

    def buscar_por_id(
        self,
        instituicao_id: int,
    ) -> Instituicao | None: ...

    def buscar_por_codigo(
        self,
        codigo: str,
    ) -> Instituicao | None: ...


class CursoRepository(Protocol):
    def adicionar(self, curso: Curso) -> None: ...

    def buscar_por_id(
        self,
        curso_id: int,
    ) -> Curso | None: ...

    def buscar_por_codigo(
        self,
        instituicao_id: int,
        codigo: str,
    ) -> Curso | None: ...


class DisciplinaRepository(Protocol):
    def adicionar(self, disciplina: Disciplina) -> None: ...

    def buscar_por_id(
        self,
        disciplina_id: int,
    ) -> Disciplina | None: ...

    def buscar_por_codigo(
        self,
        instituicao_id: int,
        codigo: str,
    ) -> Disciplina | None: ...


class MatrizCurricularRepository(Protocol):
    def adicionar(
        self,
        matriz: MatrizCurricular,
    ) -> None: ...

    def buscar_por_id(
        self,
        matriz_curricular_id: int,
    ) -> MatrizCurricular | None: ...

    def buscar_por_codigo(
        self,
        curso_id: int,
        codigo: str,
    ) -> MatrizCurricular | None: ...


class MatrizDisciplinaRepository(Protocol):
    def adicionar(
        self,
        matriz_disciplina: MatrizDisciplina,
    ) -> None: ...

    def buscar_por_id(
        self,
        matriz_disciplina_id: int,
    ) -> MatrizDisciplina | None: ...

    def buscar_associacao(
        self,
        matriz_curricular_id: int,
        disciplina_id: int,
    ) -> MatrizDisciplina | None: ...


class EmentaRepository(Protocol):
    def adicionar(self, ementa: Ementa) -> None: ...

    def buscar_por_id(
        self,
        ementa_id: int,
    ) -> Ementa | None: ...

    def buscar_por_identidade(
        self,
        disciplina_id: int,
        matriz_disciplina_id: int | None,
        versao: str,
    ) -> Ementa | None: ...
