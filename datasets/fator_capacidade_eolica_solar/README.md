# fator_capacidade_eolica_solar — ONS, Fator de Capacidade horário (eólica/solar)

## Conteúdo
- `FATOR_CAPACIDADE-2_2025_MM.parquet` — 12 arquivos mensais, passo **horário**
  (agregando → 8760 timestamps de 2025).
- `DicionarioDados_FatorCapacidade.pdf` — dicionário.

## Estrutura
Cada linha = (usina/conjunto, hora). Colunas relevantes:

| coluna | uso |
|---|---|
| `nom_subsistema` | N, NE, S, SE/CO |
| `nom_estado`, `id_estado` | UF |
| `nom_usina_conjunto` | identificador |
| `val_latitudesecoletora` / `val_longitudesecoletora` | coord. da SE coletora |
| `nom_modalidadeoperacao` | tipicamente "Conjunto de Usinas" |
| `nom_tipousina` | Eólica ou Solar |
| `din_instante` | hora (UTC? sem fuso explícito) |
| `val_capacidadeinstalada` | MW |
| `val_geracaoverificada` | MWh na hora |
| `val_fatorcapacidade` | gen/cap na hora (valor primário do dataset) |

Numéricos vêm como strings de alta precisão → `pd.to_numeric` necessário.

## Cobertura
- 1.943.736 linhas, 262 conjuntos/usinas, 8760 horas.
- Tecnologia × subsistema (n linhas, proxy de n usinas ativas):

| tech \\ sub | NE | S | N | SE/CO |
|---|---:|---:|---:|---:|
| Eólica | ~1,36M | 114k | 8,7k | — |
| Solar  | 268k  | —   | —   | 194k |

## Fatores de capacidade (ponderados por capacidade, média 2025)
| tech \\ sub | Nordeste | Norte | SE/CO | Sul |
|---|---:|---:|---:|---:|
| Eólica | 0,385 | 0,498 | — | 0,302 |
| Solar  | 0,206 | — | 0,203 | — |

Perfil diário **eólica NE** (ponderado): forte anticorrelação com solar — pico
noturno (~0,51 às 23h) e vale às 12h (~0,18). Isto é materialmente importante
para a modelagem de despacho intradiário.

## Como entra no modelo MILP
- Dá diretamente `α_{r,k,t}` para as tecnologias **eólica e solar**, com
  granularidade horária e variação espacial por subsistema.
- Duas formas de usá-lo:
  1. **Agregado**: perfis `α_{r,k,t}` ponderados por capacidade em cada
     subsistema → 4 × 2 séries horárias. Simples, bem condicionado.
  2. **Clusterizado**: agrupar usinas por similaridade de perfil dentro do
     subsistema (k-means em correlações) para obter `α_{r,k,c,t}` em clusters
     → útil se quiser capturar heterogeneidade intra-regional, mas aumenta o
     tamanho do MILP.

## Limitações / armadilhas
- **Capacidade só das usinas operando em 2025** → o `α_{r,k,t}` é proxy da
  disponibilidade do *recurso* atual, mas é enviesado pela localização atual
  das usinas. Para expansão, um perfil baseado em sites *futuros* (ERA5,
  Global Wind Atlas, NSRDB) seria mais correto — aqui assumimos sites
  representativos.
- Sem expansões regionais ainda não construídas: **Norte-solar** e
  **SE/CO-eólica** não aparecem (sem dado empírico = proxy de outra região).
- Timezone não documentada nas colunas — tratar como "hora local" do ONS
  (UTC-3) é a convenção mais provável.
- FC calculado = `gen_verificada / capacidade_instalada` depende da
  disponibilidade *operativa* (paradas, curtailment). Para expansão
  "green-field", isto subestima o recurso disponível.
