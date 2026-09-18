import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


def _normalizar_texto_opcional(valor: str | None) -> str | None:
    if valor is None:
        return None

    valor_normalizado = valor.strip()

    return valor_normalizado or None


@dataclass(slots=True)
class Instituicao:
    nome: str
    codigo: str | None = None
    sigla: str | None = None
    cnpj: str | None = None
    cidade: str | None = None
    uf: str | None = None
    ativa: bool = True
    instituicao_id: int | None = None

    def __post_init__(self) -> None:
        self.nome = self.nome.strip()
        self.codigo = _normalizar_texto_opcional(self.codigo)
        self.sigla = _normalizar_texto_opcional(self.sigla)
        self.cnpj = _normalizar_texto_opcional(self.cnpj)
        self.cidade = _normalizar_texto_opcional(self.cidade)
        self.uf = _normalizar_texto_opcional(self.uf)

        if not self.nome:
            raise ValueError("O nome da instituição é obrigatório.")

        if len(self.nome) > 200:
            raise ValueError(
                "O nome da instituição não pode ultrapassar 200 caracteres."
            )

        if self.codigo is not None and len(self.codigo) > 30:
            raise ValueError(
                "O código da instituição não pode ultrapassar 30 caracteres."
            )

        if self.sigla is not None:
            self.sigla = self.sigla.upper()

            if len(self.sigla) > 30:
                raise ValueError(
                    "A sigla da instituição não pode ultrapassar 30 caracteres."
                )

        if self.uf is not None:
            self.uf = self.uf.upper()

            if len(self.uf) != 2:
                raise ValueError("A UF deve possuir exatamente dois caracteres.")

        if self.cnpj is not None:
            somente_numeros = self.cnpj.isdigit()

            if not somente_numeros or len(self.cnpj) != 14:
                raise ValueError(
                    "O CNPJ deve possuir exatamente 14 números, sem pontuação."
                )

    def atribuir_id(self, instituicao_id: int) -> None:
        if instituicao_id <= 0:
            raise ValueError("O identificador da instituição deve ser positivo.")

        if self.instituicao_id is not None:
            raise ValueError("A instituição já possui um identificador.")

        self.instituicao_id = instituicao_id

class NivelCurso(str, Enum):
    GRADUACAO = "GRADUACAO"
    POS_GRADUACAO = "POS_GRADUACAO"
    TECNICO = "TECNICO"
    OUTRO = "OUTRO"


class ModalidadeCurso(str, Enum):
    PRESENCIAL = "PRESENCIAL"
    EAD = "EAD"
    HIBRIDO = "HIBRIDO"
    OUTRO = "OUTRO"


def normalizar_nome_para_busca(valor: str) -> str:
    valor_sem_acentos = "".join(
        caractere
        for caractere in unicodedata.normalize("NFKD", valor)
        if not unicodedata.combining(caractere)
    )

    valor_minusculo = valor_sem_acentos.casefold()

    return re.sub(r"\s+", " ", valor_minusculo).strip()


@dataclass(slots=True)
class Curso:
    instituicao_id: int
    codigo: str
    nome: str
    nivel: NivelCurso = NivelCurso.GRADUACAO
    modalidade: ModalidadeCurso = ModalidadeCurso.PRESENCIAL
    ativo: bool = True
    curso_id: int | None = None

    def __post_init__(self) -> None:
        self.codigo = self.codigo.strip().upper()
        self.nome = self.nome.strip()

        if self.instituicao_id <= 0:
            raise ValueError(
                "O identificador da instituição deve ser positivo."
            )

        if not self.codigo:
            raise ValueError("O código do curso é obrigatório.")

        if len(self.codigo) > 30:
            raise ValueError(
                "O código do curso não pode ultrapassar 30 caracteres."
            )

        if not self.nome:
            raise ValueError("O nome do curso é obrigatório.")

        if len(self.nome) > 200:
            raise ValueError(
                "O nome do curso não pode ultrapassar 200 caracteres."
            )

    def atribuir_id(self, curso_id: int) -> None:
        if curso_id <= 0:
            raise ValueError("O identificador do curso deve ser positivo.")

        if self.curso_id is not None:
            raise ValueError("O curso já possui um identificador.")

        self.curso_id = curso_id


@dataclass(slots=True)
class Disciplina:
    instituicao_id: int
    codigo: str
    nome: str
    area_conhecimento: str | None = None
    ativa: bool = True
    disciplina_id: int | None = None
    nome_normalizado: str | None = None

    def __post_init__(self) -> None:
        self.codigo = self.codigo.strip().upper()
        self.nome = self.nome.strip()

        if self.area_conhecimento is not None:
            self.area_conhecimento = (
                self.area_conhecimento.strip() or None
            )

        if self.instituicao_id <= 0:
            raise ValueError(
                "O identificador da instituição deve ser positivo."
            )

        if not self.codigo:
            raise ValueError("O código da disciplina é obrigatório.")

        if len(self.codigo) > 50:
            raise ValueError(
                "O código da disciplina não pode ultrapassar 50 caracteres."
            )

        if not self.nome:
            raise ValueError("O nome da disciplina é obrigatório.")

        if len(self.nome) > 200:
            raise ValueError(
                "O nome da disciplina não pode ultrapassar 200 caracteres."
            )

        if (
            self.area_conhecimento is not None
            and len(self.area_conhecimento) > 150
        ):
            raise ValueError(
                "A área de conhecimento não pode ultrapassar 150 caracteres."
            )

        self.nome_normalizado = normalizar_nome_para_busca(self.nome)

    def atribuir_id(self, disciplina_id: int) -> None:
        if disciplina_id <= 0:
            raise ValueError(
                "O identificador da disciplina deve ser positivo."
            )

        if self.disciplina_id is not None:
            raise ValueError("A disciplina já possui um identificador.")

        self.disciplina_id = disciplina_id

class StatusMatrizCurricular(str, Enum):
    RASCUNHO ='RASCUNHO'
    ATIVA ='ATIVA'
    INATIVA ='INATIVA'
    ARQUIVADA ='ARQUIVADA'

class NaturezaDisciplina(str, Enum):
    OBRIGATORIA ='OBRIGATORIA'
    OPTATIVA ='OPTATIVA'
    ELETIVA ='ELETIVA'
    OUTRA = 'OUTRA'

@dataclass(slots=True)
class MatrizCurricular:
    curso_id: int
    codigo: str
    nome: str | None = None
    ano_inicio_vigencia: int | None = None
    semestre_inicio: int | None = None
    ano_fim_vigencia: int | None = None
    semestre_fim: int | None = None
    status: StatusMatrizCurricular = StatusMatrizCurricular.RASCUNHO
    matriz_curricular_id: int | None = None

    def __post_init__(self) -> None:
        self.codigo = self.codigo.strip().upper()

        if self.nome is not None:
            self.nome = self.nome.strip() or None

        if self.curso_id <= 0:
            raise ValueError(
                "O identificador do curso deve ser positivo."
            )

        if not self.codigo:
            raise ValueError(
                "O código da matriz curricular é obrigatório."
            )

        if len(self.codigo) > 50:
            raise ValueError(
                "O código da matriz não pode ultrapassar 50 caracteres."
            )

        if self.nome is not None and len(self.nome) > 200:
            raise ValueError(
                "O nome da matriz não pode ultrapassar 200 caracteres."
            )

        self._validar_periodo_vigencia()

    def _validar_periodo_vigencia(self) -> None:
        if (
            self.ano_inicio_vigencia is None
            and self.semestre_inicio is not None
        ):
            raise ValueError(
                "Não é possível informar o semestre inicial sem o ano inicial."
            )

        if (
            self.ano_fim_vigencia is None
            and self.semestre_fim is not None
        ):
            raise ValueError(
                "Não é possível informar o semestre final sem o ano final."
            )

        for ano in (
            self.ano_inicio_vigencia,
            self.ano_fim_vigencia,
        ):
            if ano is not None and not 1900 <= ano <= 2200:
                raise ValueError(
                    "O ano de vigência deve estar entre 1900 e 2200."
                )

        for semestre in (
            self.semestre_inicio,
            self.semestre_fim,
        ):
            if semestre is not None and semestre not in (1, 2):
                raise ValueError(
                    "O semestre de vigência deve ser 1 ou 2."
                )

        if (
            self.ano_inicio_vigencia is not None
            and self.ano_fim_vigencia is not None
        ):
            inicio = (
                self.ano_inicio_vigencia,
                self.semestre_inicio or 1,
            )

            fim = (
                self.ano_fim_vigencia,
                self.semestre_fim or 2,
            )

            if fim < inicio:
                raise ValueError(
                    "O fim da vigência não pode ser anterior ao início."
                )

    @property
    def pode_ser_alterada(self) -> bool:
        return self.status == StatusMatrizCurricular.RASCUNHO

    def atribuir_id(self, matriz_curricular_id: int) -> None:
        if matriz_curricular_id <= 0:
            raise ValueError(
                "O identificador da matriz deve ser positivo."
            )

        if self.matriz_curricular_id is not None:
            raise ValueError(
                "A matriz curricular já possui um identificador."
            )

        self.matriz_curricular_id = matriz_curricular_id


@dataclass(slots=True)
class MatrizDisciplina:
    matriz_curricular_id: int
    disciplina_id: int
    periodo_sugerido: int | None = None
    natureza: NaturezaDisciplina = NaturezaDisciplina.OBRIGATORIA
    creditos: Decimal | None = None
    ativa: bool = True
    matriz_disciplina_id: int | None = None

    def __post_init__(self) -> None:
        if self.matriz_curricular_id <= 0:
            raise ValueError(
                "O identificador da matriz deve ser positivo."
            )

        if self.disciplina_id <= 0:
            raise ValueError(
                "O identificador da disciplina deve ser positivo."
            )

        if (
            self.periodo_sugerido is not None
            and not 1 <= self.periodo_sugerido <= 20
        ):
            raise ValueError(
                "O período sugerido deve estar entre 1 e 20."
            )

        if self.creditos is not None:
            if self.creditos < Decimal("0"):
                raise ValueError(
                    "A quantidade de créditos não pode ser negativa."
                )

            if self.creditos > Decimal("9999.99"):
                raise ValueError(
                    "A quantidade de créditos ultrapassa o limite."
                )

    def atribuir_id(self, matriz_disciplina_id: int) -> None:
        if matriz_disciplina_id <= 0:
            raise ValueError(
                "O identificador da associação deve ser positivo."
            )

        if self.matriz_disciplina_id is not None:
            raise ValueError(
                "A associação já possui um identificador."
            )

        self.matriz_disciplina_id = matriz_disciplina_id