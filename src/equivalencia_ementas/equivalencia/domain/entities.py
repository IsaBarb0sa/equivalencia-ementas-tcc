from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CargaHorariaEquivalencia:
    total: float | None = None
    teorica: float | None = None
    pratica: float | None = None
    unidade: str | None = None


@dataclass(frozen=True)
class DisciplinaParaEquivalencia:
    nome: str

    ementa: str | None = None
    conteudo_programatico: str | None = None

    objetivo_geral: str | None = None
    objetivos_especificos: str | None = None
    objetivos_nao_classificados: str | None = None

    competencias_habilidades: str | None = None

    carga_horaria: CargaHorariaEquivalencia = field(
        default_factory=CargaHorariaEquivalencia
    )

    identificador: str | None = None
    instituicao: str | None = None
    curso: str | None = None

    def possui_conteudo_semantico(self) -> bool:
        campos = (
            self.ementa,
            self.conteudo_programatico,
            self.objetivo_geral,
            self.objetivos_especificos,
            self.objetivos_nao_classificados,
            self.competencias_habilidades,
        )

        return any(
            isinstance(campo, str) and bool(campo.strip())
            for campo in campos
        )