# 08 — Notas sobre Fontes de Dados, Eventos e Limitações

## 1. Posição pragmática
Para o caso deste usuário, a decisão economicamente racional hoje parece ser:

- manter o Status Invest como fonte útil onde ele entrega valor real;
- usar o OV10 para governança, modelagem, reconciliação, patrimonial e fiscal;
- evoluir a independência do OV10 de forma progressiva.

## 2. Fontes externas gratuitas possíveis
Sem prometer completude, o OV10 pode futuramente usar combinação de fontes como:
- Yahoo Finance / yfinance
- Fundamentus
- FundsExplorer
- outras fontes abertas específicas por classe de ativo

## 3. Regra correta
Essas fontes devem entrar como **fontes auxiliares ou complementares**, com reconciliação, e não necessariamente como fonte única da verdade.

## 4. Eventos corporativos
Nem toda fonte gratuita cobrirá com a mesma qualidade:
- split
- reverse split
- bonificação
- subscrição
- cisão
- mudança de ticker
- amortizações específicas

Logo, o desenho do OV10 deve aceitar:
- dado consolidado externo;
- múltiplas fontes;
- correção manual governada;
- confiança por fonte.

## 5. Objetivo final realista
O OV10 não precisa provar independência total imediatamente. Precisa provar:
- consistência;
- utilidade;
- rastreabilidade;
- superioridade operacional no uso real do usuário.


## Observação adicional
Se a referência DLombello usar múltiplas fontes gratuitas para compor dados, o OV10 também pode adotar estratégia multi-fonte. O Codex deve avaliar isso por evidência técnica e custo de manutenção, e não por preferência abstrata.
