# OV10 — Pacote de Handoff para Codex

## Objetivo
Este pacote existe para orientar o Codex a evoluir o projeto OV10 a partir do estado atual, usando como referências:

- a arquitetura atual do OV10;
- o fluxo real do usuário com Status Invest;
- a planilha/Apps Script analisados como referência de business logic;
- a necessidade de automação gradual, robusta e auditável.

## Contexto resumido
O usuário **não** quer reconstruir do zero uma engine completa de eventos corporativos se houver forma economicamente melhor de aproveitar o que já funciona hoje. O fluxo atual útil é:

1. Status Invest consolida eventos corporativos e proventos da carteira do usuário.
2. O usuário exporta/copias dados da interface do Status Invest.
3. O OV10 aplica agregações, reconciliações, classificação fiscal e relatórios próprios.

## Diretriz central
O OV10 deve evoluir para ser um **Personal Portfolio Accounting Engine**, mas sem exigir de imediato a reimplementação integral do que o Status Invest já entrega melhor hoje.

## Resultado esperado do Codex
O Codex deve:

1. entender o estado atual do OV10;
2. mapear o gap entre OV10 e a planilha de referência;
3. propor e implementar melhorias modulares;
4. organizar o projeto para ingestão de dados vindos do Status Invest e de corretoras;
5. desenhar arquitetura preparada para multi-carteira, multi-investidor e multi-book;
6. preparar base futura para engine fiscal.

## Restrições reais
O Codex **não deve presumir** que terá automaticamente:

- acesso autenticado ao Google Sheets sem credenciais ou arquivos locais;
- acesso ao Status Invest via API oficial, porque não existe API pública documentada para a carteira do usuário;
- acesso ao código-fonte do Leitor de Notas de Corretagem;
- acesso irrestrito a dados pagos.

Logo, ele deve trabalhar com o que for realmente fornecido:

- repositório OV10 atual;
- arquivos exportados;
- planilha XLSX fornecida;
- Apps Script fornecido em texto;
- eventuais novos arquivos ou credenciais explicitamente disponibilizados pelo usuário.

## Como usar este pacote
Leitura recomendada pelo Codex:

1. `01_VISÃO_GERAL_E_PREMISSAS.md`
2. `02_ARQUITETURA_ALVO_OV10.md`
3. `03_MODELO_DE_DADOS_E_MÓDULOS.md`
4. `04_PLANO_DE_REFERÊNCIA_PLANILHA_APPS_SCRIPT.md`
5. `05_BACKLOG_PRIORIZADO.md`
6. `06_MULTIAGENTE_ORQUESTRAÇÃO.md`
7. `07_PROMPT_MASTER_CODEX.md`

## Princípios de implementação
- priorizar robustez sobre “mágica”; 
- evitar dependência de scraping frágil quando houver alternativa melhor;
- preservar rastreabilidade contábil;
- separar claramente ingestão, normalização, cálculo, reconciliação e relatório;
- implementar tudo de forma modular, testável e auditável.


## Atualização v2 incluída neste pacote
Este pacote foi reforçado para conter explicitamente:
- uso de `clasp` no VS Code para explorar o projeto Apps Script;
- exploração controlada da planilha Google Sheets e do Apps Script como fontes de reverse engineering;
- links exatos fornecidos pelo usuário para a planilha e para o projeto Apps Script;
- instrução explícita para pesquisar na internet referências públicas sobre `dlombelloplanilhas` / `DLombello Planilhas` e usar isso apenas como inspiração arquitetural, nunca como verdade automática.
