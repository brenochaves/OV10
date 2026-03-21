# 05 — Backlog Priorizado do OV10

## 1. Diretriz de priorização
Priorizar na ordem:

1. ingestão confiável;
2. normalização e schema;
3. posição e patrimônio;
4. reconciliação;
5. multi-carteira;
6. fiscal;
7. parser avançado de notas;
8. engine própria completa de eventos.

---

## EPIC A — Fundação de Dados

### A1. Definir schemas canônicos
- transactions
- instruments
- dividends
- corporate_actions
- positions
- tax outputs

### A2. Criar camada de mapeamento
- brokers
- tipos de ativo
- aliases de ticker
- classes fiscais

### A3. Criar validação de schemas
- validação de colunas obrigatórias
- tipos
- ranges básicos
- flags de inconsistência

**Prioridade:** altíssima

---

## EPIC B — Ingestão do Status Invest

### B1. Ingestor de operações exportadas
- CSV/Excel do Status Invest
- copiar/colar tabelas quando necessário

### B2. Ingestor de proventos
- histórico de proventos
- provisionados e/ou recebidos, conforme disponibilidade

### B3. Ingestor de posições
- posição consolidada
- preço médio quando disponível

### B4. Mapeador de origem
- marcar tipo de origem
- registrar metadados do arquivo

**Prioridade:** altíssima

---

## EPIC C — Ledger e Position Engine

### C1. Ledger mestre de operações
### C2. Cálculo de posição por data
### C3. Cálculo de preço médio
### C4. Cálculo de caixa e movimentos financeiros
### C5. Snapshots patrimoniais

**Prioridade:** altíssima

---

## EPIC D — Multi-carteira / Multi-book / Multi-investidor

### D1. Estruturas de configuração
### D2. Separação por book
### D3. Regras de agregação por portfolio
### D4. Consolidação por investidor

**Prioridade:** alta

---

## EPIC E — Regras de negócio inspiradas na planilha

### E1. Mapeamento comparativo planilha vs OV10
### E2. Portar regras úteis de:
- alocação
- summary
- rendimentos
- radar, se houver valor
- views patrimoniais relevantes

### E3. Recriar lógicas em Python, sem reproduzir desorganização de planilha

**Prioridade:** alta

---

## EPIC F — Eventos corporativos (modo híbrido)

### F1. Consumir dado consolidado vindo do Status Invest quando disponível
### F2. Criar tabela de corporate actions canônica
### F3. Permitir complementação por fontes gratuitas
### F4. Permitir override manual governado
### F5. Criar reconciliação entre fontes

**Prioridade:** alta, mas incremental

---

## EPIC G — Proventos

### G1. Cadastro canônico de eventos de provento
### G2. Recebimento por carteira/conta
### G3. Apropriação e reconciliação
### G4. Relatórios anuais e mensais

**Prioridade:** alta

---

## EPIC H — Fiscal

### H1. Definir escopo fiscal inicial
- swing trade BR
- day trade BR
- FIIs
- ativos internacionais
- cripto

### H2. Implementar base de apuração mensal
### H3. Loss carryforward
### H4. Regras por classe de ativo
### H5. Relatórios para suporte ao IR

**Prioridade:** média-alta

---

## EPIC I — Parser modular de notas de corretagem

### I1. Estrutura base de parser por corretora
### I2. Reuso de bibliotecas e ideias de projetos open source
### I3. Normalização para schema único
### I4. Suporte inicial às corretoras prioritárias do usuário

Corretoras/arquivos já citados pelo usuário historicamente:
- Binance (.xlsx)
- Inter Co/Apex (.xlsx)
- Inter Brasil (.xlsx)
- C6 (.xlsx)
- Sofisa (.html)
- eventualmente XP e Avenue

**Prioridade:** média-alta

---

## EPIC J — Governança e Diagnóstico

### J1. Regras independentes de validação
### J2. Painel de inconsistências
### J3. Explicação provável da causa do erro
### J4. Logs de transformação

**Prioridade:** alta

---

## 2. Definição objetiva de MVP útil
O MVP útil do OV10 não é “fazer tudo”. O MVP útil é:

1. importar dados do Status Invest de forma consistente;
2. normalizar em schema canônico;
3. calcular posições e visões patrimoniais;
4. suportar multi-carteira / multi-book;
5. gerar saídas melhores que a planilha atual;
6. preparar base para fiscal.
