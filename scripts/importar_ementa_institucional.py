import argparse
import hashlib
import tempfile
from pathlib import Path

from pypdf import PdfReader

from equivalencia_ementas.infraestrutura.ia.cliente_gemini import (
    ExtratorGemini,
)
from equivalencia_ementas.infraestrutura.ia.processador_documento import (
    ProcessadorDocumentoIA,
    VERSAO_CACHE_GEMINI,
)
from equivalencia_ementas.academico.application.normalizar_extracao import (
    normalizar_extracao,
)
from equivalencia_ementas.academico.infrastructure.repositories.importacao_institucional import (
    importar,
    serializar,
)


def main():
    p = argparse.ArgumentParser()

    p.add_argument("--pdf", type=Path, required=True)
    p.add_argument("--matriz-id", type=int, required=True)
    p.add_argument("--codigo", required=True)
    p.add_argument("--nome", required=True)
    p.add_argument(
        "--natureza",
        required=True,
        choices=["OBRIGATORIA", "OPTATIVA", "ELETIVA", "OUTRA"],
    )
    p.add_argument("--periodo", type=int)
    p.add_argument("--responsavel", required=True)
    p.add_argument("--gravar", action="store_true")
    p.add_argument("--atualizar", action="store_true")
    p.add_argument("--substituir-ausentes", action="store_true")

    a = p.parse_args()

    raw = a.pdf.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()

    destino = (
        Path("data/documentos_fonte").resolve() / f"{sha}.pdf"
    )

    # Extrair uma cópia estável: o hash e o documento analisado
    # precisam representar os mesmos bytes.
    with tempfile.TemporaryDirectory() as tmp:
        copia = Path(tmp) / "documento.pdf"
        copia.write_bytes(raw)

        paginas = len(PdfReader(copia).pages)

        extrator = ExtratorGemini()
        proc = ProcessadorDocumentoIA(
            extrator,
            tamanho_bloco=15,
            sobreposicao=2,
        )

        original = proc.processar(copia)
        documento = normalizar_extracao(
            original
        ).model_dump(mode="json")

    if a.gravar:
        destino.parent.mkdir(parents=True, exist_ok=True)

        try:
            with destino.open("xb") as f:
                f.write(raw)
        except FileExistsError:
            if destino.read_bytes() != raw:
                raise ValueError(
                    "Arquivo de origem armazenado está inconsistente."
                )

    fonte = {
        "nome": a.pdf.name,
        "uri": destino.as_uri(),
        "sha256": sha,
        "bytes": len(raw),
        "paginas": paginas,
        "modelo": extrator.modelo,
        "cache": VERSAO_CACHE_GEMINI,
        "extracao_bruta": original.model_dump(mode="json"),
    }

    from equivalencia_ementas.shared.database.session import (
        SessionFactory,
    )

    resultado = importar(
        SessionFactory,
        documento,
        fonte,
        matriz_id=a.matriz_id,
        codigo=a.codigo,
        nome=a.nome,
        natureza=a.natureza,
        periodo=a.periodo,
        responsavel=a.responsavel,
        gravar=a.gravar,
        atualizar=a.atualizar,
        substituir_ausentes=a.substituir_ausentes,
    )

    print(serializar(resultado))


if __name__ == "__main__":
    main()