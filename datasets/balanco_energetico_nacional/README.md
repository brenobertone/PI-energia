# balanco_energetico_nacional — EPE, BEN 2024

## Conteúdo
- `Matriz ab2024.xlsx` — planilha com 3 abas:
  - `MATRIZ 2024` (131 × 54): matriz aberta por fonte × fluxo, em 10³ tep.
  - `Matriz aberta 2024`: variante.
  - `Consolidada2024` (60 × 30): formato consolidado, também em 10³ tep.

## Estrutura (tem header embutido no formato humano)
Não é um CSV tidy — as primeiras ~10 linhas são título/metadados. Linhas
representam "CONTAS" (PRODUÇÃO, IMPORTAÇÃO, OFERTA TOTAL, TOTAL TRANSFORMAÇÃO,
CENTRAIS ELÉTRICAS DE SERVIÇO PÚBLICO, etc.) e colunas são fontes primárias
(PETRÓLEO, GÁS NATURAL, CARVÃO, URÂNIO, ENERGIA HIDRÁULICA, LENHA, ...).

Exemplo (aba Consolidada2024): `CENTRAIS ELÉTRICAS DE SERVIÇO PÚBLICO` usou
6.106 × 10³ tep de gás natural em 2024 como insumo.

## Como entra no modelo MILP
- **Fraco acoplamento** com o MILP principal de capacity expansion. Este
  dataset dá uma visão macro, útil para:
  - Dimensionar **ordem de grandeza** da demanda total de eletricidade
    anual (aprox.): oferta interna bruta de "Energia Hidráulica" em tep
    dá ~400 TWh/ano quando combinado com perdas.
  - Calibrar ou *sanity-check* do modelo: a soma de `g_{r,k,t}` precisa
    fechar, em energia anual, com a oferta interna bruta.
  - Construir premissas de autoprodução / cogeração (bagaço, licor negro).
- Não dá granularidade regional nem horária — é nacional e anual.

## Limitações
- Unidade em tep (fator de conversão energético); para eletricidade, converter
  de tep para MWh usando 1 tep = 11,63 MWh.
- Formato planilha humana — ETL exige header/footer skipping e um mapeamento
  manual linhas↔contas.
- Ano 2024 — usar como calibração; o horizonte de expansão do modelo é
  tipicamente 2030-2035.
