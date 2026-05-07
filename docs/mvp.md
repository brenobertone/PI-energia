# MVP — MILP de Capacity Expansion do SIN

Documento de referência do **que está sendo modelado** e **onde cada peça
vive**. Alinhado com o plano de implementação
(`/Users/bertone/.claude/plans/quero-implementar-o-mvp-milp-wise-fairy.md`).

## 1. Conjuntos

| símbolo | definição | valores |
|---|---|---|
| `R` | subsistemas | `{N, NE, S, SE_CO}` |
| `K` | tecnologias | `{sol, eol, hidro, term}` |
| `K_exp ⊂ K` | tecnologias expansíveis | `{sol, eol}` |
| `T` | passos temporais | `1..288` (12 meses × 24 horas) |
| `A ⊆ R × R` | arcos dirigidos de transmissão | 8 arcos (cada par inter-subsistema dirigido duas vezes) |

## 2. Parâmetros

| símbolo | unidade | fonte | arquivo | coluna MART |
|---|---|---|---|---|
| `D_{r,t}` | MW | ONS — carga diária (flat intradiário) | `/Users/bertone/Coding/PI-energia/datasets/carga_energia/CARGA_ENERGIA_2025.parquet` | `mart_demanda.mw` |
| `α_{r,k,t}` | [0, 1] | ONS — fator de capacidade horário (ponderado) | `/Users/bertone/Coding/PI-energia/datasets/fator_capacidade_eolica_solar/FATOR_CAPACIDADE-2_*.parquet` | `mart_disponibilidade.alpha` |
| `P0_{r,k}` | MW | ANEEL SIGA (fase "Operação") | `/Users/bertone/Coding/PI-energia/datasets/siga/siga-empreendimentos-geracao.csv` | `mart_capacidade_existente.p0_mw` |
| `B_k` | MW | PDE 2035 transcrito | `/Users/bertone/Coding/PI-energia/data/pde_custos.yml` | `mart_parametro_tech.bloco_mw` |
| `c^{inv}_k` | R$/MW·ano | PDE 2035 + CRF(WACC=8%) | `/Users/bertone/Coding/PI-energia/data/pde_custos.yml` | `mart_parametro_tech.c_inv_anualizado_rs_mw_ano` |
| `c^{var}_k` | R$/MWh | PDE 2035 (CVU) | `/Users/bertone/Coding/PI-energia/data/pde_custos.yml` | `mart_parametro_tech.cvu_rs_mwh` |
| `w_t` | dias | calendário civil (`config.DIAS_MES`) | `/Users/bertone/Coding/PI-energia/src/pi_energia/config.py` | `mart_passo.w_t` |
| `F̄_{r,r'}` | MW | SIGET × tabela MVA/kV (hipótese) | `/Users/bertone/Coding/PI-energia/data/ref_mva_por_tensao.yml` | `mart_arco.f_barra_mw` |
| `E^{firme}_r` | MWh/ano | SIGA — garantia física hidro em operação × 8760 | `/Users/bertone/Coding/PI-energia/datasets/siga/siga-empreendimentos-geracao.csv` | `mart_energia_firme.mwh_ano` |
| `V` | R$/MWh | VOLL assumido (5.000 R$/MWh) | `config.py` / `mart_instancia.voll` | `mart_instancia.voll` |

### 2.1 Como `α_{r,k,t}` é construído
- RAW FC horário em `raw_fator_capacidade` (1,93M linhas).
- Em `stg_fc_horario_ponderado`: `fc_{r,k,t} = Σ_usinas gen_{u,t} / Σ_usinas cap_{u,t}`
  onde `gen = cap × fc`.
- Em `mart_disponibilidade`: média do FC horário agrupada por `(mes, hora)`
  dentro do subsistema, replicada para cada passo `t = (mes, hora)`.
- Para `(N, sol)`, `(S, sol)` e `(SE_CO, eol)` — pares que **não** têm usinas
  no ONS — usa-se **proxy do subsistema vizinho**: NE→N, SE_CO→S e S→SE_CO.
- Para `hidro` e `term`: `α = 1` (variável livre restringida por outros
  vínculos — orçamento anual para hidro, CVU para térmica).

### 2.2 Como `F̄_{r,r'}` é calibrado
Hipótese explícita em `data/ref_mva_por_tensao.yml`:
| kV  | MVA/circuito |
|----:|---:|
| 230 | 300 |
| 345 | 700 |
| 440 | 1.000 |
| 500 | 1.400 |
| 525 | 1.500 |
| 600 | 2.800 (HVDC) |
| 800 | 4.000 (HVDC) |

`F̄_{r,r'} = Σ_{kV} n_circuitos(r,r',kV) × MVA_{ref}(kV) × fp`, `fp = 0,95`.
Valores resultantes para os arcos ativos do SIN em 2025:

| par | MW |
|---|---:|
| N ↔ NE | 5.130 |
| N ↔ SE_CO | 16.530 |
| NE ↔ SE_CO | 27.550 |
| S ↔ SE_CO | 5.890 |

N↔S e NE↔S **não existem** no grafo (não há linha direta no SIGET).

## 3. Variáveis

| símbolo | domínio | interpretação |
|---|---|---|
| `y_{r,k}` | `ℤ₊`, só `k ∈ K_exp` | nº de blocos de tamanho `B_k` construídos em `r` |
| `g_{r,k,t}` | `ℝ₊` | geração despachada (MW) |
| `f_{r,r',t}` | `ℝ` | fluxo no arco `(r,r')` (positivo de `r` para `r'`) |
| `s_{r,t}` | `ℝ₊` | demanda não atendida (MW) |

Capacidade total após expansão: `P_{r,k} = P0_{r,k} + B_k · y_{r,k}`
(ou só `P0_{r,k}` para `k ∉ K_exp`).

## 4. Restrições

### (balanço)
```
Σ_k g_{r,k,t}  +  Σ_{(o,r)∈A} f_{o,r,t}  −  Σ_{(r,d)∈A} f_{r,d,t}  +  s_{r,t}  =  D_{r,t}   ∀ r, t
```
Conservação de energia em cada subsistema e passo: geração local + importação
líquida + déficit cobre a demanda.

### (disponibilidade)
```
g_{r,k,t}  ≤  α_{r,k,t} · (P0_{r,k} + B_k · y_{r,k})   ∀ r, k, t
```
Para `k ∉ K_exp`, o segundo termo é zero.

### (orçamento hidráulico)
```
Σ_t w_t · g_{r, hidro, t}  ≤  E^{firme}_r       ∀ r
```
A hidro tem flexibilidade intradiária (pode deslocar para a ponta), mas o
total de energia gerada no ano é limitado pela garantia física.

### (transmissão)
```
−F̄_{r,r'}  ≤  f_{r,r',t}  ≤  F̄_{r,r'}         ∀ (r,r') ∈ A, t
```
Fluxo não excede a capacidade. Modelo de *transportation* (sem Kirchhoff de
tensão).

### (integralidade)
```
y_{r,k} ∈ ℤ₊   ∀ r, k ∈ K_exp
```
É o único componente inteiro do modelo.

## 5. Objetivo

```
min   Σ_{r, k∈K_exp}  c^{inv}_k · B_k · y_{r,k}         [investimento anualizado]
    + Σ_{r,k,t}       w_t · c^{var}_k · g_{r,k,t}       [operação (CVU × energia)]
    + Σ_{r,t}         w_t · V · s_{r,t}                  [penalidade de déficit]
```
Unidades: todos os termos em R$/ano.

## 6. Hipóteses adotadas

1. **Perfil intradiário de demanda é flat** — a carga ONS é diária (MWmed);
   espalhamos como constante nas 24 horas do dia típico do mês. Isto preserva
   sazonalidade mensal mas não capta o pico vespertino.
2. **FC ponderado pelas usinas existentes** — introduz viés locacional
   (sites atualmente em operação não representam necessariamente os melhores
   sites *futuros*).
3. **Hidro sem reservatório, sem cascata** — é uma "bateria anual"
   `E^{firme}` que pode ser despachada livremente no ano, limitada apenas
   pela capacidade instalada (`P0_hidro`) e pelo orçamento total.
4. **`F̄_{r,r'}` por hipótese MVA/kV** — o SIGET não traz MVA nominal;
   a tabela em `data/ref_mva_por_tensao.yml` é um proxy pedagógico.
   **Fator de potência 0,95**.
5. **UF → subsistema pelo mapa ONS atual** em `config.UF_TO_SUB`. AC/RO
   vão para SE_CO (convenção SIN); TO e estados do Norte vão para N.
6. **CRF anualizado com WACC real 8%** (PDE 2035, Dez/2024, R$). Sem
   deflator futuro.
7. **Proxy para α renovável faltante**: N-sol ← NE-sol, S-sol ← SE_CO-sol,
   SE_CO-eol ← S-eol.
8. **VOLL único `V = 5.000 R$/MWh`**. Déficit é apenas uma válvula: o modelo
   deve fechar com déficit praticamente nulo em instâncias bem parametrizadas.
9. **Flow é modelo de transportation**, não DCOPF. Sem lei de Kirchhoff de
   tensão, sem impedâncias — apenas balanço e capacidade de arco.
10. **Arcos dirigidos simétricos** — cada par inter-subsistema aparece como
    dois arcos em `A`; a capacidade é a mesma em ambas as direções.

## 7. Fora de escopo (deliberado)

- rampa de geração, tempos mínimos de partida/parada (unit commitment)
- reserva girante / operação
- DCOPF com impedâncias (linhas AC tratadas como transportes)
- multi-ano (horizonte plurianual)
- formulação estocástica (cenários de demanda/recurso)
- candidatos de projeto individuais (pipeline SIGA)
- curtailment explícito de renovável (aqui implícito: `g ≤ α·cap`)
- emissões de CO₂ / restrição ambiental
- rede por barra (representação por subestação)

## 8. Critérios de aceite

| check | esperado | onde |
|---|---|---|
| Demanda anual total | 600–800 TWh (SIN 2025) | `postprocess.sanity_checks` |
| `Σ w_t` | = 8.760 exato | assertion em `build_instance` |
| `α ∈ [0, 1]` | sim | assertion em `mart_disp` |
| Déficit total | ≈ 0 TWh | `MartResultadoDeficit` / `sanity_checks` |
| gap LP-MILP | < 5 % | `solver.solve_with_lp_bound` |
| wall time HiGHS | < 30 s | log / `MartResultadoResumo` |

## 9. Comando único de smoke test

```bash
poetry run pi init-db
poetry run pi ingest
poetry run pi build-instance mvp-2025
poetry run pi solve mvp-2025
poetry run pi report mvp-2025
```

## 10. Onde evoluir (V1..V4)

Ver `§9` do plano de implementação. Estão previstas como extensões aditivas
ao schema:
- **V1**: binária de reforço HVDC NE–SE e baterias como `is_expansivel`.
- **V2**: candidatos individuais via `DimUsinaSiga`.
- **V3**: multi-ano com `DimSnapshotAno` e estocástico com `MartCenario`.
- **V4**: DCOPF por subestação usando `IdeOnsSbeOrigem/Destino` do RAW SIGET.
