# parametros_custo_geracao — EPE / PDE 2035, "Parâmetros de Custos"

## Conteúdo
- PDF único (`Parâmetros de Custos Geração e Transmissão.pdf`, 3,4 MB) com as
  tabelas oficiais de CAPEX/O&M/vida útil/CVU por fonte adotadas no PDE 2035.
- Data base Dez/2024, câmbio **R$ 6,10 / USD**, **WACC real = 8 %**.

## Parâmetros econômicos por tipo de oferta (síntese)

CAPEX de referência (sem JDC) e O&M (R$/kW; R$/kW.ano; vida útil anos).
Fonte: slides 10-12 do PDF.

| fonte | CAPEX ref (R$/kW) | faixa CAPEX | O&M (R$/kW.ano) | impostos/enc. | vida (anos) | tempo desembolso (meses) |
|---|---:|---|---:|---:|---:|---:|
| Solar FV | 3.500 | 3.000–6.000 | 60 | 130 | 25 | 12 |
| Solar FV (4 patamares) | 3.000 / 3.500 / 4.500 / 5.500 | idem | 60 | 120 / 130 / 130 / 140 | 25 | 12 |
| FV Flutuante | 6.800 | 4.000–8.500 | 80 | 150 | 25 | 12 |
| Eólica Onshore | 5.000 / 5.500 / 6.200 / 7.000 | 4.500–8.000 | 110 | 150–160 | 20 | 24 |
| Eólica Offshore | 18.000 | 10.500–25.000 | 400 | 630 | 20 | 36 |
| Baterias (BESS Li-íon, 4 h) | 5.000 / 5.500 / 6.000 | 5.000–9.000 | 130–160 | 240–260 | 20 | 12 |
| Usina Reversível | 9.100 | 6.000–15.000 | 90 | 410 | 30 | 36 |
| Biocombustível | 3.500 | 3.000–5.000 | 150 | 200 | 20 | 36 |
| Biogás (resíduos) | 14.000 | 8.000–16.000 | 600 | 250 | 20 | 24 |
| Biomassa – Cana | 3.500 / 4.500 / 6.000 | 3.000–7.000 | 100 | 130–150 | 20 | 24 |
| Biomassa – Madeira | 7.500 | 5.500–8.500 | 160 | 170 | 20 | 36 |
| Biomassa + CCS (BECCS) | 27.800 | 25.000–30.000 | 980 | 1.000 | 20 | 36 |
| Carvão Nacional | 15.000 | 9.000–17.000 | 300 | 900 | 25 | 48 |
| Carvão + CCS | 32.000 | 28.000–35.000 | 800 | 1.700 | 25 | 48 |
| Gás Natural – 100 % Flex | 4.500 | 3.000–5.000 | 190 | 240 | 20 | 24 |
| Gás Natural – 70 % Inflex | 5.500 | 3.500–7.000 | 850 | 350 | 20 | 36 |
| Gás Natural – 100 % Inflex | 7.600 | 3.500–9.000 | 180 | 340 | 20 | 36 |
| Gás Natural + CCS | 18.500 | 17.000–20.000 | 400 | 690 | 20 | 36 |
| Nuclear | 35.000 | 30.000–50.000 | 760 | 820 | 30 | 60 |
| PCH | 7.000 / 9.000 / 12.000 | 6.000–14.000 | 60 | 130 / 150 / 170 | 30 | 30 |
| RSU – Incineração | 30.000 | 20.000–36.000 | 1.400 | 1.080 | 20 | 36 |

### CVU (Custo Variável Unitário) — usinas termelétricas
| fonte | CVU (R$/MWh) |
|---|---:|
| Gás Natural – 100 % Flex  | 1.000 |
| Gás Natural – 70 % Inflex | 490 |
| Gás Natural – 100 % Inflex | 430 |
| Gás Natural + CCS | 430 |
| Biocombustível | 2.050 |
| Biomassa – Cavaco | 250 |
| Carvão (c/ e s/ CCS) | 180 |
| Nuclear | 60 |

### UHEs individualizadas (PDE 2035, slide 14)
11 projetos com CAPEX ref (R$/kW) próprio — Bem Querer 650 MW · 12.919, Jatobá
1.650 MW · 12.686, etc. Potência total ≈ 4,86 GW.

### Valores em US$ (slide 13)
Tabela paralela convertendo a R$ 6,10/USD — útil para comparação com fontes
internacionais (IEA, NREL ATB).

## Como entra no modelo MILP
- `c_{r,k}^{inv}` = CAPEX anualizado = CAPEX × CRF(r, vida) + O&M + encargos.
  CRF = r(1+r)^n / ((1+r)^n − 1) com r = 0,08, n = vida útil da tecnologia.
- `c_{r,k}^{var}` = CVU em R$/MWh para térmicas (zero para eólica/solar/hidro
  em modelos estilizados).
- As **faixas** de CAPEX (mín/máx) permitem análise de sensibilidade ou uma
  formulação estocástica de primeiro estágio.

## Limitações
- **É um PDF** → valores precisam ser transcritos para tabelas estruturadas
  (csv/yaml) antes de virar dados do modelo. Sem OCR — os números aqui vêm
  da leitura visual.
- Valores nacionais médios → não há variação regional de CAPEX (possível
  mas ausente neste dataset).
- Datas de base Dez/2024; considerar deflator caso use carga/geração de outro
  ano como referência.
