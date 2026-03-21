# 10. Governança, Qualidade e Critérios de Profissionalização do OV10

## Objetivo
Este documento fixa requisitos de governança técnica, qualidade, rastreabilidade e disciplina arquitetural que o Codex deve tratar como obrigatórios ao evoluir o OV10. A stack já foi decidida em documento separado. Aqui o foco é garantir que o projeto seja profissional, auditável, escalável e mantível.

---

## 1. Tratar o OV10 como sistema de domínio, não como app comum
O OV10 deve ser modelado primeiro como um sistema profissional de **portfolio accounting + tax engine**.

A ordem conceitual correta é:
1. ledger de transações;
2. eventos corporativos;
3. proventos;
4. posição;
5. motor fiscal;
6. relatórios;
7. interfaces.

A interface não é a fonte da verdade. A fonte da verdade é o modelo de domínio persistido e auditável.

---

## 2. Criar contrato de domínio antes de expandir o código
Antes de ampliar funcionalidades, o Codex deve consolidar:
- entidades canônicas;
- enums fechados;
- tipos de transação;
- tipos de eventos corporativos;
- invariantes de negócio;
- contratos de entrada e saída.

### Invariantes mínimas
- posição calculada deve ser sempre reproduzível a partir do ledger + eventos;
- nenhuma posição pode surgir sem trilha de origem;
- nenhum evento corporativo pode alterar resultado sem rastreabilidade;
- cálculo fiscal deve ser determinístico para o mesmo conjunto de entradas;
- importações repetidas não podem duplicar efeito.

---

## 3. Exigir arquitetura modular e separação rigorosa de camadas
O Codex deve estruturar o projeto em módulos claros, sem espalhar regra de negócio em controllers, tela, script solto ou utilitários genéricos.

### Módulos esperados
- `ingestion`
- `normalization`
- `adapters`
- `ledger`
- `corporate_actions`
- `dividends`
- `positions`
- `valuation`
- `tax`
- `reporting`
- `audit`
- `api`
- `ui`

### Regra
Nenhum módulo externo pode conhecer detalhes internos do domínio sem passar por interfaces explícitas.

---

## 4. Criar camada anti-corrupção para fontes externas
Toda fonte externa deve entrar por uma camada de adaptação.

### Fontes típicas
- Status Invest;
- CSV exportado;
- copy/paste de tabelas;
- APIs públicas;
- corretoras;
- planilhas externas;
- dados de App Script / Google Sheets.

### Regra obrigatória
Formato externo nunca deve contaminar o domínio interno.

Fluxo correto:

`fonte externa -> adapter -> modelo canônico OV10`

O domínio do OV10 deve depender apenas do modelo canônico interno.

---

## 5. Exigir testes de regra de negócio com casos reais
O Codex não deve entregar apenas testes técnicos superficiais. Deve criar testes de negócio com cenários financeiros reais.

### Casos mínimos obrigatórios
- compra integral;
- compra parcial + venda parcial;
- compra em lotes com preços diferentes;
- split;
- grupamento;
- bonificação;
- subscrição;
- cisão;
- mudança de ticker;
- dividendos;
- JCP;
- amortização;
- prejuízo acumulado;
- compensação mensal;
- duplicidade de importação;
- divergência entre fonte externa e posição calculada.

### Requisitos
- testes unitários por motor;
- testes de integração por pipeline;
- testes de regressão com snapshots quando fizer sentido;
- massa de dados sintética e massa de dados real anonimizada.

---

## 6. Exigir rastreabilidade total
Toda saída relevante do sistema deve responder:
- qual foi a origem da entrada;
- qual adapter a normalizou;
- quais regras foram aplicadas;
- qual versão do motor gerou o resultado;
- qual foi a data/hora do processamento;
- qual o identificador do lote/importação.

### Isso vale para
- posição calculada;
- proventos lançados;
- eventos aplicados;
- relatórios fiscais;
- divergências;
- exportações.

Sem rastreabilidade, o OV10 não deve ser tratado como produto sério.

---

## 7. Versionar regras e motores de cálculo
Regras devem ser tratadas como artefatos versionados.

### Exemplos
- `position_engine_v1`
- `corporate_actions_engine_v1`
- `dividend_engine_v1`
- `tax_rules_br_v1`

### Regra
O sistema deve permitir saber com qual versão de motor um resultado foi produzido.

Motivo: regras evoluem. Produto profissional não mistura cálculo antigo e cálculo novo sem controle.

---

## 8. Banco relacional sério e disciplina transacional
O OV10 deve usar banco relacional robusto como fonte persistente principal.

### Decisão já tomada
- PostgreSQL como banco principal.

### Requisitos de implementação
- migrations versionadas;
- constraints explícitas;
- chaves estrangeiras;
- unicidade onde aplicável;
- trilhas de auditoria para dados sensíveis;
- estratégia clara para soft delete vs hard delete;
- transações explícitas em operações críticas.

---

## 9. Fixar stack sem rediscussão oportunista
O Codex não deve reabrir discussão de stack salvo se houver impeditivo técnico concreto e bem demonstrado.

### Stack oficial
- Core/API: Python + FastAPI
- Frontend: TypeScript + Next.js
- Desktop: Tauri
- Banco: PostgreSQL
- ETL / jobs: Python

### Regra
Evitar desvio de escopo com reescritas desnecessárias.

---

## 10. Criar ADRs obrigatórios
O projeto deve manter **Architecture Decision Records**.

### ADRs mínimos
- ADR da stack oficial;
- ADR do modelo de dados canônico;
- ADR da estratégia de eventos corporativos;
- ADR da estratégia de ingestão do Status Invest;
- ADR da camada fiscal;
- ADR dos parsers de notas;
- ADR da estratégia desktop;
- ADR da estratégia de auditoria e rastreabilidade.

### Regra
Toda decisão estrutural relevante deve ser registrada.

---

## 11. Migrations, seeds e ambiente reprodutível
Nada deve depender de criação manual ad hoc.

### O Codex deve entregar
- migrations;
- seeds/fixtures;
- ambiente local reprodutível;
- instrução clara de bootstrap;
- dados de exemplo mínimos para validar o sistema.

---

## 12. Observabilidade desde cedo
O OV10 deve nascer com observabilidade mínima aceitável.

### Exigências mínimas
- logs estruturados;
- correlação por request/importação/lote;
- logs de divergência;
- logs de decisão de adapter;
- logs de aplicação de evento corporativo;
- logs de falhas de reconciliação.

### Regra
Erro silencioso é proibido.

---

## 13. Idempotência como requisito central
O sistema deve ser idempotente em importações e reaplicações.

### Exemplos
- importar a mesma nota duas vezes não pode duplicar transação;
- importar o mesmo CSV duas vezes não pode alterar posição;
- reaplicar o mesmo evento corporativo não pode gerar duplo efeito;
- reprocessar um lote deve ser seguro.

Idempotência não é detalhe; é requisito de produto confiável.

---

## 14. Reconciliação automática
O OV10 deve incluir rotinas automáticas de reconciliação.

### Comparações desejadas
- posição esperada vs posição calculada;
- proventos esperados vs proventos lançados;
- eventos esperados vs eventos aplicados;
- divergência por ativo;
- divergência por período;
- divergência por conta/carteira/book.

### Saída
Toda divergência deve gerar registro auditável e explicável.

---

## 15. Ordem correta de implementação
O Codex deve seguir prioridade por valor estrutural, não por aparência.

### Ordem oficial
1. modelo canônico;
2. ledger;
3. adapters de ingestão;
4. eventos corporativos;
5. posição;
6. proventos;
7. reconciliação;
8. fiscal;
9. relatórios;
10. UI.

### Regra
Não priorizar interface antes de estabilizar o núcleo do domínio.

---

## 16. Recusar atalhos arquiteturais
O Codex deve explicitamente evitar:
- lógica de negócio enterrada em planilha como fonte da verdade;
- regra fiscal hardcoded em tela;
- adapter fazendo papel de domínio;
- domínio conhecendo formato bruto externo;
- parser acoplado ao cálculo fiscal;
- script solto sem contrato;
- dependência de copy/paste como mecanismo oficial do sistema.

---

## 17. Critério de profissionalização
O projeto só deve ser considerado profissional quando atender, no mínimo, aos seguintes critérios:
- domínio separado de interface;
- modelo de dados canônico consolidado;
- rastreabilidade total;
- testes reais de negócio;
- idempotência;
- reconciliação automática;
- versionamento de regras;
- migrations e ambiente reprodutível;
- observabilidade mínima;
- ADRs registrados.

---

## 18. Instrução curta e mandatória ao Codex
Usar esta instrução como regra-mãe:

> Trate o OV10 como um sistema profissional de portfolio accounting e tax engine, com foco em correção, rastreabilidade, auditabilidade, idempotência, separação rigorosa por camadas, adapters para fontes externas, reconciliação automática e testes de regras de negócio com casos reais. Não priorize interface antes de estabilizar o núcleo do domínio.

---

## 19. Resultado esperado do Codex
Ao final, o Codex deve deixar o projeto mais próximo de um sistema profissional do que de uma planilha sofisticada.

O valor do OV10 não está na tela. Está em:
- domínio correto;
- cálculo reproduzível;
- rastreabilidade;
- robustez contra erro;
- capacidade de evolução sem colapso arquitetural.
