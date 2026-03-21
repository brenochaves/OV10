# 01 — Visão Geral e Premissas

## 1. Problema real a resolver
O usuário já possui uma solução parcial funcional:

- usa o Status Invest como fonte consolidada de carteira, eventos corporativos e estimativas de proventos;
- usa planilhas/scripts próprios para classificação fiscal, agregação temporal e relatórios;
- está desenvolvendo o OV10 para se tornar sua solução patrimonial completa.

O problema é que hoje ainda existe dependência de:

- exportações CSV manuais;
- copiar/colar alguns blocos da interface do Status Invest;
- ausência de engine própria amadurecida para certos domínios.

## 2. O que o usuário valoriza
Prioridades reais do usuário:

1. **rastreabilidade contábil**;
2. **consistência do histórico**;
3. **capacidade de auditoria**;
4. **baixo retrabalho manual**;
5. **respeito ao fluxo fiscal real**;
6. **capacidade de evolução técnica via Python**.

O usuário **não** precisa que o OV10 faça análise fundamentalista de ativos. Essa função já é coberta externamente por research.

## 3. Funções que hoje o Status Invest cobre bem para este caso
- aplicação automática de eventos corporativos em muitos cenários;
- histórico consolidado da carteira do usuário;
- calendário / provisão de proventos;
- visão operacional já tratada para consumo humano.

## 4. Funções que o OV10 deve absorver ou fortalecer
- ingestão padronizada de dados do Status Invest;
- ledger mestre de operações;
- reconciliação e validação;
- classificação fiscal;
- relatórios fiscais e patrimoniais próprios;
- multi-carteira / multi-book / multi-investidor;
- futura leitura automática de notas de corretagem.

## 5. Estratégia correta de evolução
Não tentar resolver tudo de uma vez.

### Fase correta
1. consolidar ingestão e normalização;
2. consolidar modelo de dados;
3. portar regras de negócio úteis da planilha de referência;
4. estruturar camada patrimonial e fiscal;
5. só depois ampliar parser de notas e engine própria de eventos.

## 6. Regra de ouro
**Não destruir o que hoje já funciona economicamente bem.**

Se o Status Invest entrega com boa confiabilidade eventos/proventos por R$ 22/mês, o OV10 não deve obrigatoriamente substituir isso imediatamente. Deve antes ser capaz de:

- absorver esses dados de forma limpa;
- validá-los;
- enriquecê-los;
- produzir saída superior.

## 7. Premissas técnicas
- linguagem principal: Python;
- planilha/Apps Script de referência serão usadas como fonte de lógica, não como destino final;
- a arquitetura do OV10 deve ser dirigida a dados;
- preferir pipelines reproduzíveis;
- preparar estrutura para testes automatizados.

## 8. Limitações e honestidade técnica
O Codex não deve inventar integrações “fáceis” sem prova. Em especial:

- acesso automatizado ao Status Invest pode continuar parcial/manual;
- endpoints internos do Status Invest não devem ser assumidos como base estável sem validação real;
- automação por navegador só deve entrar se o usuário quiser explicitamente e se houver ganho concreto;
- fontes gratuitas de eventos corporativos devem ser usadas em arquitetura multi-fonte, com reconciliação, e não como verdade absoluta única.
