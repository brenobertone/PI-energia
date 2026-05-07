# carga_energia — ONS, Carga de Energia diária por subsistema

## Conteúdo
- `CARGA_ENERGIA_2025.parquet` — série **diária** (2025-01-01 → 2025-12-31) de
  carga de energia por subsistema, em **MWmed** (média de potência durante o dia).
- `DicionarioDados_Carga_Energia_Diaria.pdf` — dicionário oficial dos campos.

## Estrutura (parquet)
| coluna | tipo | obs |
|---|---|---|
| `id_subsistema` | string | N, NE, S, SE (4 valores) |
| `nom_subsistema` | string | "Norte", "Nordeste", "Sul", "Sudeste/Centro-Oeste" |
| `din_instante` | datetime64[ns] | dia (365 timestamps no ano) |
| `val_cargaenergiamwmed` | float64 | carga em MWmed |

Dimensão: 1460 linhas (365 dias × 4 subsistemas).

## Estatísticas rápidas (2025)
- Carga média diária SIN (soma dos 4 subsistemas): ~**79,6 GWmed**.
- Decomposição por subsistema (MWmed, média anual):
  - SE/CO ~ 46k  · NE ~ 13k  · S ~ 11k  · N ~ 7k

## Granularidade vs. outros datasets — **ponto metodológico crítico**
- Aqui a carga é **diária**.
- O dataset de fator de capacidade (eólica/solar) é **horário** — 8760 passos.
- Logo, não temos carga **horária** no zip. Para fechar um modelo de despacho
  horário, ou se estima um perfil intradiário a partir de outra fonte
  (ex.: ONS "Carga horária" ou curvas típicas BEN/EPE), ou se agrega tudo no
  nível diário (perde-se grande parte do valor do perfil renovável).
- Alternativa pragmática para o trabalho: reconstruir carga horária
  multiplicando a média diária por um perfil horário normalizado do
  subsistema (típico "curva de carga"), assumido.

## Como entra no modelo MILP
- `D_{r,t}` = demanda [MW] do subsistema `r` na hora/dia `t`.
- Se `t` for dia, deve-se **interpretar** a restrição de atendimento como
  energia diária; se for hora, construir `D_{r,t}` por disagregação.
- Cobre apenas o ano de 2025 → não dá dinâmica plurianual de crescimento de
  demanda. Crescimento de demanda é cenário (EPE, documento
  `demanda_eletricidade/`).

## Limitações
- MWmed diário ≠ pico. Planejamento de potência firme e de reserva exige o
  pico horário, que este arquivo não carrega.
- Não há discriminação por setor nem por ponto de conexão.
