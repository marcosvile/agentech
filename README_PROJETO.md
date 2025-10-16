# Documentação do Projeto

Este repositório automatiza a captura do banco de dados público do Agenda Tech Brasil e a geração de um README com os eventos do ano corrente.

## Componentes principais

- `src/scripts/scraping.py`: baixa o arquivo `database.json` diretamente do repositório oficial do Agenda Tech Brasil e salva em `src/db/database.json`. O script valida o JSON antes de gravar para evitar corromper a base local.
- `src/scripts/build_readme.py`: processa o banco de dados, filtra apenas os eventos do ano atual e atualiza o `README.md`, substituindo os rótulos de modalidade por emojis (`🏢` presencial, `🔀` híbrido, `💻` online, `❓` modalidade indefinida).
- `.github/workflows/main.yml`: workflow semanal que executa os dois scripts acima e realiza o commit automático das atualizações.

## Como executar manualmente

1. Baixe o banco de dados:

   ```bash
   python3 src/scripts/scraping.py
   ```

2. Recrie o README a partir do banco baixado:

   ```bash
   python3 src/scripts/build_readme.py
   ```

Ambos os scripts aceitam argumentos opcionais. Consulte `--help` para verificar parâmetros como `--url`, `--output`, `--db-path` e `--year`.

## Convenções adotadas

- Apenas eventos do ano corrente são exibidos no `README.md`.
- Cada mês contém marcadores HTML (`<!-- NOME_DO_MES:START -->` e `<!-- NOME_DO_MES:END -->`) para facilitar automatizações futuras.
- Os emojis substituem as etiquetas originais:
  - `🏢` presencial
  - `🔀` híbrido
  - `💻` online
  - `❓` quando a modalidade não é informada

## Fluxo automático

O GitHub Actions executa semanalmente as seguintes etapas:

1. Faz checkout do repositório.
2. Configura o Python 3.11.
3. Atualiza `src/db/database.json` via `scraping.py`.
4. Gera o `README.md` com `build_readme.py`.
5. Comita as mudanças geradas automaticamente.

Para disparar uma atualização imediata basta usar a ação manual (`workflow_dispatch`) disponível na aba *Actions* do GitHub.
