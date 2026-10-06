import json
import logging
import time
from pathlib import Path

from google import genai
from google.genai import errors

from equivalencia_ementas.infraestrutura.ia.modelos_extracao import (
    DocumentoAcademicoExtraido,
)
from equivalencia_ementas.shared.settings.config import get_settings


logger = logging.getLogger(__name__)


INSTRUCOES_EXTRACAO = """
Você é um componente de extração estruturada de documentos acadêmicos.

Sua tarefa é analisar o documento fornecido e identificar TODAS as disciplinas
ou componentes curriculares presentes nele, extraindo o máximo possível das
informações acadêmicas disponíveis.

REGRAS OBRIGATÓRIAS:

1. Extraia somente informações presentes no documento.

2. Não invente, estime, deduza ou complete informações ausentes.

3. Quando um campo textual ou numérico não estiver disponível, retorne null.
   Mantenha carga_horaria, objetivos e bibliografia como objetos com seus
   campos internos nulos quando não houver informações. Mantenha os campos
   de lista como listas; não substitua objetos ou listas por null.

4. O documento pode conter uma única disciplina ou várias disciplinas.

5. Considere como disciplina qualquer componente curricular claramente
   identificável pelo nome, mesmo que não possua ementa.

6. IMPORTANTE: uma disciplina deve ser preservada mesmo quando o documento
   apresenta somente seu nome e sua carga horária.

7. Não descarte uma disciplina apenas porque objetivos, ementa,
   conteúdo programático ou bibliografia estão ausentes.

8. Identifique todas as disciplinas individualizáveis no documento.

9. Não misture informações pertencentes a disciplinas diferentes.

10. Para cada disciplina, extraia quando existirem:
    - nome;
    - carga horária;
    - objetivos;
    - competências e habilidades;
    - ementa;
    - conteúdo programático;
    - bibliografia.

11. Extraia os dados de carga horária exatamente conforme apresentados
    no documento.

12. Quando o documento apresentar apenas uma carga horária total,
    preencha carga_horaria.total e informe sua unidade em
    carga_horaria.unidade.

13. Quando o documento apresentar explicitamente dois totais diferentes,
    um em horas-aula e outro em horas-relógio, não escolha apenas um deles.
    Preencha:
    - total_hora_aula com o valor em horas-aula;
    - total_hora_relogio com o valor em horas-relógio;
    - total como null.

14. Os campos teorica e pratica representam cargas horárias TOTAIS.
    Só os preencha quando o documento informar explicitamente a carga
    horária teórica total ou prática total.

15. Se valores teóricos e práticos representarem distribuição semanal,
    utilize teorica_semanal e pratica_semanal.

16. Não interprete automaticamente valores semanais como cargas totais.

17. Não calcule carga horária total multiplicando valores semanais.

18. Não converta hora-aula em hora-relógio.

19. Não suponha a duração da hora-aula.

20. Preserve ementa, objetivos e conteúdo programático com a maior
    fidelidade possível. Não faça resumos desnecessários.

21. Informe as páginas nas quais as informações de cada disciplina
    foram encontradas.

22. A instituição e o curso devem ser preenchidos somente quando
    puderem ser identificados no documento.

23. Classifique referências encontradas em seções como:
    "Bibliografia Básica", "Bibliografia Física Básica",
    "Bibliografia Virtual Básica", "Referências Básicas" ou
    nomenclaturas equivalentes no campo bibliografia.basica.

24. Classifique referências encontradas em seções como:
    "Bibliografia Complementar", "Bibliografia Física Complementar",
    "Bibliografia Virtual Complementar" ou nomenclaturas equivalentes
    no campo bibliografia.complementar.

25. Utilize bibliografia.nao_classificada apenas quando existirem
    referências, mas não for possível determinar se são básicas
    ou complementares.

26. Expressões como "não há", "não possui", "não se aplica",
    "sem bibliografia" ou equivalentes representam ausência de
    bibliografia. Nesses casos, mantenha os campos correspondentes dentro
    do objeto bibliografia como null.

27. Preserve as referências bibliográficas encontradas sem criar
    informações que não estejam no documento.

PRIORIDADE:
É preferível retornar uma disciplina parcialmente preenchida do que
deixar de retornar uma disciplina existente no documento.

PROCEDIMENTO DE LEITURA:
- Examine todas as páginas, incluindo tabelas, cabeçalhos e rodapés.
- Primeiro localize os nomes explícitos das disciplinas. Em tabelas com
  colunas como Período, Disciplina e Carga, cada linha que identifica um
  componente curricular deve gerar um item em disciplinas.
- Depois associe a cada nome os dados da mesma seção. O nome pode aparecer
  antes ou depois da ementa e da bibliografia na ordem de leitura do PDF.
  Use o layout da página para identificar a associação; se ela for ambígua,
  preserve o nome e os dados seguros e registre a dúvida em observacoes.
- Não use títulos de livros da bibliografia como nomes de disciplinas.
- A ausência do nome do curso não impede a extração das disciplinas.
- Use a posição da página no PDF, começando em 1, em paginas_origem.
- Antes de responder, confira se todos os nomes explícitos encontrados
  estão representados na lista disciplinas, mesmo sem outros dados.
  
  Quando uma tabela possuir colunas separadas para carga horária semanal
TEÓRICA, PRÁTICA e TOTAL:

- preencha teorica_semanal somente com o valor da coluna TEÓRICA;
- preencha pratica_semanal somente com o valor da coluna PRÁTICA;
- não copie o valor da coluna TOTAL para teorica_semanal ou pratica_semanal;
- se a célula da coluna TEÓRICA ou PRÁTICA estiver vazia, mantenha o
  campo correspondente como null;
- quando existir uma coluna TOTAL referente à distribuição semanal,
  armazene esse valor em carga_horaria.total_semanal;
- nunca armazene o TOTAL semanal em carga_horaria.total;
- carga_horaria.total representa somente a carga horária TOTAL da
  disciplina quando o documento apresenta um único total global e
  não distingue hora-aula de hora-relógio.
- não deduza a carga prática pela diferença entre total e teórica,
  nem a carga teórica pela diferença entre total e prática.

Exemplo:

TEÓRICA semanal = 4
PRÁTICA semanal = vazio
TOTAL semanal = 4
TOTAL em hora-aula = 72
TOTAL em hora-relógio = 60

deve resultar em:

total = null
total_hora_aula = 72
total_hora_relogio = 60
teorica_semanal = 4
pratica_semanal = null
total_semanal = 4

IDENTIFICAÇÃO DO CONTEXTO DA DISCIPLINA:

Para cada disciplina encontrada, classifique tipo_ocorrencia como:

- CURRICULAR:
  quando a disciplina fizer parte de uma matriz curricular, grade,
  ementário, plano de ensino ou conjunto de disciplinas apresentado
  como pertencente ao curso analisado.

- HISTORICA:
  quando a disciplina aparecer explicitamente como pertencente a
  matriz anterior, currículo antigo, versão anterior ou estrutura
  curricular substituída.

- COMPARATIVA:
  quando a disciplina aparecer apenas em tabela ou seção destinada
  a comparação, equivalência, alteração, migração ou correspondência
  entre matrizes/componentes curriculares.

- MENCAO:
  quando o nome da disciplina for apenas citado no texto, sem ser
  apresentado como componente curricular daquele conjunto.

- INDETERMINADA:
  quando o documento não fornecer contexto suficiente para classificar
  com segurança.

Não transforme disciplinas históricas, comparativas ou simples menções
em disciplinas curriculares atuais.

Não deduza vigência apenas pela posição da página.

Uma mesma disciplina pode aparecer em mais de um contexto.
Preserve cada ocorrência com a classificação correspondente.

FORMATO DA RESPOSTA:
Retorne explicitamente instituicao, curso, disciplinas e
observacoes_documento. Só retorne disciplinas vazia quando não houver
nenhum componente curricular identificável; nesse caso, explique o motivo
em observacoes_documento. Um JSON válido precisa também representar o
conteúdo acadêmico encontrado, não apenas os dados institucionais.
"""


class ExtratorGemini:
    def __init__(self) -> None:
        settings = get_settings()

        if not settings.gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY não configurada no arquivo .env."
            )

        self._modelo = settings.gemini_model
        self._cliente = genai.Client(
            api_key=settings.gemini_api_key
        )

    @property
    def modelo(self) -> str:
        return self._modelo

    def extrair(
        self,
        caminho_pdf: Path,
    ) -> DocumentoAcademicoExtraido:

        caminho_pdf = Path(caminho_pdf)

        if not caminho_pdf.exists():
            raise FileNotFoundError(
                f"Arquivo não encontrado: {caminho_pdf}"
            )

        arquivo = self._cliente.files.upload(
            file=caminho_pdf
        )

        prompt = f"""
{INSTRUCOES_EXTRACAO}

Analise integralmente o documento enviado.

Retorne todas as disciplinas e campos encontrados.
"""

        ultima_excecao = None
        esquema_resposta = DocumentoAcademicoExtraido.model_json_schema()
        # Os defaults locais não devem permitir a omissão de campos na API.
        esquema_resposta["required"] = list(esquema_resposta["properties"])

        for tentativa in range(1, 4):
            try:
                interaction = self._cliente.interactions.create(
                    model=self._modelo,
                    input=[
                        {
                            "type": "document",
                            "uri": arquivo.uri,
                            "mime_type": arquivo.mime_type,
                        },
                        {
                            "type": "text",
                            "text": prompt,
                        },
                    ],
                    response_format={
                        "type": "text",
                        "mime_type": "application/json",
                        "schema": esquema_resposta,
                    },
                )

                logger.debug("Resposta bruta do Gemini: %s", interaction.output_text)
                dados = json.loads(interaction.output_text)
                if isinstance(dados, dict) and "disciplinas" not in dados:
                    raise ValueError(
                        "Resposta incompleta do Gemini: campo disciplinas ausente."
                    )
                resultado = DocumentoAcademicoExtraido.model_validate(dados)
                if not resultado.disciplinas:
                    logger.warning(
                        "Gemini retornou zero disciplinas para %s (modelo %s). "
                        "Confira o documento e as observações: %s",
                        caminho_pdf,
                        self._modelo,
                        resultado.observacoes_documento,
                    )
                return resultado

            except errors.ServerError as exc:
                ultima_excecao = exc

                if exc.code != 503:
                    raise

                print(
                    f"Gemini indisponível (503). "
                    f"Tentativa {tentativa}/3."
                )

                if tentativa < 3:
                    time.sleep(5 * tentativa)

        raise RuntimeError(
            "O Gemini permaneceu indisponível após 3 tentativas."
        ) from ultima_excecao
