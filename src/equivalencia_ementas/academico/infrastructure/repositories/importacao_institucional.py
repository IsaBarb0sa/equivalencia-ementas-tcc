import hashlib
import json
from datetime import datetime, UTC

from sqlalchemy import MetaData, Table, select

from equivalencia_ementas.academico.domain.entities import (
    Ementa,
    StatusEmenta,
)


def serializar(valor):
    return json.dumps(
        valor,
        ensure_ascii=False,
        sort_keys=True,
        allow_nan=False,
        default=str,
    )


def importar(
    session_factory,
    documento,
    fonte,
    *,
    matriz_id,
    codigo,
    nome,
    natureza,
    periodo,
    responsavel,
    gravar=False,
    atualizar=False,
    substituir_ausentes=False,
):
    disciplinas = documento["disciplinas"]

    if len(disciplinas) != 1:
        raise ValueError(
            "Este comando exige exatamente uma disciplina por PDF."
        )

    d = disciplinas[0]

    if d["tipo_ocorrencia"] != "CURRICULAR":
        raise ValueError(
            "Confirme a ocorrência curricular antes de importar."
        )

    def normalizar(s):
        return " ".join(s.split()).casefold()

    if normalizar(d["nome"]) != normalizar(nome):
        raise ValueError(
            "O nome extraído difere do nome de destino informado."
        )

    codigo = codigo.strip().upper()
    responsavel = responsavel.strip()

    if (
        not codigo
        or len(codigo) > 50
        or not responsavel
        or len(responsavel) > 200
    ):
        raise ValueError("Código ou responsável inválido.")

    if natureza not in (
        "OBRIGATORIA", "OPTATIVA", "ELETIVA", "OUTRA"
    ):
        raise ValueError("Natureza inválida.")

    if periodo is not None and not 1 <= periodo <= 20:
        raise ValueError("Período deve estar entre 1 e 20.")

    if len(nome.strip()) > 200:
        raise ValueError("Nome deve ter até 200 caracteres.")

    with session_factory.begin() as s:
        meta = MetaData()

        def tabela(n, schema="academico"):
            return Table(
                n,
                meta,
                schema=schema,
                autoload_with=s.connection(),
                resolve_fks=False,
            )

        def um(t, *condicoes):
            q = (
                select(t)
                .where(*condicoes)
                .with_hint(t, "WITH (UPDLOCK, HOLDLOCK)", "mssql")
            )
            return s.execute(q).mappings().one_or_none()

        def inserir(t, valores):
            return s.execute(
                t.insert().values(**valores)
            ).inserted_primary_key[0]

        m, c, i = (
            tabela(n)
            for n in ("MatrizCurricular", "Curso", "Instituicao")
        )

        matriz = um(m, m.c.MatrizCurricularId == matriz_id)

        if not matriz or matriz["Status"] not in ("RASCUNHO", "ATIVA"):
            raise ValueError("Matriz inexistente ou indisponível.")

        curso = um(c, c.c.CursoId == matriz["CursoId"])
        inst = um(i, i.c.InstituicaoId == curso["InstituicaoId"])

        if not curso["Ativo"] or not inst["Ativa"]:
            raise ValueError("Curso ou instituição inativos.")

        td, tm, te = (
            tabela(n)
            for n in ("Disciplina", "MatrizDisciplina", "Ementa")
        )

        disc = um(
            td,
            td.c.InstituicaoId == inst["InstituicaoId"],
            td.c.Codigo == codigo,
        )

        if disc and (
            not disc["Ativa"]
            or normalizar(disc["Nome"]) != normalizar(nome)
        ):
            raise ValueError(
                "Código de disciplina existente com nome "
                "diferente ou inativo."
            )

        if not disc and um(
            td,
            td.c.InstituicaoId == inst["InstituicaoId"],
            td.c.Nome == nome,
        ):
            raise ValueError(
                "Nome já cadastrado com outro código; confira o cadastro."
            )

        vinc = (
            um(
                tm,
                tm.c.MatrizCurricularId == matriz_id,
                tm.c.DisciplinaId == disc["DisciplinaId"],
            )
            if disc else None
        )

        if vinc and (
            not vinc["Ativa"]
            or vinc["Natureza"] != natureza
            or (
                periodo is not None
                and vinc["PeriodoSugerido"] != periodo
            )
        ):
            raise ValueError(
                "Vínculo inativo ou período/natureza divergentes."
            )

        if not vinc and matriz["Status"] != "RASCUNHO":
            raise ValueError("Novo vínculo exige matriz RASCUNHO.")

        antiga = (
            um(
                te,
                te.c.MatrizDisciplinaId == vinc["MatrizDisciplinaId"],
                te.c.Versao == "INSTITUCIONAL",
            )
            if vinc else None
        )

        if vinc and not antiga and um(
            te,
            te.c.MatrizDisciplinaId == vinc["MatrizDisciplinaId"],
        ):
            raise ValueError(
                "Já existe ementa com outra versão; "
                "revise antes de criar outra."
            )

        tf = tabela("DocumentoFonte", "processamento")
        tr = tabela("ResultadoExtracao", "processamento")

        origem = um(tf, tf.c.HashSha256 == fonte["sha256"])

        identidade = {
            "matriz": matriz_id,
            "codigo": codigo,
            "documento": documento,
            "modelo": fonte["modelo"],
            "cache": fonte["cache"],
            "substituir_ausentes": substituir_ausentes,
        }

        chave = "inst1-" + hashlib.sha256(
            serializar(identidade).encode()
        ).hexdigest()[:40]

        anterior_resultado = (
            um(
                tr,
                tr.c.DocumentoFonteId == origem["DocumentoFonteId"],
                tr.c.VersaoExtrator == chave,
                tr.c.NumeroEmenta == 1,
            )
            if origem else None
        )

        if anterior_resultado:
            if anterior_resultado["Status"] != "IMPORTADO":
                raise ValueError("Resultado existente exige revisão.")

            return {
                "situacao": "ja_processado",
                "ementa_id": anterior_resultado["EmentaId"],
            }

        to, tb, tp, tc = (
            tabela(n)
            for n in (
                "ObjetivoEmenta",
                "Bibliografia",
                "ConteudoProgramatico",
                "EmentaCurso",
            )
        )

        def filhos(t):
            if not antiga:
                return []

            q = (
                select(t)
                .where(t.c.EmentaId == antiga["EmentaId"])
                .order_by(t.c.Ordem)
            )
            return [dict(r) for r in s.execute(q).mappings()]

        antes = {
            "ementa": dict(antiga) if antiga else None,
            "objetivos": filhos(to),
            "bibliografia": filhos(tb),
            "conteudo": filhos(tp),
        }

        pares_o = {
            "geral": "GERAL",
            "especificos": "ESPECIFICO",
            "nao_classificados": "NAO_CLASSIF",
        }
        pares_b = {
            "basica": "BASICA",
            "complementar": "COMPLEMENTAR",
            "nao_classificada": "OUTRA",
        }

        def manter(novo, velho):
            if novo is None and not substituir_ausentes:
                return velho
            return novo

        dados = json.loads(serializar(d))

        if antiga:
            dados["ementa"] = manter(
                dados["ementa"], antiga["Resumo"]
            )
            dados["competencias_habilidades"] = manter(
                dados["competencias_habilidades"],
                antiga["CompetenciasHabilidades"],
            )
            dados["conteudo_programatico"] = manter(
                dados["conteudo_programatico"],
                "\n".join(
                    r["TextoOriginal"] for r in antes["conteudo"]
                ) or None,
            )

            for campo, pares, registros, coluna in (
                ("objetivos", pares_o, antes["objetivos"], "Texto"),
                (
                    "bibliografia",
                    pares_b,
                    antes["bibliografia"],
                    "ReferenciaTexto",
                ),
            ):
                for k, tipo in pares.items():
                    velho = "\n".join(
                        r[coluna]
                        for r in registros
                        if r["Tipo"] == tipo
                    ) or None
                    dados[campo][k] = manter(dados[campo][k], velho)

            sem_carga = all(
                dados["carga_horaria"][k] is None
                for k in ("total", "teorica", "pratica")
            )

            if sem_carga and not substituir_ausentes:
                dados["carga_horaria"] = {
                    "total": antiga["CargaHorariaDeclarada"],
                    "teorica": antiga["CargaHorariaTeorica"],
                    "pratica": antiga["CargaHorariaPratica"],
                    "unidade": antiga["UnidadeCargaHoraria"],
                }

        carga = dados["carga_horaria"]
        unidade = carga["unidade"] or "NAO_INFO"

        e = Ementa(
            disciplina_id=disc["DisciplinaId"] if disc else 1,
            versao="INSTITUCIONAL",
            status=StatusEmenta.EM_REVISAO,
            resumo=dados["ementa"],
            competencias_habilidades=dados["competencias_habilidades"],
            carga_horaria_declarada=carga["total"],
            carga_horaria_teorica=carga["teorica"],
            carga_horaria_pratica=carga["pratica"],
            unidade_carga_horaria=unidade,
            unidade_carga_teorica=unidade,
            unidade_carga_pratica=unidade,
        )

        valores = {
            "Resumo": e.resumo,
            "CompetenciasHabilidades": e.competencias_habilidades,
            "CargaHorariaDeclarada": e.carga_horaria_declarada,
            "CargaHorariaTeorica": e.carga_horaria_teorica,
            "CargaHorariaPratica": e.carga_horaria_pratica,
            "UnidadeCargaHoraria": unidade,
            "UnidadeCargaTeorica": unidade,
            "UnidadeCargaPratica": unidade,
            "CargaHorariaNormalizadaMin": e.carga_horaria_normalizada_min,
            "Status": "EM_REVISAO",
            "PublicadaEm": None,
        }

        if not gravar:
            return {
                "situacao": "simulacao",
                "acao": "atualizar" if antiga else "cadastrar",
                "destino": {
                    "instituicao": inst["Nome"],
                    "curso": curso["Nome"],
                    "matriz": matriz["Codigo"],
                    "disciplina": codigo,
                },
                "antes": antes,
                "depois": dados,
            }

        if antiga and not atualizar:
            raise ValueError(
                "Ementa existente. Use --atualizar "
                "após conferir a simulação."
            )

        if antiga and antiga["Status"] == "ARQUIVADA":
            raise ValueError("Ementa arquivada não será alterada.")

        agora = datetime.now(UTC).replace(tzinfo=None)

        disc_id = (
            disc["DisciplinaId"]
            if disc else inserir(
                td,
                {
                    "InstituicaoId": inst["InstituicaoId"],
                    "Codigo": codigo,
                    "Nome": nome.strip(),
                    "Ativa": True,
                },
            )
        )

        vinc_id = (
            vinc["MatrizDisciplinaId"]
            if vinc else inserir(
                tm,
                {
                    "MatrizCurricularId": matriz_id,
                    "DisciplinaId": disc_id,
                    "Natureza": natureza,
                    "PeriodoSugerido": periodo,
                    "Ativa": True,
                },
            )
        )

        doc_id = (
            origem["DocumentoFonteId"]
            if origem else inserir(
                tf,
                {
                    "NomeArquivo": fonte["nome"],
                    "UriArmazenamento": fonte["uri"],
                    "HashSha256": fonte["sha256"],
                    "TamanhoBytes": fonte["bytes"],
                    "QuantidadePaginas": fonte["paginas"],
                    "MimeType": "application/pdf",
                    "Status": "PROCESSADO",
                },
            )
        )

        valores.update(
            DocumentoFonteId=doc_id,
            AtualizadoEm=agora,
        )

        if antiga:
            eid = antiga["EmentaId"]
            s.execute(
                te.update()
                .where(te.c.EmentaId == eid)
                .values(**valores)
            )
        else:
            eid = inserir(
                te,
                dict(
                    **valores,
                    DisciplinaId=disc_id,
                    MatrizDisciplinaId=vinc_id,
                    Versao="INSTITUCIONAL",
                    Idioma="pt-BR",
                ),
            )

        objetivos = [
            {"Tipo": tipo, "Texto": dados["objetivos"][k]}
            for k, tipo in pares_o.items()
            if dados["objetivos"][k]
        ]

        bibliografia = [
            {
                "Tipo": tipo,
                "ReferenciaTexto": dados["bibliografia"][k],
            }
            for k, tipo in pares_b.items()
            if dados["bibliografia"][k]
        ]

        conteudos = [
            {"TextoOriginal": linha.strip()}
            for linha in (
                dados["conteudo_programatico"] or ""
            ).splitlines()
            if linha.strip()
        ]

        for t, rows in (
            (to, objetivos),
            (tb, bibliografia),
            (tp, conteudos),
        ):
            s.execute(t.delete().where(t.c.EmentaId == eid))

            for ordem, row in enumerate(rows, 1):
                inserir(t, dict(**row, EmentaId=eid, Ordem=ordem))

        if not um(
            tc,
            tc.c.EmentaId == eid,
            tc.c.CursoId == curso["CursoId"],
        ):
            s.execute(
                tc.insert().values(
                    EmentaId=eid,
                    CursoId=curso["CursoId"],
                )
            )

        rid = inserir(
            tr,
            {
                "DocumentoFonteId": doc_id,
                "EmentaId": eid,
                "NumeroEmenta": 1,
                "VersaoExtrator": chave,
                "DadosExtraidosJson": serializar(d),
                "AuditoriaJson": serializar({
                    "fonte": fonte,
                    "resultado_original": documento,
                }),
                "DadosRevisadosJson": serializar({
                    "antes": antes,
                    "depois": dados,
                    "identidade": identidade,
                }),
                "Status": "IMPORTADO",
                "RevisadoPor": responsavel,
                "RevisadoEm": agora,
            },
        )

        return {
            "situacao": "atualizado" if antiga else "cadastrado",
            "ementa_id": eid,
            "resultado_id": rid,
        }