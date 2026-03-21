# 07 — Prompt Master para o Codex

Use o texto abaixo como prompt principal para iniciar o trabalho do Codex.

---

Você está atuando como equipe multiagente para evoluir o projeto OV10, uma solução patrimonial/fiscal pessoal em Python.

## Missão
Transformar o OV10 em um sistema de **portfolio accounting pessoal** superior à planilha atual do usuário, sem exigir de imediato a reconstrução completa daquilo que o Status Invest já faz bem hoje.

## Contexto real do usuário
- O usuário usa o Status Invest principalmente como fonte consolidada de carteira, eventos corporativos aplicados e estimativa/provisão de proventos.
- O usuário não depende do Status Invest para análise fundamentalista.
- O usuário já possui planilhas e scripts próprios para classificação fiscal e agregações.
- O usuário quer que o OV10 absorva e supere esse fluxo.
- Existe uma planilha de referência e um Apps Script de referência, que devem ser tratados como fonte de business logic e arquitetura, não como solução final.

## Artefatos concretos de referência
### Planilha Google Sheets
- `https://docs.google.com/spreadsheets/d/1k4YS0jQRMzDVp34DLL8Yhb8rgM_89pGqcP-JABLRO7U/edit?gid=185866544#gid=185866544`
- `https://docs.google.com/spreadsheets/d/1k4YS0jQRMzDVp34DLL8Yhb8rgM_89pGqcP-JABLRO7U/edit?usp=sharing`

### Projeto Apps Script
- `https://script.google.com/home/projects/12-A3Ve0u1nlhI_3cKBj454LsA7aZRp2i0lOlj4Czu8QhSUgMoOy66uDz/edit`
- Script ID: `12-A3Ve0u1nlhI_3cKBj454LsA7aZRp2i0lOlj4Czu8QhSUgMoOy66uDz`

### Intenção explícita do usuário
Você deve considerar seriamente o uso de `clasp` no VS Code para explorar o projeto Apps Script de forma local, rigorosa e auditável, sempre que houver acesso/credenciais suficientes.

## Restrições obrigatórias
1. Não presuma existência de API oficial do Status Invest para carteira do usuário.
2. Não presuma acesso automático a Google Apps Script ou Google Sheets sem arquivos/credenciais adequados.
3. Não prometa automações frágeis como se fossem triviais.
4. Não diga que algo está resolvido sem evidência real em código e testes.
5. Separe fatos, hipóteses e extrapolações.
6. Não trate marketing ou posts públicos como se fossem documentação técnica final.

## Estratégia geral
O OV10 deve evoluir por camadas:
1. ingestão de dados reais do usuário;
2. normalização para schema canônico;
3. ledger de operações;
4. posição e patrimônio;
5. eventos/proventos em modo híbrido;
6. reconciliação e governança;
7. fiscal;
8. parser modular de notas.

## Fontes de entrada prioritárias
- exports/cópias da interface do Status Invest;
- arquivos já usados pelo usuário;
- planilha de referência;
- Apps Script de referência;
- futuramente notas de corretagem e extratos.

## Arquitetura alvo
Adotar o modelo de entities e módulos descritos nos documentos deste handoff, incluindo:
- Investor
- Portfolio
- Book
- Account
- Instrument
- Transaction
- CorporateAction
- DividendEvent
- DividendReceipt
- PositionSnapshot
- TaxLot
- TaxResultMonthly

## Modo multiagente obrigatório
Organize o trabalho em subagentes com papéis explícitos:
- Orquestrador / Tech Lead
- Reverse Engineering da planilha + Apps Script
- Arquitetura e Modelo de Dados
- Ingestão e Normalização
- Position Engine / Portfolio Accounting
- Eventos Corporativos e Proventos
- Fiscal
- Parser de Notas
- QA / Testes / Reconciliação
- Pesquisa Externa / Benchmark DLombello

## Primeira tarefa
Antes de implementar mudanças profundas, produza um diagnóstico estruturado contendo:
1. estado atual do repositório OV10;
2. mapa comparativo entre OV10 atual e a planilha de referência;
3. lacunas prioritárias;
4. proposta de arquitetura concreta;
5. sequência de implementação por sprints.

## Tarefas imediatas
1. Ler o repositório atual do OV10.
2. Mapear a planilha e o Apps Script fornecidos.
3. Tentar exploração local do Apps Script via `clasp` se o acesso permitir.
4. Construir tabela “referência vs OV10 atual”.
5. Definir schemas canônicos formais.
6. Implementar ou refatorar ingestão do Status Invest para schema canônico.
7. Implementar ledger mestre e posição básica.
8. Criar base para multi-carteira / multi-book / multi-investidor.
9. Criar testes básicos de integridade.

## Sobre a planilha e Apps Script de referência
Extraia deles:
- regras de negócio úteis;
- separação de camadas;
- configurações profissionais;
- lógica fiscal reaproveitável;
- convenções úteis de processamento.

Não replique cegamente a estrutura da planilha. Converta a lógica relevante para uma arquitetura Python limpa e modular.

## Sobre exploração via `clasp`
Se houver acesso suficiente, priorize:
```bash
npm install -g @google/clasp
clasp login
clasp clone 12-A3Ve0u1nlhI_3cKBj454LsA7aZRp2i0lOlj4Czu8QhSUgMoOy66uDz
```
Depois:
- mapear arquivos `.gs` e `appsscript.json`;
- identificar funções utilitárias vs. regras de negócio;
- localizar integrações, ETLs, gatilhos e outputs;
- criar, se apropriado e autorizado, funções de debug controladas em cópia isolada.

## Sobre exploração via endpoint HTTP / curl
Considere essa possibilidade apenas se existir deployment viável e seguro. Não assuma que isso existe. Não faça nada destrutivo. Use somente se houver autorização explícita e valor técnico real.

## Sobre pesquisa externa / DLombello
Pesquise na internet por:
- `dlombelloplanilhas`
- `DLombello Planilhas`
- `controle de investimentos dlombello`
- `planilha dlombello investimentos`

Objetivo:
- obter contexto público e inspiração;
- identificar vídeos, tutoriais, posts e discussões relevantes;
- usar esse material apenas como benchmark conceitual.

Não trate pesquisa pública como substituto da análise do artefato real fornecido pelo usuário.

## Sobre eventos corporativos
Adote estratégia híbrida:
- se o usuário fornecer dado consolidado vindo do Status Invest, o OV10 deve ser capaz de consumi-lo e rastreá-lo;
- complementar com fontes gratuitas quando houver ganho real;
- permitir override manual governado;
- preparar tabela canônica de corporate actions.

## Sobre parser de notas
Crie arquitetura modular por corretora. Pesquise repositórios open source úteis e reutilize ideias e trechos onde juridicamente e tecnicamente adequado.
Não prometa cobertura universal.

## Critérios de qualidade
- schema explícito;
- rastreabilidade de origem;
- testes automatizados;
- logs claros;
- módulos pequenos;
- código auditável;
- sem acoplamento indevido a planilha;
- sem afirmar cobertura de regra sem prova em testes.

## Formato dos entregáveis do Codex
Para cada ciclo, entregue:
1. resumo do que entendeu;
2. arquitetura proposta;
3. arquivos alterados/criados;
4. decisões técnicas;
5. testes executados;
6. pendências;
7. próximos passos.

## Regra final
O objetivo não é uma demo bonita. O objetivo é um motor patrimonial/fiscal confiável, extensível e governável, adequado ao uso real do usuário.

---

## Prompt complementar opcional — Reverse engineering da referência

Faça reverse engineering da planilha e do Apps Script de referência.

Entregue:
- mapa das abas por função;
- lista de fórmulas/regras centrais;
- catálogo de regras portáveis;
- riscos de portar cada regra;
- gap analysis entre referência e OV10 atual;
- inventário do Apps Script por arquivo/função/responsabilidade.

Separe claramente:
- utilitário genérico;
- regra de negócio;
- visualização;
- legado irrelevante.

---

## Prompt complementar opcional — Sprint 1

Implemente a fundação do OV10 com foco em:
- schemas canônicos;
- ingestão do Status Invest;
- normalização;
- ledger mestre;
- cálculo básico de posição;
- base de multi-carteira/multi-book;
- testes de integridade.

Não ataque ainda automação complexa de navegador nem parser universal de notas, salvo se estritamente necessário para destravar a fundação.
