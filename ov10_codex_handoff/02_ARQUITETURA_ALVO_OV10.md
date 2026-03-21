# 02 — Arquitetura Alvo do OV10

## 1. Visão macro
O OV10 deve evoluir para a seguinte arquitetura lógica:

```text
Data Sources
   ├─ Status Invest exports / copied tables
   ├─ Broker notes / statements
   ├─ Free market data sources
   └─ Manual corrections / governance tables

        ↓

Ingestion Layer
   ├─ status_invest_ingestor
   ├─ broker_note_ingestor
   ├─ cash_movement_ingestor
   └─ manual_adjustments_ingestor

        ↓

Normalization Layer
   ├─ canonical transaction schema
   ├─ canonical instrument schema
   ├─ canonical dividend schema
   ├─ canonical corporate action schema
   └─ mapping / dictionaries

        ↓

Core Engines
   ├─ transaction ledger engine
   ├─ position engine
   ├─ corporate actions engine (future / hybrid)
   ├─ dividend engine
   ├─ portfolio analytics engine
   └─ tax engine (future but planned now)

        ↓

Reconciliation & Validation
   ├─ source vs normalized checks
   ├─ broker vs ledger checks
   ├─ dividends vs expected checks
   ├─ holdings checks
   └─ error flags / diagnostics

        ↓

Output Layer
   ├─ patrimonial reports
   ├─ fiscal reports
   ├─ IR support views
   ├─ dashboards
   └─ exports to spreadsheet / csv / parquet / db
```

## 2. Diretriz de desenho
O sistema deve ser desenhado para funcionar em **camadas**, evitando lógica espalhada em planilhas e scripts avulsos.

## 3. Substituição incremental
O OV10 não precisa nascer substituindo tudo. Ele pode operar em modo híbrido:

```text
Status Invest = provider parcial de consolidação
OV10 = provider de governança, reconciliação, enriquecimento e fiscal
```

## 4. Módulos principais

### 4.1 Ingestão
Responsável por ler dados de:
- CSVs do Status Invest;
- tabelas copiadas da interface;
- notas de corretagem;
- extratos;
- tabelas de apoio.

### 4.2 Normalização
Responsável por converter qualquer fonte externa em schema canônico interno.

### 4.3 Ledger
Livro mestre de eventos econômicos da carteira.

### 4.4 Posições
Reconstrução da posição por ativo, carteira, conta, investidor, data.

### 4.5 Eventos corporativos
Módulo planejado para operar inicialmente em modo híbrido:
- consumir o que vier consolidado do Status Invest;
- complementar com fontes gratuitas quando fizer sentido;
- permitir ajuste manual governado.

### 4.6 Proventos
Registrar:
- provisionado;
- recebido;
- competência;
- ativo gerador;
- origem do dado.

### 4.7 Fiscal
Camada futura, mas deve ser prevista desde já para não quebrar o modelo.

## 5. Separação obrigatória entre conceitos
Nunca misturar:

- transação operacional;
- evento corporativo;
- provento;
- movimento de caixa;
- ajuste manual;
- apuração fiscal.

## 6. Arquitetura de persistência recomendada
Para o estado atual do projeto, uma boa trajetória é:

### curto prazo
- CSV/Excel + pandas + arquivos intermediários controlados;

### médio prazo
- DuckDB ou SQLite como camada persistente local;

### longo prazo
- data mart patrimonial pessoal com tabelas bem definidas.

## 7. Modo operacional recomendado

### estágio 1
- ingestão manual assistida;
- validação forte;
- saídas reprodutíveis.

### estágio 2
- ingestão semi-automática;
- catálogos e mapeamentos permanentes;
- reconciliação multi-fonte.

### estágio 3
- orquestração completa;
- dashboards e relatórios consolidados.
