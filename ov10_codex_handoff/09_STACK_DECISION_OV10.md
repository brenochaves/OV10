# 09_STACK_DECISION_OV10.md

## Decisão objetiva de stack para o OV10 (greenfield)

### Decisão final
A stack recomendada para o OV10, começando do zero hoje, é:

- **Python** no **core/backend de domínio**
- **TypeScript** na **camada de produto/interface**

---

## Escopo de cada linguagem

### Python
Usar Python para:
- engine de portfolio accounting
- ledger de transações
- motor de eventos corporativos
- motor de proventos
- motor fiscal
- ingestão de dados
- parsers de notas de corretagem
- reconciliação de dados
- ETL e jobs
- testes de regras de negócio

### TypeScript
Usar TypeScript para:
- frontend web
- interface responsiva
- painel do produto
- shell desktop
- camada BFF/API gateway, se necessário
- integrações de UX e camadas de apresentação

---

## Frameworks e componentes recomendados

### Backend / Core
- **Python 3.12+**
- **FastAPI** para API HTTP
- **Pydantic v2** para contratos, DTOs e validação
- **SQLAlchemy 2.x** para ORM/mapeamento
- **Alembic** para migrações
- **PostgreSQL** como banco principal
- **Redis** opcional para cache, filas leves e locking
- **Celery** ou **RQ** para jobs assíncronos, se necessário
- **Pytest** para testes
- **DuckDB** opcional para análises locais/ETL analítico

### Frontend Web
- **TypeScript**
- **React**
- **Next.js**
- **TanStack Query** para data fetching/cache
- **Zod** para validação de contratos no frontend
- **Tailwind CSS** para UI rápida e consistente
- **shadcn/ui** opcional para componentes

### Desktop
- **Tauri**
- frontend em **React + TypeScript**
- consumo da API/local service do backend Python

### Mobile
Mobile não é prioridade no curto prazo.
Se virar requisito futuro:
- **React Native** se quiser manter alinhamento com TypeScript
- alternativa: **Flutter** se o time preferir ecossistema mobile mais fechado

---

## Arquitetura alvo

```text
React / Next.js / TypeScript
            ↓
        Tauri (desktop, se aplicável)
            ↓
       FastAPI (Python)
            ↓
Domain Services / Portfolio Engine / Tax Engine / Parsers
            ↓
        PostgreSQL
```

---

## O que NÃO fazer

- não usar Python como stack única de produto/interface
- não usar Apps Script como core do produto
- não acoplar regras fiscais importantes à planilha
- não reescrever o core em TypeScript sem motivo técnico forte
- não priorizar mobile antes de estabilizar o motor de domínio
- não misturar frameworks desnecessariamente no backend

---

## Justificativa da decisão

### Por que Python no core
Porque o OV10 é principalmente:
- sistema de regras de negócio
- reconciliação financeira
- processamento tabular
- parser de documentos
- cálculo fiscal e patrimonial

Python é mais adequado para esse núcleo do que uma stack web pura.

### Por que TypeScript no produto
Porque a camada de produto exige:
- UI moderna
- responsividade
- ergonomia web
- caminho limpo para desktop
- maintainability de interface

TypeScript entrega melhor isso do que tentar usar Python para a interface.

---

## Regra de ouro para o Codex

Tratar o OV10 como **dois sistemas acoplados com fronteira explícita**:

1. **Core de domínio em Python**
2. **Produto/interface em TypeScript**

A comunicação entre eles deve ocorrer por contratos claros:
- API REST
- schemas versionados
- DTOs validados

---

## Ordem recomendada de implementação

1. consolidar o modelo de dados canônico
2. consolidar o ledger transacional
3. implementar engine de posição
4. implementar engine de eventos corporativos
5. implementar engine de proventos
6. implementar engine fiscal
7. expor API FastAPI
8. construir frontend em React/Next.js
9. empacotar desktop com Tauri, se fizer sentido

---

## Decisão final a ser seguida pelo Codex

### Stack oficial do OV10
- **Core/backend:** Python
- **Framework backend:** FastAPI
- **ORM:** SQLAlchemy
- **Banco principal:** PostgreSQL
- **Frontend:** TypeScript + React + Next.js
- **Desktop:** Tauri
- **Jobs/ETL/parsers:** Python

### Se for obrigatório escolher uma linguagem única
- **TypeScript**

### Mas a recomendação principal NÃO é linguagem única
- **A recomendação oficial é Python + TypeScript**
