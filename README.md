# CSV Insight Bot

Aplicação Streamlit para conversar com dados em CSV. Você faz perguntas em linguagem natural e o agente responde com texto ou gera análises e visualizações automaticamente a partir do arquivo enviado.

- **Stack**: Streamlit, LangGraph, OpenAI, Pandas, Matplotlib/Seaborn
- **Arquitetura**: grafo de estados com nós para carregar CSV, decidir resposta (texto vs. código), executar código com amostragem e formatar a saída
- **Desafio I2A2**: projeto criado para o desafio do curso I2A2. Materiais do desafio no Google Drive: [Pasta do Desafio I2A2](https://drive.google.com/drive/folders/1EYgJrhf3BKHypPQLT5xwTHhsHa2BYMFt)


## Principais recursos

- **Upload de CSV**: leitura via `pandas.read_csv` com limpeza básica de nomes de colunas
- **Chat NL↔︎Dados**: perguntas em linguagem natural sobre o dataset
- **Geração de código**: o LLM decide quando responder com texto ou com código Python para análise/plot
- **Execução segura controlada**: execução do código em ambiente controlado, backend `Agg` e captura de stdout
- **Gráficos automáticos**: histograma, heatmap de correlação, boxplot e variações (conforme pergunta)

## Arquitetura

```
src/
├── cases/         
├── nodes/         
├── prompt/        
└── workflow/      
app.py
requirements.txt
```

### Detalhes dos Módulos

- **cases/**: Implementa diferentes tipos de análise sobre o CSV, como média, boxplot, correlação, variabilidade, etc. Cada arquivo representa um tipo de caso tratado pelo agente.
- **nodes/**: Contém os nós do workflow, responsáveis por tarefas como carregar o CSV, responder perguntas, executar código Python e formatar a saída para o usuário.
- **prompt/**: Define os prompts utilizados para orientar o modelo de linguagem na análise dos dados e na geração das respostas.
- **workflow/**: Monta o grafo de execução que conecta os nós e casos, orquestrando o processamento das perguntas do usuário.

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

## Configuração de modelos

O código usa `gpt-4o-mini` por padrão. Para ajustar, edite `src/nodes/answer_question_node.py` em `answer_question`.


## Licença

Este projeto é distribuído sob a licença MIT. Veja `LICENSE`.

