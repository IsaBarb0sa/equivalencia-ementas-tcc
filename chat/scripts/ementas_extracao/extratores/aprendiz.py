"""Formatos Aprendiz com identidade em tabela; revisão permanece obrigatória."""
import re
import pdfplumber
from ementas_extracao.comum.documento import fonte, normalizar
from .generico import analisar, extrair_segmento
from ementas_extracao.comum.registros import aproveitar_disciplinas

IMPLEMENTADO = True


def limpar(texto):
    return re.sub(r"\s+", " ", texto or "").strip()


def identidade(tabela):
    linhas = [[limpar(c) for c in row if limpar(c)] for row in tabela.extract()]
    linhas = [row for row in linhas if row]
    if len(linhas) >= 2 and [normalizar(c) for c in linhas[0]] == ["periodo", "disciplina", "carga"]:
        if len(linhas[1]) == 3:
            _, nome, carga = linhas[1]
            m = re.fullmatch(r"(\d+)\s*h/a(?:\s+EAD)?", carga, re.I)
            if m:
                return nome, {"total": int(m[1]), "teorica": None,
                              "pratica": None, "unidade": "hora_aula"}
    celulas = [c for row in linhas for c in row]
    nomes = [c for c in celulas if normalizar(c).startswith("componente curricular ")]
    if len(nomes) != 1 or not any(normalizar(c) == "informacoes basicas" for c in celulas):
        return None
    nome = re.sub(r"^componente curricular\s+", "", nomes[0], flags=re.I)
    carga = {"total": None, "teorica": None, "pratica": None, "unidade": "nao_identificada"}
    for campo in ("teorica", "pratica", "total"):
        valores = [re.fullmatch(campo + r"\s+(\d+)", normalizar(c)) for c in celulas]
        valores = [int(m[1]) for m in valores if m]
        if len(valores) != 1:
            return None
        carga[campo] = valores[0]
    return nome, carga


def preparar(caminho):
    linhas, inicios = [], []
    with pdfplumber.open(caminho) as pdf:
        for numero, pagina in enumerate(pdf.pages, 1):
            pagina_limpa = pagina.dedupe_chars(tolerance=1)
            pagina_limpa = pagina_limpa.filter(
                lambda obj: obj.get("object_type") != "char" or obj.get("upright", True)
            )
            atuais = [{"texto": l["text"].strip(), "pagina": numero,
                       "bbox": [round(l[k], 2) for k in ("x0", "top", "x1", "bottom")],
                       "altura_pagina": pagina.height, "margem_repetida": False}
                      for l in pagina_limpa.extract_text_lines(y_tolerance=5, return_chars=False)
                      if l["text"].strip()]
            ies = [l for l in atuais if l["bbox"][1] < 160 and
                   re.search(r"(?:faculdade(?:: faculdade)? aprendiz|centro de estudos superiores aprendiz)\b",
                             normalizar(l["texto"]))]
            tabelas = [(t, identidade(t)) for t in pagina_limpa.find_tables()] if ies else []
            reconhecidas = [(t, d) for t, d in tabelas if d]
            if len(reconhecidas) > 1:
                raise ValueError(f"Aprendiz: múltiplas identidades na página {numero}; revisar.")
            if reconhecidas:
                tabela, (nome, carga) = reconhecidas[0]
                origens = [l for l in atuais if tabela.bbox[1]-1 <= l["bbox"][1] <= tabela.bbox[3]+1]
                restantes = [l for l in atuais if l not in origens]
                marcador = dict(origens[0], texto="DISCIPLINA: " + nome)
                cursos = [re.search(r"\bCurso:\s*(.+)$", l["texto"], re.I) for l in atuais
                          if l["bbox"][1] < tabela.bbox[1]]
                cursos = [m[1].strip() for m in cursos if m]
                inicios.append({"indice": len(linhas), "nome": nome, "repeticoes": [],
                                "metodo": "tabela_aprendiz", "carga": carga,
                                "fontes_tabela": [fonte(l) for l in origens],
                                "instituicao": ies[0], "curso": cursos[0] if len(set(cursos)) == 1 else None,
                                "fontes_curso": [fonte(l) for l in atuais if "Curso:" in l["texto"] and l["bbox"][1] < tabela.bbox[1]]})
                atuais = [marcador] + restantes
            for l in atuais:
                n = normalizar(l["texto"])
                # Retira apenas cabeçalhos institucionais na faixa superior.
                if l["bbox"][1] < 160 and re.match(
                    r"^(?:faculdade|centro de estudos superiores|entidade mantenedora|cnpj|r\s*ua |"
                    r"credenciamento:|reconhecimento:|renovacao de reconhecimento:|portaria |departamento:)", n
                ):
                    continue
                if re.fullmatch(r"bibliografia virtual (basica|complementar)\s*:?", n):
                    l = dict(l, texto_original=l["texto"], texto=re.sub(r"\bvirtual\s+", "", l["texto"], flags=re.I))
                if n.startswith("bibliogafia basica complementar:"):
                    l = dict(l, texto_original=l["texto"], texto="BIBLIOGRAFIA: " + l["texto"].split(":", 1)[1].strip())
                l["indice"] = len(linhas)
                linhas.append(l)
            pagina.close()
    return linhas, inicios


def extrair(caminho, linhas, paginas):
    preparadas, inicios = preparar(caminho)
    if not inicios:
        resultado = analisar(linhas, paginas)
        resultado["perfil_aprendiz"] = {"situacao": "formato_nao_reconhecido", "tabelas": 0}
        return aproveitar_disciplinas(resultado)
    resultado = analisar([], paginas)
    resultado["linhas_perfil_aprendiz"] = preparadas
    registros, inconclusivos = [], []
    for i, inicio in enumerate(inicios):
        fim = inicios[i+1]["indice"] if i+1 < len(inicios) else len(preparadas)
        r = extrair_segmento(preparadas, inicio, fim, len(registros)+1)
        r["dados"]["carga_horaria"] = inicio["carga"]
        r["dados"]["instituicao"] = inicio["instituicao"]["texto"].removeprefix("Faculdade: ")
        r["inicio"] = inicio["fontes_tabela"][0]
        r["evidencias"]["disciplina"] = inicio["fontes_tabela"]
        r["evidencias"]["carga_horaria"] = inicio["fontes_tabela"]
        r["evidencias"]["instituicao"] = [fonte(inicio["instituicao"])]
        if inicio["curso"]:
            r["dados"]["curso"] = inicio["curso"]
            r["evidencias"]["curso"] = inicio["fontes_curso"]
        r["avisos"] = [v for v in r["avisos"] if v != "instituicao_nao_localizado"
                       and not (v == "curso_nao_localizado" and inicio["curso"])
                       and not (v == "carga_teorica_ou_pratica_nao_localizada"
                                and inicio["carga"]["teorica"] is not None
                                and inicio["carga"]["pratica"] is not None)]
        c = inicio["carga"]
        if c["teorica"] is not None and c["teorica"] + c["pratica"] != c["total"]:
            r["avisos"].append("soma_teorica_pratica_divergente")
        if r["criterios"]["conteudo_academico"] and c["total"] is not None:
            r["identificacao"] = "ementa_identificada"
        else:
            r["avisos"].append("identidade_sem_conteudo_academico_suficiente")
        destino = registros if r["identificacao"] == "ementa_identificada" else inconclusivos
        destino.append(r)
    resultado["ementas"] = registros
    resultado["candidatos_inconclusivos"] = inconclusivos
    resultado["perfil_aprendiz"] = {"situacao": "tabelas_reconhecidas", "tabelas": len(inicios)}
    if registros:
        resultado["classificacao"].update(resultado="contem_ementas", motivo="Identidades em tabelas Aprendiz e conteúdo acadêmico reconhecidos.")
    return aproveitar_disciplinas(resultado)
