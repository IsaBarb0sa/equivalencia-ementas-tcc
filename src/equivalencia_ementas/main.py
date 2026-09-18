from decimal import Decimal

from equivalencia_ementas.academico.application.commands import (
    CadastrarEmentaCommand,
)
from equivalencia_ementas.academico.application.use_cases.cadastrar_ementa import (
    CadastrarEmenta,
)
from equivalencia_ementas.academico.domain.entities import (
    UnidadeCargaHoraria,
)
from equivalencia_ementas.academico.infrastructure.unit_of_work import (
    SqlAlchemyAcademicoUnitOfWork,
)


DISCIPLINA_ID = 2
MATRIZ_DISCIPLINA_ID = 2


EMENTA_SEMIOLOGIA = (
    "Realização do exame clínico, diagnóstico diferencial, "
    "diagnóstico final, prognóstico e plano de tratamento das "
    "doenças da cavidade oral. Desenvolvimento de habilidades "
    "necessárias para a utilização de seus conhecimentos de forma "
    "efetiva como procedimento diário de sua clínica, como na "
    "utilização dos recursos do exame clínico na obtenção de sinais "
    "e sintomas das doenças e atribuir valor clínico a estes. "
    "Trabalho com tema transversal - liberdade de aprender, ensinar, "
    "pesquisar e divulgar a cultura, o pensamento, a arte e o saber."
)


def cadastrar_ementa_semiologia() -> int:
    if DISCIPLINA_ID <= 2:
        raise RuntimeError(
        )

    if MATRIZ_DISCIPLINA_ID <= 2:
        raise RuntimeError(
        )

    command = CadastrarEmentaCommand(
        disciplina_id=DISCIPLINA_ID,
        matriz_disciplina_id=MATRIZ_DISCIPLINA_ID,
        versao="2019/2",
        idioma="pt-BR",
        ano_vigencia=2019,
        semestre_vigencia=2,
        resumo=EMENTA_SEMIOLOGIA,
        carga_horaria_declarada=Decimal("40"),
        unidade_carga_horaria=UnidadeCargaHoraria.HORA,
        carga_horaria_normalizada_min=2400,
    )

    caso_de_uso = CadastrarEmenta(
        SqlAlchemyAcademicoUnitOfWork()
    )

    return caso_de_uso.executar(command)


def main() -> None:
    ementa_id = cadastrar_ementa_semiologia()

    print(
        "Ementa de Semiologia cadastrada com sucesso. "
        f"EmentaId: {ementa_id}"
    )


if __name__ == "__main__":
    main()