"""Extrator estrutural experimental. Python >=3.11; dependência: pdfplumber.

Não grava no banco, não faz OCR e não infere dados ausentes.
O JSON preserva texto e regiões de origem para revisão humana.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path
from importlib.metadata import version

import pdfplumber

VERSAO = "0.2.0"


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto)
    return re.sub(r"\s+", " ", "".join(c for c in texto if not unicodedata.combining(c))).strip().lower()


ROTULOS = {
    "ementa": "ementa",
    "objetivos do curso": "objetivos_curso",
    "objetivos de aprendizagem": "objetivos_aprendizagem",
    "objetivos de ensino / aprendizagem": "objetivos_aprendizagem",
    "objetivo geral": "objetivo_geral_disciplina",
    "objetivos especificos": "objetivos_especificos_disciplina",
    "competencias e habilidades": "competencias_habilidades",
    "conhecimentos e habilidades": "competencias_habilidades",
    "bibliografia basica": "bibliografia_basica",
    "bibliografia complementar": "bibliografia_complementar",
    "conteudo programatico": "conteudo_programatico",
    "conteudo": "conteudo_programatico",
    "estrategias de ensinagem": "_estrategias",
    "recursos didaticos": "_recursos",
    "avaliacao da aprendizagem": "_avaliacao",
    "articulacao com outras disciplinas": "_articulacao",
    "periodicos": "_periodicos",
    "leituras complementares": "_leituras",
    "bibliografias": "_bibliografias",
    "justificativa de adequacao da bibliografia da unidade curricular": "_justificativa",
    "contribuicoes do componente curricular para o perfil do egresso": "_perfil",
}


def campo() -> dict:
    return {"valor": None, "status": "nao_localizado", "rotulos": [], "fontes": []}


def identificar(texto: str) -> str | None:
    chave = normalizar(texto)
    # Alguns modelos imprimem a referência normativa na mesma célula do título.
    # Só remove o sufixo nesse cabeçalho, não em parágrafos do conteúdo.
    if chave.replace(' ','').startswith(('competencias','conhecimentos')):
        chave = re.split(r'\(art\.',chave,maxsplit=1)[0].strip()
    chave = re.sub(r"[\d:!]+$", "", chave).strip()
    chave = re.sub(r"\s*/\s*", " / ", chave)
    direto=ROTULOS.get(chave)
    if direto:return direto
    compacto=chave.replace(' ','')
    return next((valor for rotulo,valor in ROTULOS.items() if rotulo.replace(' ','')==compacto),None)


def ler_regiao(pagina, caixa) -> str:
    # Centro do caractere evita duplicá-lo em regiões vizinhas.
    x0, y0, x1, y1 = caixa
    recorte = pagina.filter(lambda o: o.get("object_type") == "char" and
        x0 <= (o["x0"] + o["x1"]) / 2 < x1 and
        y0 <= (o["top"] + o["bottom"]) / 2 < y1)
    return (recorte.extract_text(x_tolerance=2, y_tolerance=3) or "").strip()


def fonte(pagina: int, caixa, texto: str) -> dict:
    return {"pagina": pagina, "bbox": [round(v, 2) for v in caixa], "texto_original": texto}


def adicionar(destino: dict, texto: str, origem: dict) -> None:
    if not texto.strip():
        return
    destino["fontes"].append(origem)
    destino["valor"] = "\n".join(f["texto_original"] for f in destino["fontes"])
    destino["status"] = "extraido"


def tabelas_externas(pagina):
    tabelas = sorted(pagina.find_tables(), key=lambda t: (t.bbox[2]-t.bbox[0])*(t.bbox[3]-t.bbox[1]), reverse=True)
    escolhidas = []
    for tabela in tabelas:
        a = tabela.bbox
        if a[0] < -2 or a[2] > pagina.width+2 or a[3] > pagina.height+2:
            continue
        if any(b.bbox[0]-2 <= a[0] and b.bbox[1]-2 <= a[1] and
               b.bbox[2]+2 >= a[2] and b.bbox[3]+2 >= a[3] for b in escolhidas):
            continue
        escolhidas.append(tabela)
    return sorted(escolhidas, key=lambda t: t.bbox[1])


def extrair(caminho: Path, instituicao: str | None = None) -> dict:
    nomes = ["curso", "disciplina", "instituicao"] + [v for v in ROTULOS.values() if not v.startswith("_")]
    campos = {n: campo() for n in nomes}
    cargas = {n: campo() for n in ("total", "teorica", "pratica")}
    avisos = []
    blocos = []
    cronograma = []
    ativa = None
    lateral_x = None
    colunas_cronograma = None
    ultima_pagina_cronograma = 0
    with pdfplumber.open(caminho) as pdf:
        total_paginas = len(pdf.pages)
        for numero, pagina in enumerate(pdf.pages, 1):
            texto_pagina = pagina.extract_text() or ""
            if not texto_pagina.strip():
                avisos.append(f"Página {numero} sem texto: pode ser vazia ou exigir OCR; verificar visualmente.")
                continue
            # Instituição somente se constar em texto, ou informada explicitamente.
            if campos["instituicao"]["valor"] is None:
                m = re.search(r"(?im)^.*(?:Centro Universit[aá]rio Presidente Ant[oô]nio Carlos|UNIPAC\s*[–-]\s*CAMPUS).*$", texto_pagina)
                if m:
                    adicionar(campos["instituicao"], m.group(), {"pagina": numero, "texto_original": m.group()})
            tabelas = tabelas_externas(pagina)
            if not tabelas:
                avisos.append(f"Página {numero}: texto preservado, mas nenhuma tabela reconhecida; revisar cobertura.")
                blocos.append({"pagina": numero, "tipo": "texto_sem_tabela", "texto_original": texto_pagina})
                # Fallback conservador para documento em uma coluna com títulos
                # em linhas próprias; não tenta interpretar colunas sem bordas.
                for linha in texto_pagina.splitlines():
                    chave = identificar(linha)
                    if chave in ('objetivo_geral_disciplina','objetivos_especificos_disciplina') and ativa=='objetivos_curso':
                        chave=None
                    if chave:
                        ativa=chave
                        if chave in campos:
                            campos[chave]['status']='campo_vazio' if campos[chave]['valor'] is None else campos[chave]['status']
                            campos[chave]['rotulos'].append({'pagina':numero,'texto_original':linha})
                    elif re.match(r'^(Professor|Coordenador|Assinatura)\b',linha,re.I):
                        ativa=None
                    elif ativa in campos and not re.fullmatch(r'\s*\d+\s*',linha):
                        adicionar(campos[ativa],linha,{'pagina':numero,'texto_original':linha})
                    for nome,padrao in (('curso',r'^Curso:\s*(.*)$'),('disciplina',r'^(?:Disciplina|Componente Curricular):\s*(.*)$')):
                        m=re.match(padrao,linha,re.I)
                        if m and campos[nome]['valor'] is None:
                            campos[nome]['status']='campo_vazio'
                            campos[nome]['metodo']='texto_livre'
                            if m.group(1):adicionar(campos[nome],m.group(1),{'pagina':numero,'texto_original':m.group(1)})
                continue
            for tabela in tabelas:
                bbox = tabela.bbox
                celulas = [(c, ler_regiao(pagina, c)) for c in sorted(set(tabela.cells), key=lambda c: (c[1],c[0]))]
                bruto = ler_regiao(pagina, bbox)
                blocos.append({"tipo": "tabela", **fonte(numero, bbox, bruto)})
                # Coluna temática identificada pelo cabeçalho, jamais por página ou x fixo.
                tema = next(((c,t) for c,t in celulas if normalizar(t) == "tema de estudo"), None)
                if tema:
                    c = tema[0]
                    colunas_cronograma = ((c[0]-bbox[0])/(bbox[2]-bbox[0]), (c[2]-bbox[0])/(bbox[2]-bbox[0]))
                    inicio = max(c[3], next((r.bbox[3] for r in tabela.rows if r.bbox[1] <= c[1] < r.bbox[3]), c[3]))
                    ativa = None
                else:
                    inicio = bbox[1]
                # Continuação aceita apenas em página adjacente e tabela larga (paisagem).
                continua = (colunas_cronograma is not None and numero <= ultima_pagina_cronograma+1 and
                            pagina.width > pagina.height and bbox[2]-bbox[0] > pagina.width*.65)
                if tema or continua:
                    ultima_pagina_cronograma = numero
                    esquerda = bbox[0] + colunas_cronograma[0]*(bbox[2]-bbox[0])
                    direita = bbox[0] + colunas_cronograma[1]*(bbox[2]-bbox[0])
                    linhas = tabela.rows
                    for indice, row in enumerate(linhas):
                        linha_completa = ler_regiao(pagina,row.bbox)
                        if re.match(r"^(Professor(?:a)?|Coordenador(?:a)?(?: de Curso)?)\s*:",linha_completa,re.I):
                            colunas_cronograma = None
                            break
                        y0, y1 = max(inicio,row.bbox[1]), row.bbox[3]
                        if indice+1 < len(linhas):
                            y1 = min(y1,linhas[indice+1].bbox[1])
                        if y1 <= y0: continue
                        texto = ler_regiao(pagina, (esquerda,y0,direita,y1))
                        identidade = ler_regiao(pagina, (bbox[0],y0,esquerda,y1))
                        if not texto or normalizar(texto) == "tema de estudo": continue
                        cronograma.append({"identificacao": identidade or None, "texto": texto,
                            "possivel_continuacao": not bool(identidade),
                            "fonte": fonte(numero,(esquerda,y0,direita,y1),texto)})
                    continue

                # Metadados, inclusive rótulo e valor em células distintas.
                for c,t in celulas:
                    for nome, padrao in (("curso",r"^Curso\s*:\s*(.*)$"),
                                         ("disciplina",r"^(?:Componente Curricular|DISCIPLINA)\s*:\s*(.*)$")):
                        m = re.match(padrao,t,re.I|re.S)
                        if not m or (campos[nome]["status"] == "extraido" and campos[nome].get('metodo')!='texto_livre'): continue
                        if campos[nome].get('metodo')=='texto_livre':campos[nome]=campo()
                        valor = m.group(1).strip()
                        regiao = c
                        if not valor:
                            vizinhos = [(b,s) for b,s in celulas if b[0] >= c[2]-2 and abs(b[1]-c[1])<3 and s.strip()]
                            if vizinhos:
                                b,s = min(vizinhos,key=lambda z:z[0][0])
                                if not re.search(r"curricular:|disciplina:|professor",s,re.I):
                                    regiao = (b[0],c[1],b[2],max(c[3],b[3]))
                                    valor = ler_regiao(pagina,regiao)
                        campos[nome]["status"] = "campo_vazio"
                        campos[nome]["rotulos"].append(fonte(numero,c,t))
                        if valor: adicionar(campos[nome],valor,fonte(numero,regiao,valor))

                # Carga: valor na mesma célula ou diretamente abaixo, alinhado à coluna.
                for c,t in celulas:
                    n = normalizar(t)
                    nome = None
                    if re.match(r"^carga horaria(?: total)?(?:\s*:\s*\d*|\s+\d+)?$",n): nome="total"
                    elif n in ("teoria","teorica"): nome="teorica"
                    elif n in ("pratica",): nome="pratica"
                    if nome is None: continue
                    achados = re.findall(r"\b\d+(?:[.,]\d+)?\b",t)
                    regiao = c
                    if not achados:
                        candidatos = [(b,s) for b,s in celulas if b[1] >= c[3]-2 and b[1]-c[3]<35 and
                                      b[0]-2 <= (c[0]+c[2])/2 <= b[2]+2 and re.fullmatch(r"\d+(?:[.,]\d+)?",s.strip())]
                        # Layout lateral: valor imediatamente à direita.
                        candidatos += [(b,s) for b,s in celulas if abs(b[0]-c[2])<3 and abs(b[1]-c[1])<3 and re.fullmatch(r"\d+(?:[.,]\d+)?",s.strip())]
                        if candidatos:
                            regiao,s = min(candidatos,key=lambda z:abs(z[0][1]-c[3]))
                            achados=[s.strip()]
                    if achados and cargas[nome]["valor"] is None:
                        adicionar(cargas[nome],achados[-1],fonte(numero,regiao,ler_regiao(pagina,regiao)))
                        cargas[nome]["valor"] = float(achados[-1].replace(",","."))

                # Âncoras são células inteiras de rótulo; subtítulos dentro do
                # texto de objetivos do curso não viram objetivos da disciplina.
                ancoras = []
                for c,t in celulas:
                    chave = identificar(t)
                    assinatura = re.match(r"^(Professor(?:a)?|Coordenador(?:a)?(?: de Curso)?)\s*:",t,re.I)
                    if chave or assinatura:
                        lateral = c[2]-c[0] < (bbox[2]-bbox[0])*.4 and c[0]<bbox[0]+5
                        ancoras.append((c,t,chave or "_assinatura",lateral))
                ancoras.sort(key=lambda a:a[0][1])

                def guardar(chave, caixa):
                    if chave not in campos or caixa[3]<=caixa[1]: return
                    t = ler_regiao(pagina,caixa)
                    adicionar(campos[chave],t,fonte(numero,caixa,t))

                if ativa:
                    limite = ancoras[0][0][1] if ancoras else bbox[3]
                    guardar(ativa,(max(bbox[0],lateral_x or bbox[0]),bbox[1],bbox[2],limite))
                for idx,(c,t,chave,lateral) in enumerate(ancoras):
                    ativa = chave
                    lateral_x = c[2] if lateral else None
                    if chave in campos:
                        campos[chave]["rotulos"].append(fonte(numero,c,t))
                        if campos[chave]["status"] == "nao_localizado": campos[chave]["status"]="campo_vazio"
                    fim = ancoras[idx+1][0][1] if idx+1<len(ancoras) else bbox[3]
                    guardar(chave,(c[2] if lateral else bbox[0],c[1] if lateral else c[3],bbox[2],fim))

    if instituicao and campos["instituicao"]["valor"] is None:
        campos["instituicao"].update(valor=instituicao,status="informado",origem="argumento_usuario")
    for nome in ("competencias_habilidades",):
        f=campos[nome]
        if f["valor"] and re.fullmatch(r"\(Art\..*?\)",f["valor"],re.S|re.I):
            f.update(valor=None,status="campo_vazio",observacao="Somente marcador de preenchimento; original preservado nas fontes.")
    if cronograma:
        avisos.append("Cronograma preservado em fragmentos, incluindo avaliações. Continuação e classificação exigem revisão; não há deduplicação automática.")
    for nome in ("curso","disciplina","ementa","objetivos_aprendizagem","competencias_habilidades"):
        if campos[nome]["status"] != "extraido": avisos.append(f"Revisar {nome}: {campos[nome]['status']}.")
    if cargas["total"]["valor"] is not None and all(cargas[k]["valor"] is not None for k in ("teorica","pratica")):
        if abs(cargas["teorica"]["valor"]+cargas["pratica"]["valor"]-cargas["total"]["valor"])>.001:
            avisos.append("Carga total difere da soma teoria + prática; verificar unidade e categorias.")
    return {"arquivo":caminho.name,"sha256":hashlib.sha256(caminho.read_bytes()).hexdigest(),
        "versao_extrator":VERSAO,"pdfplumber":version("pdfplumber"),"paginas":total_paginas,
        "status":"pendente_revisao","campos":campos,
        "carga_horaria":{"valores":cargas,"unidade":"nao_identificada","observacao":"Não converter para minutos sem confirmar a unidade no documento ou cadastro institucional."},
        "cronograma_fragmentos":cronograma,"blocos_originais":blocos,"avisos":avisos}


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entrada",type=Path,help="PDF ou pasta de PDFs")
    parser.add_argument("--saida",type=Path,default=Path("data/saida_v2"),help="Pasta dos resultados")
    parser.add_argument("--instituicao",help="Fallback informado; nunca apresentado como extraído")
    args=parser.parse_args()
    if not args.entrada.exists(): parser.error("Entrada inexistente.")
    arquivos=sorted(args.entrada.glob("*")) if args.entrada.is_dir() else [args.entrada]
    arquivos=[p for p in arquivos if p.is_file() and p.suffix.lower()==".pdf"]
    if not arquivos: parser.error("Nenhum PDF encontrado (busca não recursiva).")
    args.saida.mkdir(parents=True,exist_ok=True)
    resumo=[]
    for arquivo in arquivos:
        try:
            resultado=extrair(arquivo,args.instituicao)
            # Hash evita colisão entre nomes iguais com extensões distintas.
            destino=args.saida/(arquivo.stem+"_"+resultado["sha256"][:8]+".json")
            destino.write_text(json.dumps(resultado,ensure_ascii=False,indent=2),encoding="utf-8")
            resumo.append({"arquivo":arquivo.name,"execucao":"concluida","saida":destino.name,"avisos":resultado["avisos"]})
            print(f"OK (revisão necessária): {arquivo.name}")
        except Exception as erro:
            resumo.append({"arquivo":arquivo.name,"execucao":"falhou","erro":f"{type(erro).__name__}: {erro}"})
            print(f"FALHOU: {arquivo.name}: {erro}")
    (args.saida/"resumo_execucao.json").write_text(json.dumps(resumo,ensure_ascii=False,indent=2),encoding="utf-8")
    return int(any(r["execucao"]=="falhou" for r in resumo))


if __name__=="__main__":
    raise SystemExit(main())
