# 06 — Estratégia Multiagente para o Codex

## 1. Objetivo
O usuário quer que o Codex trabalhe em modo multiagente. A melhor forma é dividir por especialidade, com um agente coordenador.

## 2. Estrutura recomendada

### Agente 0 — Orquestrador / Tech Lead
Responsabilidades:
- ler todos os documentos deste pacote;
- entender estado atual do repositório OV10;
- quebrar trabalho em frentes;
- arbitrar conflitos de modelagem;
- consolidar plano final;
- garantir consistência entre módulos.

### Agente 1 — Reverse Engineering da planilha + Apps Script
Responsabilidades:
- mapear abas, fórmulas e lógica da referência;
- separar utilidades genéricas de regras de negócio;
- produzir catálogo de regras aproveitáveis;
- comparar referência com OV10 atual;
- priorizar exploração via `clasp` quando houver acesso real ao projeto Apps Script.

### Agente 2 — Arquitetura e Modelo de Dados
Responsabilidades:
- definir schemas canônicos;
- modelar entidades;
- propor persistência local;
- desenhar contratos entre módulos.

### Agente 3 — Ingestão e Normalização
Responsabilidades:
- criar ingestors para Status Invest;
- criar parsers de entrada tabular/copiada;
- normalizar para schema interno;
- cuidar de rastreabilidade de origem.

### Agente 4 — Portfolio Accounting / Position Engine
Responsabilidades:
- ledger;
- posição;
- preço médio;
- snapshots patrimoniais;
- alocação e rentabilidade.

### Agente 5 — Eventos Corporativos e Proventos
Responsabilidades:
- desenhar modo híbrido de eventos;
- integrar múltiplas fontes gratuitas quando fizer sentido;
- modelar dividend_event e dividend_receipt;
- prever governança de override manual.

### Agente 6 — Fiscal
Responsabilidades:
- desenhar tax engine futura;
- mapear backlog fiscal;
- implementar base inicial se couber na sprint.

### Agente 7 — Parser de Notas / Corretoras
Responsabilidades:
- pesquisar projetos open source úteis;
- propor arquitetura modular por corretora;
- desenhar abstrações de parser;
- não prometer cobertura total sem evidência.

### Agente 8 — QA / Reconciliação / Testes
Responsabilidades:
- criar testes de schema;
- testes de reconciliação;
- cenários sintéticos;
- validações de consistência.

### Agente 9 — Pesquisa Externa / Benchmark / DLombello
Responsabilidades:
- pesquisar publicamente `dlombelloplanilhas` / `DLombello Planilhas` e variações;
- coletar contexto útil, vídeos, posts, tutoriais e discussões relevantes;
- separar contexto público de evidência real do artefato fornecido;
- produzir benchmark conceitual, nunca substituir análise do artefato real.

## 3. Regras de operação multiagente
- nenhum agente altera o modelo canônico sem validação do orquestrador;
- nenhuma integração externa é marcada como “resolvida” sem teste real;
- toda hipótese deve ser rotulada como hipótese;
- toda regra portada da planilha deve ter origem identificada;
- pesquisa web serve como contexto, não como prova suficiente;
- exploração via `clasp` deve ser preferida à leitura superficial quando houver acesso real.

## 4. Sequência recomendada

### Sprint 0 — Diagnóstico
- Agente 0 coordena
- Agente 1 mapeia referência
- Agente 2 modela dados
- Agente 9 levanta contexto público sobre DLombello

### Sprint 1 — Fundação
- Agente 3 implementa ingestão
- Agente 4 implementa ledger/posição
- Agente 8 cobre testes

### Sprint 2 — Enriquecimento
- Agente 5 trata eventos/proventos
- Agente 4 amplia analytics
- Agente 8 reforça reconciliação

### Sprint 3 — Fiscal e Notas
- Agente 6 modela fiscal
- Agente 7 estrutura parser modular

## 5. Entregáveis por agente
Cada agente deve sempre produzir:
- diagnóstico do estado atual;
- proposta de mudança;
- riscos;
- arquivos alterados;
- testes adicionados;
- lacunas remanescentes.
