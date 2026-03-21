# 04 — Plano de Referência: Planilha Google Sheets + Apps Script + Reverse Engineering Controlado

## 1. Objetivo
Usar a planilha e o Apps Script de referência como **fonte de arquitetura, regras de negócio e organização por camadas** para inspirar a evolução do OV10.

O objetivo **não** é acoplar o OV10 à solução original nem copiar cegamente a implementação. O objetivo é:
- entender a arquitetura da referência;
- minerar regras úteis;
- identificar o que é portável;
- converter o que for valioso para uma arquitetura Python limpa e governável.

---

## 2. Artefatos de referência fornecidos pelo usuário

### 2.1 Planilha Google Sheets
- Link principal:
  `https://docs.google.com/spreadsheets/d/1k4YS0jQRMzDVp34DLL8Yhb8rgM_89pGqcP-JABLRO7U/edit?gid=185866544#gid=185866544`
- Link compartilhado com permissão de editor:
  `https://docs.google.com/spreadsheets/d/1k4YS0jQRMzDVp34DLL8Yhb8rgM_89pGqcP-JABLRO7U/edit?usp=sharing`

### 2.2 Projeto Google Apps Script
- Link do projeto:
  `https://script.google.com/home/projects/12-A3Ve0u1nlhI_3cKBj454LsA7aZRp2i0lOlj4Czu8QhSUgMoOy66uDz/edit`
- Script ID / Código do script:
  `12-A3Ve0u1nlhI_3cKBj454LsA7aZRp2i0lOlj4Czu8QhSUgMoOy66uDz`

### 2.3 Arquivo local de referência já exportado
- XLSX baixado pelo usuário e já fornecido para análise.

---

## 3. Hipótese central a ser validada
A referência parece conter valor real em quatro frentes:
1. **camada de entrada / staging**;
2. **camada de processamento patrimonial**;
3. **camada fiscal**;
4. **camada de configuração profissional** (multi-carteira, multi-book, multi-investidor).

Essa hipótese deve ser validada por evidência concreta, não por impressão visual.

---

## 4. Diretriz forte para o Codex
O Codex deve tratar a referência como um sistema a ser estudado em três níveis:

### Nível A — Estrutura da planilha
- mapear abas;
- classificar por função;
- distinguir input, staging, processamento, saída e configuração;
- mapear relações entre abas;
- localizar fórmulas centrais.

### Nível B — Lógica do Apps Script
- separar biblioteca genérica (ex.: ImportJSON) de lógica específica do projeto;
- identificar funções que acionam ETL, atualização, transformação ou consolidação;
- identificar rotinas que revelam regras de negócio;
- localizar eventuais convenções de nomenclatura e fluxos operacionais.

### Nível C — Regras de negócio portáveis
- preço médio;
- posição consolidada;
- apropriação de proventos;
- visão multi-carteira;
- classificação de books;
- regras fiscais;
- indicadores de alocação e consolidação.

---

## 5. Exploração via `clasp` no VS Code — obrigatória quando houver acesso
O usuário explicitamente quer que o Codex considere o uso de `clasp` para trabalhar com o Apps Script de forma séria no VS Code.

### 5.1 Postura esperada
Se houver credenciais/acesso suficientes, o Codex **deve priorizar** a exploração local do Apps Script via `clasp`, em vez de tratar a lógica apenas como texto colado.

### 5.2 Fluxo recomendado
1. autenticar no ambiente Google apropriado;
2. instalar `clasp`;
3. clonar o projeto Apps Script usando o Script ID;
4. abrir o projeto localmente no VS Code;
5. mapear arquivos `.gs` e `appsscript.json`;
6. identificar funções executáveis, gatilhos, integrações e regras.

### 5.3 Exemplos de comandos esperados
```bash
npm install -g @google/clasp
clasp login
clasp clone 12-A3Ve0u1nlhI_3cKBj454LsA7aZRp2i0lOlj4Czu8QhSUgMoOy66uDz
```

### 5.4 Resultado esperado
O Codex deve produzir um inventário como:
- arquivo/função;
- tipo (utilitário, ETL, regra de negócio, output, fiscal, config);
- dependências;
- risco de portar;
- prioridade de portar.

---

## 6. Exploração da planilha Google Sheets
Se houver acesso real à planilha com permissão de editor, o Codex pode e deve explorar:
- nomes das abas;
- intervalos relevantes;
- fórmulas centrais;
- folhas de configuração;
- staging de dados externos;
- outputs fiscais.

### 6.1 O que procurar explicitamente
- abas tipo `config.*`;
- abas de operações;
- abas de proventos;
- abas de portfolio/summary/alocação/radar;
- abas fiscais (DARF, DIRPF, extratos etc.);
- qualquer separação entre normal trade/day trade;
- qualquer conceito de books/carteiras/investidores.

### 6.2 O que registrar
Produzir tabela no mínimo assim:

| Aba | Categoria | Papel | Depende de | Regras relevantes | Portar? |
|---|---|---|---|---|---|
| op.normal | input | ledger de operações normais | usuário | schema transacional | sim |
| portfolio | processamento | consolidação patrimonial | inputs + ETL | posição/alocação | sim |

---

## 7. Exploração via endpoint HTTP / `curl` — condicional
O usuário explicitamente levantou a ideia de explorar Apps Script “como endpoint” para debugar regras.

### 7.1 Diretriz
Isso **pode** ser útil, mas apenas se existir deployment web app funcional e se essa estratégia trouxer ganho real.

### 7.2 Só fazer se houver evidência de viabilidade
Critérios mínimos:
- deployment publicado e acessível;
- comportamento determinístico;
- sem risco de corromper dados do usuário;
- autorização explícita do usuário;
- logging claro.

### 7.3 Uso recomendado
Se viável, criar funções de inspeção controlada para:
- retornar outputs intermediários;
- testar regras específicas;
- comparar cálculo de referência vs cálculo do OV10.

### 7.4 O que **não** fazer
- não alterar silenciosamente a planilha original do usuário;
- não criar debug destrutivo;
- não assumir que qualquer link de projeto equivale a API pública pronta.

---

## 8. Sobre pesquisa pública na internet: `dlombelloplanilhas` / `DLombello Planilhas`
O usuário explicitamente quer que o Codex pesquise o que existir publicamente na internet sobre essa referência.

### 8.1 Mandato para o Codex
Pesquisar na internet por termos como:
- `dlombelloplanilhas`
- `DLombello Planilhas`
- `controle de investimentos dlombello`
- `planilha dlombello investimentos`
- variações razoáveis do nome

### 8.2 Objetivo da pesquisa
- coletar contexto público;
- identificar materiais explicativos, vídeos, posts, tutoriais, discussões, changelogs ou exemplos;
- descobrir pistas sobre arquitetura, escopo funcional e filosofia da solução;
- usar isso **somente** como inspiração e contexto, nunca como fonte única de verdade.

### 8.3 Restrições
- não assumir que conteúdo público representa a versão exata fornecida pelo usuário;
- não tratar marketing como documentação técnica;
- preferir sempre evidência extraída da planilha e do Apps Script reais.

---

## 9. Resultado mínimo exigido desta fase
O Codex deve entregar:
1. mapa da planilha por camadas;
2. mapa do Apps Script por arquivos/funções/responsabilidades;
3. tabela de regras de negócio portáveis;
4. gap analysis entre referência e OV10 atual;
5. proposta de como portar a arquitetura relevante sem herdar o legado ruim.

---

## 10. Regra final desta fase
Extrair conhecimento, **não** clonar a solução.
A referência serve para acelerar o design do OV10, não para prender o OV10 à tecnologia de planilha/Apps Script.
