import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import BinaryIO, Protocol
from uuid import uuid4

from pypdf import PdfReader


MAX_ARQUIVOS = 10
MAX_BYTES_ARQUIVO = 20 * 1024 * 1024
MAX_BYTES_TOTAL = 50 * 1024 * 1024
TAMANHO_BLOCO = 1024 * 1024


class ErroRecebimento(ValueError):
    pass


@dataclass
class ArquivoRecebido:
    nome: str
    stream: BinaryIO


@dataclass(frozen=True)
class DocumentoPreparado:
    nome: str
    caminho_temporario: Path
    hash_sha256: str
    tamanho: int
    paginas: int


@dataclass(frozen=True)
class SolicitacaoRecebida:
    protocolo: str
    status: str
    quantidade_documentos: int


class RepositorioSolicitacoes(Protocol):
    def curso_disponivel(self, curso_id: int, instituicao_id: int) -> bool:
        ...


    def criar(
        self,
        protocolo: str,
        curso_id: int,
        candidato_usuario_id: int,
    ) -> int:
        ...

    def obter_ou_criar_documento(
        self,
        *,
        nome: str,
        uri: str,
        hash_sha256: str,
        tamanho: int,
        paginas: int,
    ) -> int:
        ...

    def vincular_documento(
        self,
        solicitacao_id: int,
        documento_id: int,
        nome_enviado: str,
    ) -> None:
        ...


class ReceberSolicitacao:
    def __init__(
        self,
        repository: RepositorioSolicitacoes,
        diretorio: Path,
    ) -> None:
        self._repository = repository
        self._diretorio = diretorio.resolve()


    def executar(
        self,
        *,
        curso_id: int,
        instituicao_id: int,
        candidato_usuario_id: int,
        arquivos: list[ArquivoRecebido],
    ) -> SolicitacaoRecebida:
        if candidato_usuario_id <= 0:
            raise ErroRecebimento(
                "O candidato responsável pela solicitação é inválido."
            )

        if not 1 <= len(arquivos) <= MAX_ARQUIVOS:
            raise ErroRecebimento("Envie entre 1 e 10 arquivos PDF.")

        self._diretorio.mkdir(parents=True, exist_ok=True)

        # Temporários ficam no mesmo disco dos arquivos finais.
        with TemporaryDirectory(dir=self._diretorio) as pasta_temporaria:
            documentos = []
            hashes = set()
            total = 0

            for indice, arquivo in enumerate(arquivos):
                nome = arquivo.nome.replace("\\", "/").rsplit("/", 1)[-1]

                if (
                    not nome
                    or len(nome) > 260
                    or not nome.lower().endswith(".pdf")
                    or any(ord(caractere) < 32 for caractere in nome)
                ):
                    raise ErroRecebimento(
                        "Todos os arquivos devem ter um nome válido e extensão .pdf."
                    )

                temporario = Path(pasta_temporaria) / f"{indice}.pdf"
                tamanho = 0
                digest = hashlib.sha256()
                arquivo.stream.seek(0)

                with temporario.open("wb") as destino:
                    while bloco := arquivo.stream.read(TAMANHO_BLOCO):
                        tamanho += len(bloco)
                        total += len(bloco)

                        if tamanho > MAX_BYTES_ARQUIVO:
                            raise ErroRecebimento(
                                f"{nome}: o limite por arquivo é de 20 MB."
                            )

                        if total > MAX_BYTES_TOTAL:
                            raise ErroRecebimento(
                                "O total dos arquivos deve ser de até 50 MB."
                            )

                        digest.update(bloco)
                        destino.write(bloco)

                if tamanho == 0:
                    raise ErroRecebimento(f"{nome}: o arquivo está vazio.")

                try:
                    with temporario.open("rb") as entrada:
                        if b"%PDF-" not in entrada.read(1024):
                            raise ErroRecebimento(
                                f"{nome}: o conteúdo não foi reconhecido como PDF."
                            )

                        entrada.seek(0)
                        leitor = PdfReader(entrada, strict=False)

                        if leitor.is_encrypted:
                            raise ErroRecebimento(
                                f"{nome}: envie uma cópia do PDF sem criptografia."
                            )

                        paginas = len(leitor.pages)

                        if paginas == 0:
                            raise ErroRecebimento(
                                f"{nome}: o PDF não possui páginas."
                            )
                except ErroRecebimento:
                    raise
                except Exception as exc:
                    raise ErroRecebimento(
                        f"{nome}: não foi possível ler a estrutura do PDF."
                    ) from exc

                hash_sha256 = digest.hexdigest()

                if hash_sha256 in hashes:
                    raise ErroRecebimento(
                        f"{nome}: o mesmo conteúdo foi enviado mais de uma vez."
                    )

                hashes.add(hash_sha256)
                documentos.append(
                    DocumentoPreparado(
                        nome=nome,
                        caminho_temporario=temporario,
                        hash_sha256=hash_sha256,
                        tamanho=tamanho,
                        paginas=paginas,
                    )
                )

            # Valida todos os arquivos antes de iniciar as gravações no banco.
            if not self._repository.curso_disponivel(curso_id, instituicao_id):
                raise ErroRecebimento(
                    "O curso não está disponível para a instituição de destino."
                )

            protocolo = str(uuid4())
            solicitacao_id = self._repository.criar(
                protocolo=protocolo,
                curso_id=curso_id,
                candidato_usuario_id=candidato_usuario_id,
            )


            # Ordem estável também reduz conflitos entre uploads concorrentes.
            for documento in sorted(documentos, key=lambda item: item.hash_sha256):
                caminho_final = self._diretorio / f"{documento.hash_sha256}.pdf"

                # O nome final depende do conteúdo, nunca do nome enviado.
                os.replace(documento.caminho_temporario, caminho_final)

                documento_id = self._repository.obter_ou_criar_documento(
                    nome=documento.nome,
                    uri=str(caminho_final),
                    hash_sha256=documento.hash_sha256,
                    tamanho=documento.tamanho,
                    paginas=documento.paginas,
                )

                self._repository.vincular_documento(
                    solicitacao_id,
                    documento_id,
                    documento.nome,
                )

            return SolicitacaoRecebida(
                protocolo=protocolo,
                status="RECEBIDA",
                quantidade_documentos=len(documentos),
            )