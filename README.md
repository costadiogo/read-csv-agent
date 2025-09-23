# CSV Insight Bot

Aplicação Streamlit para conversar com dados em CSV. Você faz perguntas em linguagem natural e o agente responde com texto ou gera análises e visualizações automaticamente a partir do arquivo enviado.

- **Stack**: Streamlit, LangGraph, OpenAI, Pandas, Matplotlib/Seaborn
- **Arquitetura**: grafo de estados com nós para carregar CSV, decidir resposta (texto vs. código), executar código com amostragem e formatar a saída
- **Desafio I2A2**: projeto criado para o desafio do curso I2A2. Materiais do desafio no Google Drive: [Pasta do Desafio I2A2](https://drive.google.com/drive/folders/1EYgJrhf3BKHypPQLT5xwTHhsHa2BYMFt)


## Principais recursos

- **Upload de CSV**: leitura via `pandas.read_csv` com limpeza básica de nomes de colunas
- **Chat NL↔︎Dados**: perguntas em linguagem natural sobre o dataset
- **Geração de código**: o LLM decide quando responder com texto ou com código Python para análise/plot
- **Amostragem automática**: `df_small = df.sample(min(1000, len(df)), random_state=42)` para escala e responsividade
- **Execução segura controlada**: execução do código em ambiente controlado, backend `Agg` e captura de stdout
- **Gráficos automáticos**: histograma, heatmap de correlação, boxplot e variações (conforme pergunta)
- **UX**: barra de progresso, mensagens de sistema e cache temporário de imagem

## Arquitetura

```
app.py (UI Streamlit)
  └─ build_graph() -> src/agent/graph.py (LangGraph)
       ├─ load_csv -> src/agent/nodes.py
       ├─ answer_question (LLM decide texto/código)
       ├─ execute_code (exec do código + geração de imagem)
       └─ format_output (extrai resposta final)
```

- `src/agent/graph.py`: define o grafo (`load_csv` → `answer_question` → `execute_code` → `format_output`).
- `src/agent/nodes.py`:
  - `load_csv`: lê CSV, guarda `df` global, publica `schema`/`data_info`.
  - `answer_question`: usa OpenAI (`gpt-4o-mini`) para decidir e/ou gerar código; força análise se detectar termos de visualização.
  - `execute_code`: prepara ambiente seguro (Ajusta `savefig` para `img_path`, backend `Agg`), executa código e captura imagem.
  - `format_output`: extrai `{"answer": ...}` do stdout e define `final_answer`.

## Pré-requisitos

- Python 3.10+
- Chave de API da OpenAI com acesso ao modelo `gpt-4o-mini`

## Instalação

1. Clone o repositório:
   ```sh
   https://github.com/costadiogo/read-csv-agent.git
   cd read-csv-agent
   ```

2. Crie e ative um ambiente virtual:
   ```sh
   python -m venv venv
   
   # Windows
   venv\Scripts\activate

   # Linux/Mac
   source venv/bin/activate
   ```

3. Instale as dependências:
   ```sh
   pip install -r requirements.txt
   ```
## Execução

```bash
streamlit run app.py
```

No app:
- Preencha a OpenAI API Key na barra lateral
- Faça upload do CSV
- Envie perguntas pelo campo de chat

## Estrutura do projeto

```
read-csv-agent/
  app.py                 # UI Streamlit e orquestração
  requirements.txt       # dependências
  src/agent/graph.py     # definição do LangGraph
  src/agent/nodes.py     # nós: load_csv, answer_question, execute_code, format_output
```

## Configuração de modelos

O código usa `gpt-4o-mini` por padrão. Para ajustar, edite `src/agent/nodes.py` em `answer_question`.


## Licença

Este projeto é distribuído sob a licença MIT. Veja `LICENSE`.

