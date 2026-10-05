"""Perfil UNIUBE: segmentação compartilhada e tabelas em tabelas.py."""
def extrair(caminho, linhas, paginas):
    # Mantém os reconhecedores do fluxo anterior durante a migração estrutural.
    from ..generico import extrair as extrair_compartilhado
    return extrair_compartilhado(caminho, linhas, paginas)
