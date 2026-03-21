# 10. ACESSOS GOOGLE APPS SCRIPT / APP WEB

Este arquivo consolida os identificadores e URLs operacionais que o Codex deve considerar ao explorar o projeto de referência baseado em Google Sheets + Apps Script.

## 1. Projeto Apps Script

- **Script ID / Código do script**: `12-A3Ve0u1nlhI_3cKBj454LsA7aZRp2i0lOlj4Czu8QhSUgMoOy66uDz`
- **URL do projeto Apps Script**: `https://script.google.com/home/projects/12-A3Ve0u1nlhI_3cKBj454LsA7aZRp2i0lOlj4Czu8QhSUgMoOy66uDz/edit`

## 2. Deploy do App Web

- **Deployment ID / Código de implantação**: `AKfycbyUKw10d2EP589uAy55lHuuApz6h4A5sDJAvK6fMc_1gxG7a4F0jdyfu5j5uSRrT9a6bQ`
- **App Web URL**: `https://script.google.com/macros/s/AKfycbyUKw10d2EP589uAy55lHuuApz6h4A5sDJAvK6fMc_1gxG7a4F0jdyfu5j5uSRrT9a6bQ/exec`

## 3. Planilha Google Sheets associada

- **URL principal**: `https://docs.google.com/spreadsheets/d/1k4YS0jQRMzDVp34DLL8Yhb8rgM_89pGqcP-JABLRO7U/edit?gid=185866544#gid=185866544`
- **URL de compartilhamento com permissão de editor**: `https://docs.google.com/spreadsheets/d/1k4YS0jQRMzDVp34DLL8Yhb8rgM_89pGqcP-JABLRO7U/edit?usp=sharing`
- **Spreadsheet ID**: `1k4YS0jQRMzDVp34DLL8Yhb8rgM_89pGqcP-JABLRO7U`

## 4. Diretriz para o Codex

O Codex deve tratar esses dados como insumos operacionais para:

1. explorar o projeto via `clasp` no VS Code;
2. clonar/sincronizar o Apps Script localmente quando aplicável;
3. inspecionar a planilha como camada de dados e cálculo;
4. testar, quando viável, o `App Web URL` como endpoint HTTP para observar saídas e comportamento;
5. mapear quais regras de negócio residem:
   - na planilha,
   - no Apps Script,
   - no deploy web,
   - e quais podem ser convertidas para o domínio canônico do OV10.

## 5. Ordem de exploração recomendada

1. **Abrir a planilha e mapear abas/camadas**
2. **Clonar o Apps Script com `clasp`**
3. **Inspecionar funções públicas, menus, triggers e pontos de entrada**
4. **Testar o app web/endpoint implantado**
5. **Inferir contratos de entrada/saída**
6. **Extrair regras de negócio e classificar por módulo-alvo do OV10**

## 6. Observações importantes

- O fato de existir um `exec` público **não garante** que todas as regras do sistema estejam expostas por HTTP.
- Parte relevante da lógica pode estar distribuída entre:
  - fórmulas da planilha,
  - Apps Script vinculado à planilha,
  - menus customizados,
  - gatilhos (`onOpen`, `onEdit`, time-driven etc.),
  - e endpoints do app web.
- O objetivo não é copiar cegamente a implementação, mas **usar a referência para mapear regras, arquitetura e decisões úteis ao OV10**.

## 7. Instrução objetiva

O Codex deve usar estes acessos para conduzir reverse engineering controlado e documentado do sistema de referência, priorizando extração de regras de negócio, contratos de dados e arquitetura por camadas.
