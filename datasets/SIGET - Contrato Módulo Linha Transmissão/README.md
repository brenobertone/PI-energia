# SIGET — Contrato Módulo Linha Transmissão

## Conteúdo
- `siget-contrato-modulolinhatransmissao-subestacaoorigem-subestacaodestino.csv`
- `dm-siget-...pdf` — dicionário oficial ANEEL (Ver. 1.0, 28-04-2023).

## Leitura
- separador `;` · encoding **latin1** · decimal vírgula em km e kV.
- 1.160 linhas, 29 colunas, snapshot 2026-04-27.

## Estrutura
Cada linha = uma linha de transmissão da **rede básica** (≥ 230 kV
tipicamente). Campos relevantes para modelagem:

| campo | uso |
|---|---|
| `DscSitLinTms` | Ativa / Desativada (1.123 / 37) |
| `IdeOnsSbeOrigem`, `IdeOnsSbeDestino` | IDs ONS das SE origem/destino → **grafo** |
| `NomSubestacaoOrigem`, `NomSubestacaoDestino` | nomes legíveis |
| `SigUFSubestacaoOrigem`, `SigUFSubestacaoDestino` | UF por ponta → subsistema |
| `NumTensaoBaseLinhaTransm` | tensão (kV) |
| `NumEtnLinTms` | extensão (km) |
| `NumCcuLinTms` | número do circuito (1º, 2º, …) |
| `IdcTipoCircuitoLinhaTransm` | simples (0) / duplo (1) |

### Distribuição por tensão
| kV  | n linhas | km total | km média |
|---:|---:|---:|---:|
| 230 | 565 | 43.701 | 77 |
| 345 | 86 | 4.860 | 56 |
| 440 | 36 | 3.609 | 100 |
| 500 | 370 | 68.735 | 186 |
| 525 | 46 | 7.053 | 153 |
| 600 | 3 | 7.206 | 2.402 (HVDC) |
| 800 | 6 | 12.198 | 2.033 (HVDC) |

### Linhas inter-subsistema ativas (proxy de interligações do SIN)
| par subsistema | kV | n linhas | km total |
|---|---:|---:|---:|
| N ↔ NE | 230 | 4 | 557 |
| N ↔ NE | 500 | 3 | 1.149 |
| N ↔ SE/CO | 500 | 1 | 196 |
| N ↔ SE/CO | 800 | 4 | 9.262 |
| NE ↔ SE/CO | 500 | 15 | 4.018 |
| NE ↔ SE/CO | 800 | 2 | 2.936 |
| S ↔ SE/CO | 230 | 2 | 147 |
| S ↔ SE/CO | 500 | 4 | 1.104 |

Observação: **não há linha direta** N ↔ S nem NE ↔ S — S se conecta ao SIN
apenas via SE/CO. Isso é uma restrição topológica natural.

## Como entra no modelo MILP
Primeiro dataset do zip que suporta representação de rede de verdade.

Usos imediatos para um modelo multi-barra (4 subsistemas):
- **Grafo fixo** `A ⊆ {(r, r') : r ≠ r'}` = pares com ao menos uma linha
  ativa. Evita modelar arcos inexistentes.
- **Caracterização topológica** de cada par: `(km total, tensão dominante,
  n circuitos)` — ajuda a escolher tecnologia-base (CA 500 kV × HVDC).
- **Custo unitário de expansão** `c^T_{r,r'}`: combinar (km) com R$/MW·km
  de referência do PDE (HVDC-VSC ≈ R$ 26,5 bi / 3 GW / 2.500 km ≈ 3,5 MR$/MW).

Para um modelo **nodal por subestação** (nível mais fino), os IDs
`IdeOnsSbeOrigem/Destino` dão o grafo completo (~500 nós, 1.123 arcos
ativos).

## Limitações sérias
- **Não traz MVA nominal (capacidade térmica) da linha.** Para DCOPF ou
  restrição de fluxo, é preciso inferir a partir de (kV, tipo de condutor,
  n circuitos) — tabelas de referência ONS ou aproximação tipo
  `S_{max} ≈ 1,0 × V² / x` exigem dados extras.
- **Não traz impedância.** DCOPF completo fica fora — mas um modelo de
  "transportation" (só capacidade, sem Kirchhoff tensão) é viável.
- **Não traz custos diretos** (CAPEX/RAP). O custo tem que vir do PDE ou
  do MELP da EPE.
- Coluna `QtdTorLinTms` (quantidade de torres) frequentemente ausente
  para LTs novas.

## Recomendação
Usar quando o modelo evoluir de uninodal para multi-barra (Sistema 2).
Para o Sistema 1 (uninodal NE), este dataset fica de fora.
