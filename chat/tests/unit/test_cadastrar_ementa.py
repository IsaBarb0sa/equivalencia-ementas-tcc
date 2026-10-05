from decimal import Decimal
from types import TracebackType

import pytest

from equivalencia_ementas.academico.application.commands import (
    CadastrarEmentaCommand,
)
from equivalencia_ementas.academico.application.exceptions import (
    DisciplinaNaoEncontradaError,
    EmentaJaExisteError,
    EmentaMatrizDisciplinaIncompativelError,
    MatrizDisciplinaNaoEncontradaError,
)
from equivalencia_ementas.academico.application.use_cases.cadastrar_ementa import (
    CadastrarEmenta,
)
from equivalencia_ementas.academico.domain.entities import (
    Disciplina,
    Ementa,
    MatrizDisciplina,
)


class DisciplinaRepositoryFake:
    def __init__(
        self,
        disciplinas: list[Disciplina] | None = None,
    ) -> None:
        self._disciplinas = {
            disciplina.disciplina_id: disciplina
            for disciplina in disciplinas or []
        }

    def buscar_por_id(
        self,
        disciplina_id: int,
    ) -> Disciplina | None:
        return self._disciplinas.get(disciplina_id)


class MatrizDisciplinaRepositoryFake:
    def __init__(
        self,
        vinculos: list[MatrizDisciplina] | None = None,
    ) -> None:
        self._vinculos = {
            vinculo.matriz_disciplina_id: vinculo
            for vinculo in vinculos or []
        }

    def buscar_por_id(
        self,
        matriz_disciplina_id: int,
    ) -> MatrizDisciplina | None:
        return self._vinculos.get(matriz_disciplina_id)


class EmentaRepositoryFake:
    def __init__(
        self,
        ementas: list[Ementa] | None = None,
    ) -> None:
        self.ementas = list(ementas or [])

    def adicionar(self, ementa: Ementa) -> None:
        proximo_id = len(self.ementas) + 1

        ementa.atribuir_id(proximo_id)
        self.ementas.append(ementa)

    def buscar_por_identidade(
        self,
        disciplina_id: int,
        matriz_disciplina_id: int | None,
        versao: str,
    ) -> Ementa | None:
        for ementa in self.ementas:
            if (
                ementa.disciplina_id == disciplina_id
                and ementa.matriz_disciplina_id
                == matriz_disciplina_id
                and ementa.versao == versao
            ):
                return ementa

        return None


class AcademicoUnitOfWorkFake:
    def __init__(
        self,
        disciplinas: list[Disciplina] | None = None,
        vinculos: list[MatrizDisciplina] | None = None,
        ementas: list[Ementa] | None = None,
    ) -> None:
        self.disciplinas = DisciplinaRepositoryFake(
            disciplinas
        )
        self.matrizes_disciplinas = (
            MatrizDisciplinaRepositoryFake(vinculos)
        )
        self.ementas = EmentaRepositoryFake(ementas)

        self.quantidade_commits = 0
        self.quantidade_rollbacks = 0

    def __enter__(self) -> "AcademicoUnitOfWorkFake":
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exception_type is not None:
            self.rollback()

    def commit(self) -> None:
        self.quantidade_commits += 1

    def rollback(self) -> None:
        self.quantidade_rollbacks += 1


def criar_disciplina(
    disciplina_id: int = 1,
) -> Disciplina:
    return Disciplina(
        disciplina_id=disciplina_id,
        instituicao_id=1,
        codigo=f"DISC-{disciplina_id}",
        nome="Semiologia",
        area_conhecimento="Odontologia",
    )


def criar_vinculo(
    matriz_disciplina_id: int = 10,
    disciplina_id: int = 1,
) -> MatrizDisciplina:
    return MatrizDisciplina(
        matriz_disciplina_id=matriz_disciplina_id,
        matriz_curricular_id=5,
        disciplina_id=disciplina_id,
        periodo_sugerido=4,
    )


def criar_command(
    disciplina_id: int = 1,
    matriz_disciplina_id: int | None = 10,
) -> CadastrarEmentaCommand:
    return CadastrarEmentaCommand(
        disciplina_id=disciplina_id,
        matriz_disciplina_id=matriz_disciplina_id,
        versao="2019/2",
        ano_vigencia=2019,
        semestre_vigencia=2,
        resumo="Realização do exame clínico.",
        carga_horaria_declarada=Decimal("40"),
        carga_horaria_normalizada_min=2400,
    )


def test_deve_cadastrar_ementa_valida() -> None:
    uow = AcademicoUnitOfWorkFake(
        disciplinas=[criar_disciplina()],
        vinculos=[criar_vinculo()],
    )

    caso_de_uso = CadastrarEmenta(uow)

    ementa_id = caso_de_uso.executar(
        criar_command()
    )

    assert ementa_id == 1
    assert uow.quantidade_commits == 1
    assert uow.quantidade_rollbacks == 0
    assert len(uow.ementas.ementas) == 1

    ementa = uow.ementas.ementas[0]

    assert ementa.disciplina_id == 1
    assert ementa.matriz_disciplina_id == 10
    assert ementa.versao == "2019/2"
    assert ementa.carga_horaria_declarada == Decimal("40")


def test_deve_cadastrar_ementa_sem_matriz() -> None:
    uow = AcademicoUnitOfWorkFake(
        disciplinas=[criar_disciplina()],
    )

    caso_de_uso = CadastrarEmenta(uow)

    ementa_id = caso_de_uso.executar(
        criar_command(matriz_disciplina_id=None)
    )

    assert ementa_id == 1
    assert uow.quantidade_commits == 1
    assert uow.ementas.ementas[0].matriz_disciplina_id is None


def test_deve_rejeitar_disciplina_inexistente() -> None:
    uow = AcademicoUnitOfWorkFake()
    caso_de_uso = CadastrarEmenta(uow)

    with pytest.raises(
        DisciplinaNaoEncontradaError,
        match="Disciplina 1 não encontrada",
    ):
        caso_de_uso.executar(criar_command())

    assert uow.quantidade_commits == 0
    assert uow.quantidade_rollbacks == 1


def test_deve_rejeitar_vinculo_inexistente() -> None:
    uow = AcademicoUnitOfWorkFake(
        disciplinas=[criar_disciplina()],
    )

    caso_de_uso = CadastrarEmenta(uow)

    with pytest.raises(
        MatrizDisciplinaNaoEncontradaError,
        match="Vínculo entre matriz e disciplina 10 não encontrado",
    ):
        caso_de_uso.executar(criar_command())

    assert uow.quantidade_commits == 0
    assert uow.quantidade_rollbacks == 1


def test_deve_rejeitar_vinculo_de_outra_disciplina() -> None:
    uow = AcademicoUnitOfWorkFake(
        disciplinas=[criar_disciplina(disciplina_id=1)],
        vinculos=[
            criar_vinculo(
                matriz_disciplina_id=10,
                disciplina_id=2,
            )
        ],
    )

    caso_de_uso = CadastrarEmenta(uow)

    with pytest.raises(
        EmentaMatrizDisciplinaIncompativelError,
        match="vínculo informado pertence a outra disciplina",
    ):
        caso_de_uso.executar(criar_command())

    assert uow.quantidade_commits == 0
    assert uow.quantidade_rollbacks == 1


def test_deve_rejeitar_ementa_duplicada() -> None:
    existente = Ementa(
        ementa_id=50,
        disciplina_id=1,
        matriz_disciplina_id=10,
        versao="2019/2",
        resumo="Ementa já cadastrada.",
        carga_horaria_declarada=Decimal("40"),
    )

    uow = AcademicoUnitOfWorkFake(
        disciplinas=[criar_disciplina()],
        vinculos=[criar_vinculo()],
        ementas=[existente],
    )

    caso_de_uso = CadastrarEmenta(uow)

    with pytest.raises(
        EmentaJaExisteError,
        match="Já existe uma ementa",
    ):
        caso_de_uso.executar(criar_command())

    assert uow.quantidade_commits == 0
    assert uow.quantidade_rollbacks == 1
    assert len(uow.ementas.ementas) == 1