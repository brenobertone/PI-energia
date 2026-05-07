# SIGET — Contrato Módulo Geral Subestação Tipo Arranjo

## Conteúdo
- `siget-contrato-modulogeral-subestacao-tipoarranjo.csv`
- `dm-siget-...pdf` — dicionário.

## Leitura
- separador `;` · encoding **latin1**.
- 502 linhas, 16 colunas.

## Estrutura
Cada linha = um módulo geral de subestação com seu **tipo de arranjo
elétrico**. Campos relevantes:

| campo | uso |
|---|---|
| `IdeOnsSbe` | ID ONS da subestação |
| `NomSubestacao`, `NomLongoSubestacao` | nomes |
| `SigUFSubestacao` | UF |
| `SglTipAnj`, `DscTipAnj` | tipo de arranjo: Disjuntor e Meio, Barra Dupla, Barra Simples, Anel, ... |
| `NumTnsMdl` | tensão do módulo (kV) |
| `IdcSitMdl` | situação (3 = ativa, tipicamente) |
| `NomMdl` | nome do módulo ("MG 230 kV PENEDO MG1 AL") |

## Como entra no modelo MILP
**Não entra** no capacity expansion. Tipo de arranjo elétrico é um atributo
de **projeto de subestação** relevante para:
- Estudos de confiabilidade (Disjuntor e Meio → maior tolerância N-1 que
  Barra Simples).
- Orçamento detalhado de expansão da SE (CAPEX varia com o arranjo).

Nenhum desses entra em modelos LP/MILP de planejamento energético de
geração.

## Recomendação
**Ignorar.** Mantemos o sidecar apenas para documentar que o dataset foi
inspecionado e descartado deliberadamente do escopo.
