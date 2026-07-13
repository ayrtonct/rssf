-- Renomeia a coluna de data usada pela estrutura antiga
-- para o nome esperado pelo backend atual.

ALTER TABLE medicoes
RENAME COLUMN created_at TO data_hora;
