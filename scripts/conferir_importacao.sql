-- Consultas somente de leitura. Selecione o banco do projeto.
SELECT DB_NAME() AS BancoAtual;
SELECT Versao, Descricao, AplicadaEm FROM governanca.VersaoSchema ORDER BY AplicadaEm;

SELECT r.ResultadoExtracaoId, r.Status AS StatusImportacao,
       r.RevisadoPor, r.RevisadoEm,
       e.EmentaId, e.Status AS StatusEmenta, e.Versao,
       i.Nome AS Instituicao, c.Nome AS Curso, d.Nome AS Disciplina,
       e.CargaHorariaDeclarada, e.CargaHorariaTeorica, e.CargaHorariaPratica,
       e.UnidadeCargaHoraria, e.MatrizDisciplinaId
FROM processamento.ResultadoExtracao AS r
LEFT JOIN academico.Ementa AS e ON e.EmentaId=r.EmentaId
LEFT JOIN academico.Disciplina AS d ON d.DisciplinaId=e.DisciplinaId
LEFT JOIN academico.Instituicao AS i ON i.InstituicaoId=d.InstituicaoId
LEFT JOIN academico.EmentaCurso AS ec ON ec.EmentaId=e.EmentaId
LEFT JOIN academico.Curso AS c ON c.CursoId=ec.CursoId
WHERE r.ResultadoExtracaoId=1;

SELECT o.* FROM academico.ObjetivoEmenta AS o
JOIN processamento.ResultadoExtracao AS r ON r.EmentaId=o.EmentaId
WHERE r.ResultadoExtracaoId=1 ORDER BY o.Ordem;
SELECT b.* FROM academico.Bibliografia AS b
JOIN processamento.ResultadoExtracao AS r ON r.EmentaId=b.EmentaId
WHERE r.ResultadoExtracaoId=1 ORDER BY b.Ordem;
SELECT cp.* FROM academico.ConteudoProgramatico AS cp
JOIN processamento.ResultadoExtracao AS r ON r.EmentaId=cp.EmentaId
WHERE r.ResultadoExtracaoId=1 ORDER BY cp.Ordem;
