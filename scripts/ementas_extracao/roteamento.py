"""Escolha explícita de perfil, sem inferir a instituição do documento."""
from .extratores import generico, unipac, uniube, aprendiz, estacio, anhanguera_unopar

PERFIS = {
    "generico": generico,
    "unipac": unipac,
    "uniube": uniube,
    "aprendiz": aprendiz,
    "estacio": estacio,
    "anhanguera_unopar": anhanguera_unopar,
    "outros": generico,
}
PENDENTES = frozenset({ "estacio", "anhanguera_unopar"})


def selecionar(instituicao="generico"):
    if instituicao not in PERFIS:
        raise ValueError(f"Instituição/perfil desconhecido: {instituicao}")
    fallback = instituicao in PENDENTES
    usado = "generico" if fallback or instituicao == "outros" else instituicao
    return PERFIS[instituicao].extrair, {
        "instituicao_solicitada": instituicao,
        "perfil_utilizado": usado,
        "fallback_generico": fallback,
        "motivo": "perfil_especifico_pendente" if fallback else "selecao_explicita",
        "etapa": "organizacao_inicial_com_regras_compartilhadas",
    }
