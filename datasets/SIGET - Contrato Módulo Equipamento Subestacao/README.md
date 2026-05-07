# SIGET — Contrato Módulo Equipamento Subestação

## Conteúdo
- `siget-contrato-moduloequipamento-subestacao.csv`
- `dm-siget-...pdf` — dicionário.

## Leitura
- separador `;` · encoding **latin1** · decimal vírgula.
- 2.306 linhas, 21 colunas.

## Estrutura
Cada linha = um **módulo de equipamento** instalado em uma subestação. Tipos
e quantidades observadas:

| tipo de equipamento | n | Σ potência (MVA) | obs |
|---|---:|---:|---|
| Transformador de Potência | 823 | 222.861 | capacidade em `MdaPotAtvMdlEqp` |
| Reator de Linha | 813 | — | potência não preenchida |
| Reator de Barra | 355 | — | idem |
| Transformador de Aterramento | 71 | 988 | |
| Banco de Capacitores | 66 | — | Mvar em outra coluna |
| Capacitor Série | 42 | — | |
| Compensador Síncrono | 39 | — | |
| Banco de Filtros | 36 | — | auxiliar HVDC |
| Compensador Estático (SVC) | 31 | — | |
| **Conversora** | **30** | **42.878** | **conversores HVDC** (Belo Monte, Madeira, ...) |

Colunas principais: `DscTipEqp` (tipo), `NomSubestacao` / `IdeOnsSbe` (SE
hospedeira), `MdaPotAtvMdlEqp` (potência ativa, MVA), `NumTnsMdl` (tensão, kV),
`DscFinMdlEqp` (Principal/Reserva).

## Como entra no modelo MILP
Baixa relevância para capacity expansion. Usos possíveis (segundo plano):
- **Limite de injeção por SE** em um modelo nodal: a capacidade de
  transformação (Σ MVA de transformadores de potência) é proxy de "quanto
  aquele nó consegue escoar" — útil em modelagem de alta granularidade.
- **Identificação de nós HVDC** (as 30 conversoras marcam os terminais dos
  bipolos existentes) — útil se quiser representar explicitamente os elos
  DC como arcos especiais no grafo.
- **Não entra em função objetivo nem em restrições primárias** de um MILP
  de expansão de geração.

## Limitações
- A coluna `MdaPotAtvMdlEqp` só é preenchida para transformadores e
  conversoras. Para capacitores/reatores há colunas separadas (Mvar) não
  preenchidas no que inspecionei.
- É um cadastro de equipamentos individuais, não de "capacidades agregadas"
  — precisa agregar por SE antes de usar.

## Recomendação
**Ignorar no escopo atual.** Se o projeto evoluir para análise de
confiabilidade N-1 ou estudo nodal fino, reavaliar.
