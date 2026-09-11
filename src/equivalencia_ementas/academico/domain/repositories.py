from typing import Protocol

from equivalencia_ementas.academico.domain.entities import (
    Curso,
    Disciplina,
    Instituicao,
)


class InstituicaoRepository(Protocol):
    def adicionar(self, instituicao: Instituicao) -> None:
        ...

    def buscar_por_id(
        self,
        instituicao_id: int,
    ) -> Instituicao | None:
        ...

    def buscar_por_codigo(
        self,
        codigo: str,
    ) -> Instituicao | None:
        ...

class CursoRepository(Protocol):
    def adicionar(self, curso: Curso) -> None:
        ...

    def buscar_por_id(
        self,
        curso_id: int,
    ) -> Curso | None:
        ...

    def buscar_por_codigo(
        self,
        instituicao_id: int,
        codigo: str,
    ) -> Curso | None:
        ...

class DisciplinaRepository(Protocol):
    def adicionar(self, disciplina: Disciplina) -> None:
        ...

    def buscar_por_id(
        self,
        disciplina_id: int,
    ) -> Disciplina | None:
        ...

    def buscar_por_codigo(
        self,
        instituicao_id: int,
        codigo: str,
    ) -> Disciplina | None:
        ...