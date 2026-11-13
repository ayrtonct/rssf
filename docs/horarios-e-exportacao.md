# Horarios e exportacao: campo e laboratorio

## Contrato implementado

- Campo: IDs 1 e 44204, cada transmissao de 30 minutos usa o INSERT individual e seu CURRENT_TIMESTAMP. Nao subtrai idades nem reconstrui lotes.
- Laboratorio: somente os nos listados em LAB_SENSOR_ID (um ou mais, separados por virgula) no LAB_GATEWAY_ID configurado aceitam `medicoes`. O gateway deve estar explicito no POST; identificacao historica por fallback nao autoriza lote. Um unico CURRENT_TIMESTAMP ancora as idades recebidas (0 a 450 minutos, ate 16 amostras). O pacote regular sai a cada 8 horas; o firmware tambem envia uma amostra no inicio do ensaio.
- O perfil de laboratorio existente continua SEM sondas: temperaturas NULL, RSSI preservado. Nao o usar como perfil de campo.
- Banco DATETIME: horario de Sao Luis, sessao MySQL -03:00 tanto no INSERT individual quanto no lote. A mudanca de sessao nao altera valores DATETIME existentes.
- API: ISO 8601 com Z, calculado a partir do DATETIME local. Relogio de servidor UTC permanece UTC. Filtros com offset convertem para DATETIME local; entradas sem offset continuam interpretadas como UTC por compatibilidade.
- Interface, datas personalizadas e CSV: Sao Luis (America/Fortaleza, UTC-03:00), independente do fuso do navegador. O CSV contem offset explicito.
- CSV: endpoint dedicado sem LIMIT e sem agregacao. Preserva valores brutos, inclusive -127 e 85, sem arredondar. Grafico pode continuar agregado em intervalos longos. Exportacao tambem disponivel no painel de laboratorio.
- O status usa a amostra de idade zero como horario do recebimento no laboratorio, obrigatoria no lote; nao usa a primeira amostra reconstruida. Limites de campo e laboratorio continuam configurados separadamente.

## Evidencias e limite da correcao historica

O usuario confirmou a convencao local antiga e os horarios corretos do No 2. A tabela publicada e DATETIME DEFAULT CURRENT_TIMESTAMP; o painel MySQL mostrou SYSTEM/-03. O codigo anterior forca sessao +00:00. Registro 4017: 2026-11-06 15:12:48, com recebimento correlacionado no historico da investigacao a 12:12:48 local. Isso sustenta corrigir esse registro para 12:12:48, mas nao autoriza corrigir automaticamente todos os registros posteriores a uma data.

A janela de 20/10/2026 16:00 a 22:00 foi informada vazia. O corte 19:00 serve apenas para localizar candidatos. E necessario confirmar quais writers estavam ativos, seus deployments e os IDs afetados. Nenhum historico foi modificado nesta implementacao.

O rascunho anterior que somava 3h aos registros antigos foi removido. Nao deve ser usado: o destino escolhido e horario local, preservando os antigos corretos.

## Aplicacao coordenada

1. Executar `backend/database/audit_local_times_readonly.sql` e conferir os candidatos com logs dos writers. O acesso OAuth do plugin Railway nao fornece SQL nem valores de credenciais; requer uma conexao MySQL autorizada ou consultas pelo painel.
2. Preparar um manifesto JSON com IDs explicitamente auditados e horarios originais. Cada item: `id`, `sensor_id`, `gateway_id`, `data_hora` exato como aparece no banco. Nao preencher a lista apenas pelo corte temporal.
3. Executar `python backend/scripts/correct_local_times.py manifesto.json`. O padrao e somente leitura. Rever cada antes/depois. Fazer backup completo recuperavel do banco.
4. Na janela de publicacao, coordenar recepcao: parar o writer UTC antigo, incluindo instancias durante rolling deploy; considerar que transmissoes de campo sem buffer podem se perder durante a janela. Atualizar o manifesto final com quaisquer linhas novas ainda gravadas pelo writer antigo.
5. Executar o script com `--apply --backup /caminho/novo-backup.json` usando conexao autorizada. Exige coluna DATETIME, valida identidade/horario por ID, bloqueia linhas, guarda originais e altera somente os IDs auditados numa transacao. Repetir o mesmo manifesto nao subtrai outras 3 horas. Se ocorrer divergencia, faz rollback. O backup JSON complementa, nao substitui, o backup integral.
6. Publicar backend e frontend correspondentes. Nunca publicar o leitor local sobre um banco ainda misto. Conferir nova medicao de campo e novo lote contra um horario real com offset; comparar CSV por ID e contagem no banco, historico do No 2, filtros e status.
7. Em rollback, coordenar a convencao do writer/leitor com os dados. Nao voltar isoladamente ao codigo que presume UTC. O backup preserva valores anteriores para uma restauracao controlada.

## Validacao local

Testes cobrem: historico do No 2 mantido, offsets sem conversao dupla, filtros que cruzam meia-noite, CSV de 1201 registros brutos, lote de 16 idades com passagem de dia, status pela idade zero, rejeicao de lote em gateways de campo/fallback, coexistencia com INSERT individual e repeticao segura do mesmo manifesto de correcao. Integracao MySQL exige banco descartavel *_test e RUN_MYSQL_INTEGRATION=1; mocks nao comprovam a execucao SQL em producao.

## Auditoria complementar de 06/11/2026

O usuario retornou exatamente cinco candidatos: IDs 4013 a 4017. Logs Railway consultados diretamente mostram POSTs HTTP 201 nos horarios locais 04/11 17:06:54, 17:06:58, 17:08:03, 18:32:33 e 06/11 12:12:48. Cada um coincide em minutos/segundos com um dos cinco DATETIMEs, com diferenca de +3h. Os logs de plataforma possuem UTC explicito. Essa correlacao temporal e o writer de sessao UTC sustentam a correcao dos cinco IDs; logs nao incluem o ID do registro ou payload. Manifesto preparado em backend/database/time_correction_20261106.json. Nenhum UPDATE executado. No 2 permanece fora do manifesto.
