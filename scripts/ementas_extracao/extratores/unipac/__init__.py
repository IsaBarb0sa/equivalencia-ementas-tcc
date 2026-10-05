"""Perfil UNIPAC: planos de aprendizagem já presentes no projeto.

A seleção não atribui instituição aos dados nem comprova o formato do PDF.
"""
def extrair(caminho, linhas, paginas):
    from ..generico import analisar
    from .adaptadores import aplicar_perfil_aprendizagem
    return aplicar_perfil_aprendizagem(caminho, linhas, analisar(linhas, paginas))
