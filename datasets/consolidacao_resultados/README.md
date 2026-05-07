# consolidacao_resultados — EPE / PDE 2035, "Consolidação de Resultados"

## Conteúdo
- `Consolidação de Resultados.pdf` (2,4 MB, Mar/2026) — caderno que integra os
  resultados das demais publicações do PDE 2035. Traz indicadores econômico-
  energéticos, decomposição carga/consumo e evolução da OIE (Oferta Interna
  de Energia) e da geração elétrica.

## Âncoras numéricas (cenário de referência)
### Indicadores macro 2025 → 2035 (slide 7)
| indicador | 2025 | 2035 | CAGR |
|---|---:|---:|---:|
| PIB (índice 2025=100) | 100 | 131 | 2,7 %/ano |
| População (M hab.) | 213,8 | 219,5 | 0,27 %/ano |
| PIB per capita (10³ R$[2010]/hab.) | 22,0 | 28,1 | 2,5 %/ano |
| OIE per capita (tep/hab.) | 1,54 | 1,88 | 2,0 %/ano |
| **Geração de energia elétrica per capita (kWh/hab.)** | **3.791** | **5.112** | **3,0 %/ano** |
| Consumo final energético (Mtep) | 284,0 | 341,5 | 1,9 %/ano |

### Oferta de energia elétrica (slide 7, texto)
- **2035: 1.122,1 TWh** · CAGR 3,3 %/ano (2025 → 2035).
- Em 2025 (por produto das duas curvas): ~810 TWh; em 2030: ~950 TWh
  (consistente com 3,3 %/ano).

### OIE (Mtep) e % renovável (slide 10)
| ano | OIE total | % renovável | gás natural | petróleo |
|---:|---:|---:|---:|---:|
| 2025 | 329,6 | 51 % | 10 % | 33 % |
| 2030 | 375,3 | 50 % | 13 % | 31 % |
| 2035 | 411,9 | 51 % | 13 % | 29 % |

Setor elétrico passa de 27 % para 30 % da OIE (eletrificação).

### Decomposição consumo → carga (slide 8)
A EPE decompõe a carga em: consumo potencial → eficiência elétrica →
consumo total → autossuprimento (D1 autoprodução não injetada + D2 MMGD) →
consumo das classes → sistemas isolados → perdas → carga global SIN.
Isso explicita onde o MILP faz cortes (MMGD, autoprodução, isolados).

## Como entra no modelo MILP
- **Meta anual de energia (cenário)**: use 1.122 TWh em 2035 como valor-alvo
  para `∑_{r,t} g_{r,k,t} × w_t ≥ E^{alvo}` em um modelo de energia-anual.
- **Crescimento do setor elétrico**: 3,3 %/ano sobre carga de 2025 dá o
  multiplicador de demanda para anos-alvo (2030: ×1,18; 2035: ×1,38 sobre
  a carga de 2025).
- **Meta renovável**: o PDE projeta ~51 % renovável no total (OIE — inclui
  todos os vetores). Para o setor **elétrico** a fração é muito maior
  (~85 % hoje). Isso motiva restrições do tipo
  `∑ g_{renovável} ≥ φ × D_{total}` com `φ` calibrado.
- **Sanity-check**: ao resolver o MILP para 2035, o resultado em GWh deve
  fechar com 1.122 TWh (± margem para perdas e autoprodução).

## Limitações
- PDF — transcrição manual das tabelas.
- Nível nacional (sem desagregação por subsistema): o crescimento por
  subsistema é implícito no caderno "Demanda de Eletricidade" e exige
  hipótese para separar.
- Os cenários inferior/superior não aparecem aqui; aparecem em
  `datasets/demanda_eletricidade/`.
