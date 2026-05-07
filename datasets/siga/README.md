# siga — ANEEL SIGA (Sistema de Informações de Geração)

## Conteúdo
- `siga-empreendimentos-geracao.csv` — cadastro de unidades geradoras.
- `dm-siga-sistema-de-informacoes-de-geracao-da-aneel.pdf` — dicionário ANEEL.

## Leitura
- **separador**: `;` · **encoding**: `latin1` · **decimal**: vírgula (!)
  → converter: `MdaPotenciaOutorgadaKw`, `MdaPotenciaFiscalizadaKw`,
  `MdaGarantiaFisicaKw`, coordenadas.

## Estrutura (23 colunas, 25.417 linhas)
Colunas-chave para o modelo:
| coluna | descrição |
|---|---|
| `SigTipoGeracao` | UFV, EOL, UHE, UTE, PCH, CGH, UTN |
| `DscFaseUsina` | Operação / Construção / Construção não iniciada |
| `NomFonteCombustivel` | detalhe (Radiação solar, Bagaço de Cana, Gás Natural, ...) |
| `SigUFPrincipal` | UF — proxy para subsistema |
| `MdaPotenciaOutorgadaKw` | capacidade autorizada (kW) |
| `MdaGarantiaFisicaKw` | energia firme (kW) — importante! |
| `NumCoordNEmpreendimento` / `NumCoordEEmpreendimento` | lat/long |
| `DatEntradaOperacao` | data de entrada em operação |

## Panorama (MW → GW outorgado)
| tech | Em Operação | Em Construção | Não iniciada |
|---|---:|---:|---:|
| Hidro (UHE) | 103,27 | 0,05 | 0,21 |
| Térmica (UTE) | 49,51 | 4,93 | 0,93 |
| Eólica (EOL) | 34,91 | 1,43 | **15,97** |
| Solar (UFV)  | 22,31 | 2,67 | **89,33** |
| PCH | 6,07 | 0,32 | 1,07 |
| Nuclear (UTN) | 1,99 | 1,35 | — |
| CGH | 0,91 | 0,00 | 0,02 |

Pipeline **solar "não iniciada" ≈ 90 GW** e eólico ≈ 16 GW — sinal locacional
do que já está outorgado.

### Em Operação, por subsistema (GW)
|  | N | NE | S | SE/CO |
|---|---:|---:|---:|---:|
| Hidro | 25,20 | 11,98 | 22,63 | 43,46 |
| Eólica | 0,00 | 32,54 | 2,34 | 0,03 |
| Solar | 0,03 | 11,84 | 0,10 | 10,33 |
| Térmica | 2,99 | 11,20 | 5,27 | 30,05 |

Subsistema derivado de `SigUFPrincipal` via mapeamento ONS (SE/CO inclui AC,
RO; N = PA AP AM RR TO — aproximação para o SIN — PA é parte de N no ONS).

## Como entra no modelo MILP
- `P0_{r,k}` — capacidade **instalada existente** (soma por subsistema × tech,
  filtrando `DscFaseUsina == "Operação"`).
- `U_{r,k}` — **limite superior de expansão** `x_{r,k} ≤ U_{r,k}`. Uma escolha
  defensável: usar o pipeline outorgado (`Construção` + `Construção não iniciada`)
  como proxy de potencial locacional de curto prazo — ou inflar por fator (2×,
  5×) para representar potencial de médio prazo.
- Garantia física (`MdaGarantiaFisicaKw`) é proxy útil para hidráulicas,
  que não aparecem no dataset de FC.

## Limitações
- UF → subsistema é aproximação (AC/RO no ONS são N ou SE/CO dependendo do
  ano; o mapeamento aqui segue o SIN atual — verificar se precisar de rigor).
- `MdaPotenciaOutorgadaKw` ≠ capacidade efetiva; `MdaPotenciaFiscalizadaKw`
  é mais próximo do instalado comissionado. Usar fiscalizada quando não nula.
- Cadastros têm duplicatas potenciais (UGs x UHE agrupadoras) — checar antes
  de somar.
