# transmissao_energia — EPE / PDE 2035, "Transmissão de Energia"

## Conteúdo
- PDF único (`Transmissão de Energia.pdf`, 6,9 MB). É um **caderno
  qualitativo** com estudos de expansão e não traz uma tabela de
  capacidades e custos por interligação pronta para importação.

## O que é extraível (numérico, para modelagem)
- **Limite atual das interligações regionais** (informação indireta, vem de
  outras publicações do ONS/EPE — aqui aparece como "evolução dos limites").
- **Meta de expansão Nordeste → SE**: 24 GW de capacidade de exportação
  visando suportar até 60 GW instalados de eólica + solar na região N/NE
  até 2033.
- **Meta de importação do Sul**: 17 GW em 2033 e 18 GW em 2035.
- **Alternativa vencedora** para a interligação estratégica: HVDC-VSC
  ±600 kV / 3 GW / 2.500 km ligando SE Angicos (RN) ↔ SE Itaporanga 2
  (SP/PR), custo ~R$ 26,5 bi.
- **Cargas grandes previstas**: 54,2 GW até 2038 (26,3 GW data center +
  27,9 GW hidrogênio), concentradas em SP e NE (CE 18,5 GW, PI 3,6 GW).
- **Investimentos totais**: R$ 25 bi determinativos até 2033, R$ 1,5 bi
  indicativos até 2035.
- **Premissas econômicas de transmissão** (para calcular custo unitário):
  WACC real 8 %, vida útil 30 anos, JDC 20 %/ano × 60 meses.
- Encargos: TFSEE 0,4 %, P&D ANEEL 1,0 %.

## Como entra no modelo MILP
- Para um modelo de **4 subsistemas com arcos** (N, NE, S, SE/CO):
  - `F_{r,r',t}` = fluxo [MW] e `x^T_{r,r'}` = expansão de capacidade de
    transmissão entre `r` e `r'`.
  - Capacidades de arcos existentes `\\bar F_{r,r'}^0`: **não** estão neste
    dataset em formato tabular — vem em figuras e precisa ser assumido a
    partir do texto do PDE ou de outra publicação ONS.
  - Custo de expansão `c^T_{r,r'}`: pode-se usar R$ 26,5 bi / 3 GW / 2.500 km
    ≈ 3,5 M R$/MW para HVDC-VSC longa como proxy, mas isso é apenas um
    número de referência.
- Sem o dataset tabular completo, duas abordagens práticas:
  1. **Calibrar a partir de figuras** do PDE (leitura manual) e criar uma
     tabela `arcos.csv` à mão.
  2. **Modelar sem expansão de transmissão explícita** e apenas impor
     limites de importação/exportação por subsistema (cap simples).

## Limitações
- PDF orientado a apresentação — muitos gráficos, pouca tabela limpa.
- Não diferencia AC vs DC nem granularidade de subestação → abstração de
  nós/arcos tem que ser escolhida pelo modelador.
- Não há dados dinâmicos (reatâncias, DC power flow): se quiser DCOPF, é
  preciso ONS SIN ou dados MELP.
