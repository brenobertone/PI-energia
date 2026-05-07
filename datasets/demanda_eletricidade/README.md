# demanda_eletricidade — EPE / PDE 2035, "Demanda de Eletricidade"

## Conteúdo
- PDF (`Demanda de Eletricidade.pdf`, 2,8 MB) — projeção de consumo e carga
  de eletricidade até 2035, por classe (residencial, comercial, industrial,
  ...), com cenários de referência / inferior / superior.

## Decomposição usada pela EPE (slide 8 do PDF)
A carga total = Consumo potencial – Eficiência elétrica + Sistemas isolados
 + Autoprodução + Perdas. Para o modelo, o que interessa é a **carga global
de energia do SIN**.

## Numeros-âncora (cenário de referência)
- **Residencial 2035**: 91 M unidades × 233 kWh/mês → **254 TWh/ano**
  (crescimento médio 3 %/ano entre 2025 e 2035).
- Cenário inferior: 232 TWh/ano (+2,2 %/ano); superior: 268 TWh/ano (+3,5 %/ano).
- Outros setores (comercial/industrial/rural/público) estão no PDF; cada um
  tem sua taxa de crescimento.

## Como entra no modelo MILP
- Define o **crescimento de demanda** a ser aplicado em cima de
  `val_cargaenergiamwmed` 2025 para construir demanda dos anos-alvo
  (2030, 2035).
  - Exemplo: `D_{r,t}^{2035} = D_{r,t}^{2025} × (1 + g)^{10}` com
    `g` = taxa setor-agnóstica ou específica por classe/subsistema.
- Pode fornecer **3 cenários** (inferior / ref / superior) para uma
  formulação estocástica de dois estágios — primeiro estágio decide `x_{r,k}`,
  segundo estágio decide despacho `g_{r,k,t,s}` para cada cenário `s`.

## Limitações
- PDF, não tabela estruturada — taxas de crescimento e totais por setor
  precisam ser transcritos.
- Não discrimina por subsistema na forma que aparece no PDF (gráficos
  agregados); para um modelo com 4 barras, uma premissa pragmática é aplicar
  o crescimento nacional uniformemente — um desvio sabido de realidade, já
  que NE e N crescem mais rápido.
