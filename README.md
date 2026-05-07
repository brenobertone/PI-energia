# PI Energia

Painel de exploração de dados do Sistema Interligado Nacional (SIN).

Conteúdo

- datasets/: coleções de dados usados pelo projeto
  - SIGET - Contrato Módulo Equipamento Subestacao
  - SIGET - Contrato Módulo Geral Subestação Tipo Arranjo
  - SIGET - Contrato Módulo Linha Transmissão
  - balanco_energetico_nacional
  - carga_energia
  - consolidacao_resultados
  - demanda_eletricidade
  - fator_capacidade_eolica_solar
  - parametros_custo_geracao
  - siga
  - subestacao_rede_operacoes
  - transmissao_energia

Executando a visualização

Este projeto usa Streamlit. Para rodar a aplicação localmente (recomendado usar o Poetry para gerenciar dependências):

1. Instale o Poetry se necessário: https://python-poetry.org/
2. Instale as dependências:

   poetry install

3. Execute o dashboard Streamlit:

   poetry run python -m streamlit run src/pi_energia/viz/app.py

Observações

- O arquivo de banco de dados grande está em data/pi.db e já está listado em .gitignore para não ser versionado.
- O painel abre no navegador (por padrão http://localhost:8501). Se quiser mudar porta/host, use as opções do Streamlit.

Licença

(Adicionar licença se desejar)
