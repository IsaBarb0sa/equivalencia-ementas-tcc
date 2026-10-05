# Onde alterar cada parte

| Local | Responsabilidade |
| --- | --- |
| scripts/extrair_ementas.py | Argumentos de linha de comando e salvamento dos JSONs |
| scripts/ementas_extracao/pipeline.py | Sequência de processamento, OCR, extração e auditoria |
| scripts/ementas_extracao/roteamento.py | Escolha explícita de perfil e fallback dos perfis pendentes |
| scripts/ementas_extracao/triagem.py | Classificação documental anterior, sem mudança de regra |
| scripts/ementas_extracao/comum/documento.py | Inspeção e leitura de linhas do PDF |
| scripts/ementas_extracao/comum/ocr.py | Preparação do PDF temporário com OCR |
| scripts/ementas_extracao/comum/segmentacao.py | Títulos, identidade e início de disciplinas |
| scripts/ementas_extracao/comum/cobertura.py | Evidências e cobertura de páginas |
| scripts/ementas_extracao/comum/celulas.py | Números e coordenadas de células |
| scripts/ementas_extracao/comum/tabelas.py | Busca e associação das tabelas aos registros |
| scripts/ementas_extracao/extratores/generico.py | Interpretação compartilhada das seções |
| scripts/ementas_extracao/extratores/unipac/ | Plano de aprendizagem: adaptador, leitura estrutural, normalização e identificação por alias |
| scripts/ementas_extracao/extratores/uniube/tabelas.py | Tabela de modalidades presencial/não presencial, incluindo teoria/prática combinada |
| scripts/ementas_extracao/extratores/aprendiz.py | Ponto de entrada futuro; atualmente delega ao genérico |
| scripts/ementas_extracao/extratores/estacio.py | Ponto de entrada futuro; atualmente delega ao genérico |
| scripts/ementas_extracao/extratores/anhanguera_unopar.py | Ponto de entrada futuro; atualmente delega ao genérico |
| tests/integration/extratores/unipac/ | Seis verificações dos PDFs institucionais |
| tests/integration/extratores/uniube/ | Duas verificações das tabelas da EMENTA 15 |
| tests/integration/test_bibliografia.py | Quatro combinações de títulos e margem repetida |
| tests/unit/test_roteamento.py | Fallback explícito e recusa de perfil desconhecido |

## Compatibilidade

Os arquivos antigos documento.py, ocr.py, generico.py, segmentacao.py, cobertura.py,
tabelas.py, estrutural.py, normalizacao.py, adaptadores.py e instituicao.py continuam
na raiz de ementas_extracao. São pequenos módulos de reexportação, não cópias da
implementação. Permitem que imports antigos continuem funcionando. Altere as
implementações nas novas pastas, não esses módulos de compatibilidade.

O serviço processar continua importável de extrair_ementas, mas sua implementação
agora está em pipeline.py. Os três argumentos posicionais anteriores são preservados;
instituicao é um quarto argumento opcional.

## Evolução de um perfil

Cada extrator expõe extrair(caminho, linhas, paginas) e devolve o mesmo dicionário
de análise. A leitura e o OCR ocorrem uma vez no pipeline. Enriquecimento, evidências,
revisão e salvamento continuam compartilhados. O próximo perfil deve adicionar
regras baseadas no formato observado e testes de documentos reais antes de sair
da lista PENDENTES em roteamento.py. Para PDFs mistos, a seleção pelo usuário
continua insuficiente; a separação por blocos é uma etapa futura.
