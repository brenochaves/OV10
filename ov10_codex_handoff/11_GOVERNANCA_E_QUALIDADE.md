# 11. GOVERNANÇA E QUALIDADE OBRIGATÓRIAS

Este arquivo fixa critérios obrigatórios de governança, qualidade e desenho técnico para o OV10.

## 1. Natureza do sistema

Tratar o OV10 como:

- sistema profissional de **portfolio accounting**;
- motor de **eventos corporativos**;
- motor de **proventos**;
- motor de **apuração fiscal**;
- plataforma de **ingestão, reconciliação e auditabilidade**.

Não tratar o OV10 como simples app de tela, CRUD ou dashboard.

## 2. Prioridade do domínio

A ordem correta de construção é:

1. modelo canônico de domínio;
2. ledger de transações;
3. motor de eventos corporativos;
4. cálculo de posição;
5. motor de proventos;
6. motor fiscal;
7. ingestão automatizada;
8. interface.

## 3. Contratos e invariantes

Definir explicitamente:

- entidades canônicas;
- enums fechados;
- tipos de transação;
- tipos de eventos;
- invariantes do sistema.

Exemplos de invariantes:

- posição deve ser reprodutível a partir do ledger + eventos;
- mesma importação não pode duplicar efeito;
- cálculo fiscal deve ser reproduzível e auditável;
- eventos corporativos não podem alterar estado sem trilha.

## 4. Isolamento das fontes externas

Toda fonte externa deve passar por adapters:

- Status Invest;
- CSVs;
- copy/paste;
- corretoras;
- APIs públicas;
- planilhas;
- Apps Script.

Padrão obrigatório:

`fonte externa -> adapter -> modelo canônico OV10`

## 5. Testes obrigatórios

Implementar:

- testes unitários;
- testes de integração;
- testes de regra de negócio com casos reais.

Cobertura mínima:

- compra parcial;
- venda parcial;
- split;
- grupamento;
- bonificação;
- subscrição;
- cisão;
- ticker change;
- dividendos;
- JCP;
- prejuízo acumulado;
- compensação mensal.

## 6. Auditoria e rastreabilidade

Toda saída importante deve permitir responder:

- qual foi a entrada;
- qual adapter tratou a entrada;
- quais regras foram aplicadas;
- qual versão do motor produziu o resultado.

## 7. Versionamento de regras

Versionar regras críticas:

- `position_engine_v1`
- `corporate_actions_v1`
- `tax_rules_v1`
- `dividend_engine_v1`

## 8. Banco e persistência

Banco principal:

- **PostgreSQL**

Exigir:

- migrations;
- seed controlado;
- ambiente reproduzível;
- constraints explícitas.

## 9. Stack fixa

Não rediscutir stack, salvo motivo técnico muito forte.

Stack oficial:

- **Python + FastAPI** no core/API
- **TypeScript + Next.js** no frontend
- **Tauri** no desktop
- **PostgreSQL** no banco principal

## 10. ADRs obrigatórios

Criar ADRs para:

- stack;
- modelo de dados;
- estratégia de eventos corporativos;
- integração com Status Invest;
- parser de notas;
- banco;
- estratégia desktop.

## 11. Idempotência

Importar o mesmo dado duas vezes não pode duplicar efeito econômico ou contábil.

## 12. Reconciliação

Implementar mecanismos de reconciliação entre:

- posição esperada;
- posição calculada;
- proventos esperados;
- proventos lançados;
- divergências por período e ativo.

## 13. Atalhos proibidos

Evitar explicitamente:

- lógica crítica espalhada em UI;
- regra fiscal hardcoded em tela;
- dependência direta do formato externo bruto;
- importadores sem contrato de dados;
- planilha externa como fonte da verdade do domínio.

## 14. Instrução final ao Codex

Tratar o OV10 como software profissional de missão crítica para integridade patrimonial e fiscal, priorizando correção, rastreabilidade, auditabilidade, testes e separação arquitetural.
