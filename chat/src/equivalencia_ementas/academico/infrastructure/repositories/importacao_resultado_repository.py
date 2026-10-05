"""Adaptador SQLAlchemy Core: reflexão e transação única no banco existente."""
from datetime import UTC, datetime
import json
from sqlalchemy import MetaData, Table, select
from equivalencia_ementas.academico.application.importar_resultado import validar,hash_origem,json_canonico


def bloquear(stmt,tabela):
    return stmt.with_hint(tabela,'WITH (UPDLOCK, HOLDLOCK)','mssql')


def nome_comparavel(nome):return ' '.join(nome.split()).casefold()


class SqlAlchemyImportacaoResultado:
    def __init__(self,session_factory):self._factory=session_factory

    @staticmethod
    def tabela(session,metadata,nome,schema='academico'):
        return Table(nome,metadata,schema=schema,autoload_with=session.connection(),resolve_fks=False)

    def obter(self,resultado_id):
        with self._factory() as session:
            t=self.tabela(session,MetaData(),'ResultadoExtracao','processamento')
            row=session.execute(select(t).where(t.c.ResultadoExtracaoId==resultado_id)).mappings().one_or_none()
            if row is None:raise ValueError('Resultado de extração não encontrado.')
            return dict(row)

    def importar_atomico(self,formulario,simular=False):
        entidade=validar(formulario)
        with self._factory.begin() as session:
            meta=MetaData()
            r=self.tabela(session,meta,'ResultadoExtracao','processamento')
            row=session.execute(bloquear(select(r).where(r.c.ResultadoExtracaoId==formulario['resultado_extracao_id']),r)).mappings().one_or_none()
            if row is None:raise ValueError('Resultado não encontrado.')
            if hash_origem(row)!=formulario.get('hash_origem'):
                raise ValueError('Origem mudou ou formulário pertence a outro resultado. Gere nova revisão.')
            if row['Status']=='IMPORTADO':
                revisao=json.loads(row['DadosRevisadosJson'])
                if revisao.get('formulario')!=formulario:
                    raise ValueError('Resultado já importado com outra revisão; nenhuma alteração foi feita.')
                return {'situacao':'ja_importado','ementa_id':row['EmentaId'],**revisao['vinculos']}
            if row['Status'] not in ('PENDENTE','REVISADO'):
                raise ValueError('Resultado rejeitado ou status incompatível com importação.')
            d=formulario['dados'];c=formulario['cadastro'];acoes=[]
            def resolver(nome,idcol,valores,identidade,ativo):
                t=self.tabela(session,meta,nome)
                consulta=select(t).where(*(t.c[k]==v for k,v in identidade.items()))
                existente=session.execute(bloquear(consulta,t)).mappings().one_or_none()
                if existente:
                    if not existente[ativo]:raise ValueError(f'{nome} existente está inativo.')
                    campos=['Nome']+(['Nivel','Modalidade'] if nome=='Curso' else [])
                    if any(nome_comparavel(str(existente[k]))!=nome_comparavel(str(valores[k])) for k in campos):
                        raise ValueError(f'{nome}: código já existe com dados diferentes. Confira a revisão.')
                    acoes.append(f'Reutilizar {nome} {existente[idcol]}')
                    return existente[idcol]
                # Não unir automaticamente por nome nem criar possível duplicata sem conferência.
                filtros=[t.c.Nome==valores['Nome']]
                if 'InstituicaoId' in identidade:filtros.append(t.c.InstituicaoId==identidade['InstituicaoId'])
                mesmo_nome=session.execute(bloquear(select(t.c[idcol]).where(*filtros),t)).first()
                if mesmo_nome:raise ValueError(f'{nome}: nome já cadastrado com outro código ou sem código. Consulte o cadastro antes de importar.')
                acoes.append(f'Criar {nome}: {valores["Nome"]}')
                if simular:return -1
                return session.execute(t.insert().values(**valores)).inserted_primary_key[0]

            instcodigo=c['instituicao_codigo'].strip().upper()
            inst=resolver('Instituicao','InstituicaoId',{'Codigo':instcodigo,'Nome':d['instituicao'].strip(),'Ativa':True},
                {'Codigo':instcodigo},'Ativa')
            cursocodigo=c['curso_codigo'].strip().upper()
            curso=resolver('Curso','CursoId',{'InstituicaoId':inst,'Codigo':cursocodigo,'Nome':d['curso'].strip(),
                'Nivel':c['curso_nivel'],'Modalidade':c['curso_modalidade'],'Ativo':True},
                {'InstituicaoId':inst,'Codigo':cursocodigo},'Ativo')
            disccodigo=c['disciplina_codigo'].strip().upper()
            disc=resolver('Disciplina','DisciplinaId',{'InstituicaoId':inst,'Codigo':disccodigo,
                'Nome':d['disciplina'].strip(),'Ativa':True}, {'InstituicaoId':inst,'Codigo':disccodigo},'Ativa')
            e=self.tabela(session,meta,'Ementa')
            existente=session.execute(bloquear(select(e.c.EmentaId).where(e.c.DisciplinaId==disc,
                e.c.MatrizDisciplinaId.is_(None),e.c.Versao==entidade.versao),e)).first()
            if existente:raise ValueError('Já existe ementa dessa disciplina, sem matriz e com a mesma versão. Não foi sobrescrita.')
            # Refletir dependências também na simulação para detectar migration ausente.
            objetivos=self.tabela(session,meta,'ObjetivoEmenta')
            bibliografia=self.tabela(session,meta,'Bibliografia')
            conteudos=self.tabela(session,meta,'ConteudoProgramatico')
            vinculo=self.tabela(session,meta,'EmentaCurso')
            acoes.append('Criar ementa EM_REVISAO e conteúdos; vincular ao curso; marcar resultado IMPORTADO')
            if simular:return {'situacao':'simulacao_sem_gravacao','acoes':acoes}
            ementa_id=session.execute(e.insert().values(DisciplinaId=disc,MatrizDisciplinaId=None,
                DocumentoFonteId=row['DocumentoFonteId'],Versao=entidade.versao,Idioma='pt-BR',
                Resumo=entidade.resumo,CargaHorariaDeclarada=entidade.carga_horaria_declarada,
                CargaHorariaTeorica=entidade.carga_horaria_teorica,CargaHorariaPratica=entidade.carga_horaria_pratica,
                CompetenciasHabilidades=entidade.competencias_habilidades,
                UnidadeCargaHoraria=entidade.unidade_carga_horaria.value,
                DuracaoHoraAulaMinutos=entidade.duracao_hora_aula_minutos,
                CargaHorariaNormalizadaMin=None,Status='EM_REVISAO')).inserted_primary_key[0]
            session.execute(vinculo.insert().values(EmentaId=ementa_id,CursoId=curso))
            ordem=0
            for campo,tipo in [('geral','GERAL'),('especificos','ESPECIFICO'),('nao_classificados','NAO_CLASSIF')]:
                valor=(d.get('objetivos') or {}).get(campo)
                if valor and valor.strip():
                    ordem+=1;session.execute(objetivos.insert().values(EmentaId=ementa_id,Ordem=ordem,Tipo=tipo,Texto=valor.strip()))
            ordem=0
            for campo,tipo in [('basica','BASICA'),('complementar','COMPLEMENTAR'),('nao_classificada','OUTRA')]:
                valor=(d.get('bibliografia') or {}).get(campo)
                if valor and valor.strip():
                    ordem+=1;session.execute(bibliografia.insert().values(EmentaId=ementa_id,Ordem=ordem,Tipo=tipo,ReferenciaTexto=valor.strip()))
            if d.get('conteudo_programatico') and d['conteudo_programatico'].strip():
                session.execute(conteudos.insert().values(EmentaId=ementa_id,Ordem=1,TextoOriginal=d['conteudo_programatico'].strip()))
            ids={'instituicao_id':inst,'curso_id':curso,'disciplina_id':disc}
            session.execute(r.update().where(r.c.ResultadoExtracaoId==row['ResultadoExtracaoId']).values(
                Status='IMPORTADO',EmentaId=ementa_id,RevisadoPor=formulario['revisado_por'].strip(),
                RevisadoEm=datetime.now(UTC).replace(tzinfo=None),
                DadosRevisadosJson=json_canonico({'formulario':formulario,'vinculos':ids})))
            return {'situacao':'importado','ementa_id':ementa_id,**ids}
