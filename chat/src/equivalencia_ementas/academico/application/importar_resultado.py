"""Contrato de revisão e validação sem dependência de SQLAlchemy."""
from copy import deepcopy
from decimal import Decimal, InvalidOperation
import hashlib
import json
from typing import Protocol
from equivalencia_ementas.academico.domain.entities import Ementa, StatusEmenta, UnidadeCargaHoraria


def json_canonico(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, allow_nan=False)


def hash_origem(resultado):
    conteudo={k:resultado[k] for k in ('ResultadoExtracaoId','DocumentoFonteId','NumeroEmenta',
        'VersaoExtrator','DadosExtraidosJson','AuditoriaJson')}
    return hashlib.sha256(json_canonico(conteudo).encode('utf-8')).hexdigest()


def gerar_formulario(resultado):
    original=json.loads(resultado['DadosExtraidosJson'])
    dados=original['dados'] if isinstance(original.get('dados'),dict) else original
    return {'formato':1,'resultado_extracao_id':resultado['ResultadoExtracaoId'],
        'hash_origem':hash_origem(resultado),'revisado_por':None,'confirmado':False,
        'cadastro':{'instituicao_codigo':None,'curso_codigo':None,'curso_nivel':None,
            'curso_modalidade':None,'disciplina_codigo':None,'versao_ementa':None},
        'dados':deepcopy(dados)}


def texto(valor, nome, limite=None, obrigatorio=False):
    if valor is None and not obrigatorio:return None
    if not isinstance(valor,str):raise ValueError(f'{nome}: informe um texto.')
    valor=valor.strip()
    if obrigatorio and not valor:raise ValueError(f'{nome}: preenchimento obrigatório.')
    if limite and len(valor)>limite:raise ValueError(f'{nome}: máximo de {limite} caracteres.')
    return valor or None


def decimal(valor,nome,obrigatorio=False):
    if valor is None and not obrigatorio:return None
    if isinstance(valor,bool):raise ValueError(f'{nome}: número inválido.')
    try:v=Decimal(str(valor))
    except (InvalidOperation,ValueError):raise ValueError(f'{nome}: número inválido.') from None
    if not v.is_finite() or v<0 or v>Decimal('999999.99') or v!=v.quantize(Decimal('.01')):
        raise ValueError(f'{nome}: use número não negativo com até duas casas decimais.')
    return v


def validar(form):
    if form.get('formato')!=1:raise ValueError('Formato de revisão inválido.')
    if type(form.get('resultado_extracao_id')) is not int or form['resultado_extracao_id']<=0:
        raise ValueError('Identificador inválido.')
    if form.get('confirmado') is not True:raise ValueError('Confira o formulário e defina confirmado como true.')
    texto(form.get('revisado_por'),'revisado_por',200,True)
    c=form['cadastro'];d=form['dados']
    for k,n in [('instituicao_codigo',30),('curso_codigo',30),('disciplina_codigo',50),('versao_ementa',30)]:
        texto(c.get(k),k,n,True)
    if c.get('curso_nivel') not in ('GRADUACAO','POS_GRADUACAO','TECNICO','OUTRO'):
        raise ValueError('Informe curso_nivel: GRADUACAO, POS_GRADUACAO, TECNICO ou OUTRO.')
    if c.get('curso_modalidade') not in ('PRESENCIAL','EAD','HIBRIDO','OUTRO'):
        raise ValueError('Informe curso_modalidade: PRESENCIAL, EAD, HIBRIDO ou OUTRO.')
    for k in ('instituicao','curso','disciplina'):texto(d.get(k),k,200,True)
    texto(d.get('ementa'), 'ementa')
    for k in ('competencias_habilidades', 'conteudo_programatico'):
        texto(d.get(k), k)
    for secao,chaves in [('objetivos',('geral','especificos','nao_classificados')),
                         ('bibliografia',('basica','complementar','nao_classificada'))]:
        obj=d.get(secao) or {}
        if not isinstance(obj,dict):raise ValueError(f'{secao}: esperado objeto JSON.')
        for k in chaves:texto(obj.get(k),f'{secao}.{k}')
    carga=d['carga_horaria']
    unidades={'HORA':'HORA','hora_relogio':'HORA','HORA_AULA':'HORA_AULA','hora_aula':'HORA_AULA',
        'CREDITO':'CREDITO','credito':'CREDITO','NAO_INFO':'NAO_INFO','nao_identificada':'NAO_INFO',
        'nao_declarada':'NAO_INFO','hora_declarada':'NAO_INFO'}
    unidade=unidades.get(carga.get('unidade'))
    if unidade is None:raise ValueError('Unidade não reconhecida. Use HORA, HORA_AULA, CREDITO ou NAO_INFO.')
    total=decimal(carga.get('total'),'carga total',True)
    t=decimal(carga.get('teorica'),'carga teórica');p=decimal(carga.get('pratica'),'carga prática')
    duracao=carga.get('duracao_hora_aula_minutos')
    if duracao is not None and (type(duracao) is not int or unidade!='HORA_AULA'):
        raise ValueError('Duração só se aplica a HORA_AULA e deve ser um inteiro.')
    e=Ementa(disciplina_id=1,versao=c['versao_ementa'].strip(),carga_horaria_declarada=total,
        carga_horaria_teorica=t,carga_horaria_pratica=p,unidade_carga_horaria=UnidadeCargaHoraria(unidade),
        duracao_hora_aula_minutos=duracao,resumo=d['ementa'],
        competencias_habilidades=d.get('competencias_habilidades'),status=StatusEmenta.EM_REVISAO)
    # Identificador provisório só valida a entidade; substituído pelo ID real na infraestrutura.
    return e


class RepositorioImportacao(Protocol):
    def obter(self, resultado_id:int)->dict: ...
    def importar_atomico(self, formulario:dict, simular:bool)->dict: ...


class ImportarResultado:
    def __init__(self,repositorio:RepositorioImportacao):self._repositorio=repositorio
    def preparar(self,resultado_id:int)->dict:
        return gerar_formulario(self._repositorio.obter(resultado_id))
    def executar(self,formulario:dict,simular=True)->dict:
        validar(formulario)
        return self._repositorio.importar_atomico(formulario,simular)
