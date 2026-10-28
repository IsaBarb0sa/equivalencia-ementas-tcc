from dataclasses import dataclass
from typing import Protocol

from equivalencia_ementas.academico.domain.entities import Curso


class RepositorioListagemCursos(Protocol):
    def listar_ativos_por_instituicao(self, instituicao_id: int) -> list[Curso]:
        ...


@dataclass(frozen=True)
class CursoListado:
    id: int
    nome: str


class ListarCursos:
    def __init__(self, repository: RepositorioListagemCursos) -> None:
        self._repository = repository

    def executar(self, instituicao_id: int) -> list[CursoListado]:
        if instituicao_id <= 0:
            raise ValueError("O ID da instituição deve ser positivo.")

        cursos = self._repository.listar_ativos_por_instituicao(instituicao_id)
        resultado = []

        for curso in cursos:
            if curso.curso_id is None:
                raise ValueError("Curso persistido sem identificador.")

            resultado.append(
                CursoListado(
                    id=curso.curso_id,
                    nome=curso.nome,
                )
            )

        return resultado