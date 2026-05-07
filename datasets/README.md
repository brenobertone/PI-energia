# datasets — visão geral e mapa para o modelo MILP

Este diretório reúne os dados públicos de base para o projeto de
**capacity expansion planning** do setor elétrico brasileiro. Cada subpasta
tem seu próprio `README.md` detalhado. Aqui fica a leitura transversal:
**o que é data-driven de verdade e o que precisa ser assumido.**

## Inventário

| pasta | fonte | formato | escopo | granularidade |
|---|---|---|---|---|
| `carga_energia/` | ONS | parquet | 2025, SIN por subsistema | **diária**, 4 subsistemas |
| `fator_capacidade_eolica_solar/` | ONS | parquet (×12) | 2025, eólica+solar | **horária**, 262 conjuntos |
| `siga/` | ANEEL | csv | snapshot 2026-04 | por usina (todas) |
| `parametros_custo_geracao/` | EPE (PDE 2035) | **pdf** | 2024-2035 | por tecnologia (nacional) |
| `transmissao_energia/` | EPE (PDE 2035) | **pdf** | 2024-2035 | interligações (qualitativo) |
| `SIGET - Contrato Módulo Linha Transmissão/` | ANEEL/SIGET | csv | snapshot 2026-04 | linha-a-linha (kV, km, SE-SE) |
| `SIGET - Contrato Módulo Equipamento Subestacao/` | ANEEL/SIGET | csv | snapshot 2026-04 | trafos/reatores/conversoras |
| `SIGET - Contrato Módulo Geral Subestação Tipo Arranjo/` | ANEEL/SIGET | csv | snapshot 2026-04 | arranjo elétrico das SE |
| `demanda_eletricidade/` | EPE (PDE 2035) | **pdf** | 2025-2035 | nacional, por classe |
| `balanco_energetico_nacional/` | EPE (BEN) | xlsx | 2024 anual | nacional por fonte |
| `consolidacao_resultados/` | EPE (PDE 2035) | **pdf** | 2025-2035 | nacional integrado |

## Mapa parâmetro do modelo → dataset

| parâmetro MILP | data-driven? | fonte | como obter | risco |
|---|---|---|---|---|
| `D_{r,t}` (demanda) | parcial | `carga_energia` | diário OK; horário exige perfil intradiário assumido | médio |
| `α_{r,k,t}` eólica/solar | sim | `fator_capacidade_eolica_solar` | média ponderada por subsistema × tech | baixo p/ NE e S; proxy p/ N e SE/CO |
| `P0_{r,k}` (capacidade existente) | sim | `siga` (fase Operação) | pivot UF→subsistema × tech | baixo |
| `U_{r,k}` (potencial de expansão) | proxy | `siga` (pipeline) | outorgadas não iniciadas; inflar por fator | alto (hipótese) |
| `c_{r,k}^{inv}` (CAPEX anualizado) | sim, mas em PDF | `parametros_custo_geracao` | transcrever tabela + CRF(8 %, vida) | baixo |
| `c_{r,k}^{var}` (CVU térmicas) | sim, mas em PDF | `parametros_custo_geracao` | tabela CVU | baixo |
| `α_{r,k,t}` hidro / PCH | **não** | — | energia firme `MdaGarantiaFisicaKw` / P0 | alto |
| grafo da rede básica (pares (r,r') conectados) | sim | `SIGET - Linha Transmissão` | agregação UF→subsistema | baixo |
| `\bar F_{r,r'}^0` (capacidade de interligação MW) | proxy | `SIGET - Linha Transmissão` + PDE | n circuitos × kV → MVA via tabela; ou PDE (24 GW NE, etc.) | médio |
| `c^T_{r,r'}` (custo transmissão por MW·km) | proxy | `transmissao_energia` + `SIGET` | R$ 26,5 bi / 3 GW / 2.500 km ≈ 3,5 MR$/MW · km real do SIGET | médio |
| crescimento de demanda | proxy | `demanda_eletricidade` + `consolidacao_resultados` | 3,3 %/ano na geração elétrica (2025→2035) | médio |
| meta anual de energia | sim | `consolidacao_resultados` | 1.122 TWh em 2035 | baixo |
| % renovável-alvo | sim | `consolidacao_resultados` | ~51 % OIE, ~85 % do elétrico | baixo |

Regras:
- **"sim"** = o valor do parâmetro sai direto dos arquivos sem juízo adicional.
- **"proxy"** = o dataset dá uma aproximação defensável; hipótese precisa ser
  explicitada na formulação.
- **"não"** = exige dado externo ou arbítrio do modelador.

## O ponto metodológico mais importante
- **Carga é diária, fator de capacidade é horário.** Não há como fazer um
  modelo horário honesto só com este zip sem introduzir um perfil
  intradiário por subsistema (assumido).
- Possíveis caminhos:
  1. **Modelo diário**: agregar FC para diário também. Perde-se a
     anticorrelação solar/eólica dentro do dia e o valor da flexibilidade
     — é um erro caro para o tipo de estudo que este projeto quer fazer.
  2. **Modelo com horas representativas**: tirar `H` horas típicas por
     estação/mês (ex. 4 estações × 24 horas = 96 passos) e tratar cada passo
     com um peso `w_t`. Permite perfil intradiário sem explodir o tamanho.
     **Recomendado** para o primeiro MILP.
  3. **Modelo pleno 8760 h**: só depois que a estrutura estiver estabilizada.

## Derivação pretendida (pipeline de preparação)
```
datasets/ → scripts/prepare_*.py → instance/<name>.{json,npz}
   └─ usados pelo solver (pyomo/cvxpy/gurobipy, a definir)
```
Sugestão de ordem:
1. `prepare_demand.py`   → `D_{r,t}` com desagregação horária escolhida.
2. `prepare_renewables.py` → `α_{r,k,t}` ponderado por subsistema × tech.
3. `prepare_existing.py`  → `P0_{r,k}` a partir do SIGA.
4. `prepare_costs.py`     → CRF + tabela final `(r, k) → c^{inv}, c^{var}`.
5. `build_instance.py`    → serialização única da instância para o solver.

Scripts de inspeção (read-only) já estão em `scripts/inspect_*.py`.
