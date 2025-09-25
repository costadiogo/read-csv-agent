import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import io, os, json, contextlib, time, re
from io import StringIO
import streamlit as st
from openai import OpenAI
from langchain.memory import ConversationBufferMemory

# ===========================
# Load CSV
# ===========================
def load_csv(state):
    file_bytes = state.pop("file_content")
    file_like_object = io.BytesIO(file_bytes)
    
    df = pd.read_csv(file_like_object)
    df.columns = df.columns.str.strip()
    
    schema_lite = {col: str(dtype) for col, dtype in df.dtypes.items()}
    state["dataframe_csv"] = df.to_csv(index=False)
    
    state["schema"] = schema_lite
    state["data_info"] = {
        "shape": df.shape,
        "columns": list(df.columns),
        "total_rows": df.shape[0],
        "total_columns": df.shape[1]
    }
        
    return state

# ===========================
# Answer Question
# ===========================
def answer_question(state):
    api_key = state["api_key"]
    question = state["question"]
    schema = state["schema"]
    
    memory = state.get("memory")
    if not memory:
        print("⚠️ Memória não encontrada no state")
        memory = ConversationBufferMemory(return_messages=True)
    
    client = OpenAI(api_key=api_key)

    memory.chat_memory.add_user_message(question)

    analysis_keywords = [
        "gráfico", "plot", "histograma", "boxplot", "scatter",
        "heatmap", "curva", "linha", "barras", "visualização",
        "correlação", "distribuição", "crie", "mostre", "gere",
        "exploratória", "eda", "padrões", "amostra",
        "visualizar", "gráficos", "plots", "dados", "explorar", "padrão",
        "outliers", "boxplots"
    ]
    force_analysis = any(kw in question.lower() for kw in analysis_keywords)
    if force_analysis:
        matched_keywords = [kw for kw in analysis_keywords if kw in question.lower()]
        print(f"🔍 Palavras-chave encontradas: {matched_keywords}")

    chat_history = memory.chat_memory.messages
    context_messages = []

    if force_analysis:
        data_info = state.get('data_info', {})
        dataset_shape = data_info.get('shape', 'N/A')
        total_rows = data_info.get('total_rows', 'N/A')
        total_columns = data_info.get('total_columns', 'N/A')
        
        system_prompt = f"""
            Você é um assistente que gera código Python para análise de dados.

            Dataset: {dataset_shape} linhas/colunas
            Análise: TODOS os dados disponíveis para máxima precisão
            Colunas disponíveis: {list(schema.keys())}

            RESPONDA APENAS COM CÓDIGO PYTHON COMPLETO:
            - O DataFrame df contém TODOS os dados do arquivo ({total_rows:,} linhas)
            - NÃO use df.sample() - analise o dataset completo
            - ANALISE TODAS AS COLUNAS NUMÉRICAS disponíveis
            - Use df.select_dtypes(include=['number']).columns para pegar todas as colunas numéricas
            
            REGRAS IMPORTANTES PARA SUBPLOTS:
            - NUNCA use grids fixos como (3,3), (2,2), (4,4)
            - SEMPRE calcule dinamicamente: n_cols = len(numeric_cols)
            - SEMPRE calcule: n_rows = (n_cols + 3) // 4  # 4 colunas por linha
            - SEMPRE use: plt.subplot(n_rows, 4, i+1)
            - SEMPRE ajuste o tamanho: plt.figure(figsize=(16, 4*n_rows))
            
            EXEMPLO CORRETO:
            numeric_cols = df.select_dtypes(include=['number']).columns
            n_cols = len(numeric_cols)
            n_rows = (n_cols + 3) // 4
            plt.figure(figsize=(16, 4*n_rows))
            for i, col in enumerate(numeric_cols):
                plt.subplot(n_rows, 4, i+1)
                # seu código de visualização aqui
            
            - Para datasets grandes, considere usar bins adequados nos histogramas (50+ bins)
            - Termine SEMPRE com:
            plt.savefig(img_path, dpi=150, bbox_inches='tight')
            plt.close()
            print({{"answer": "descrição breve (mencione que é baseado em todos os {total_rows:,} registros e todas as colunas numéricas)"}})

            NÃO inclua explicações, apenas código funcional.
        """
    else:
        data_info = state.get('data_info', {})
        dataset_shape = data_info.get('shape', 'N/A')
        total_rows = data_info.get('total_rows', 'N/A')
        total_columns = data_info.get('total_columns', 'N/A')
        
        system_prompt = f"""
            Você é um assistente de análise de dados.

            Dataset: {dataset_shape} linhas/colunas
            Análise: TODOS os dados disponíveis para máxima precisão
            Colunas disponíveis: {list(schema.keys())}
            
            REGRA IMPORTANTE:
            - NÃO use pd.read_csv nem recarregue o dataset.
            - O DataFrame já está disponível na variável df.
            - Considere TODAS as colunas disponíveis, não apenas as primeiras.
            
            REGRAS DE FORMATAÇÃO:
            - Use Markdown para formatar a resposta
            - Use **negrito** para destacar conceitos importantes
            - Use numeração (1., 2., 3.) para listas organizadas
            - Use bullets (- ou •) para sub-itens
            - Use `código` para nomes de variáveis
            - Seja conciso e bem estruturado

            EXEMPLO DE FORMATO:
            ## Análise Descritiva

            O dataset contém **{total_rows:,} registros** com as seguintes características:

            ### 1. Variáveis Principais
            - **Variável X**: Descrição da variável
            - **Variável Y**: Descrição da variável

            ### 2. Distribuições
            - A maioria das variáveis apresenta...

        
            RESPONDA COM TEXTO EXPLICATIVO E MARKDOWN formatado.
            Seja conciso e direto, sem incluir código Python.
            Mencione que a análise é baseada em todos os {total_rows:,} registros do dataset.
        """
    
    context_messages.append({"role": "system", "content": system_prompt})

    recent_messages = chat_history[-4:] if len(chat_history) > 4 else chat_history
    
    for msg in recent_messages:
        if hasattr(msg, 'type'):
            role = "user" if msg.type == "human" else "assistant"
            context_messages.append({
                "role": role, 
                "content": msg.content[:300]
            })

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=context_messages,
        max_tokens=300 if force_analysis else 1000,
        temperature=0.1
    )

    raw_output = response.choices[0].message.content.strip()

    memory.chat_memory.add_ai_message(raw_output)

    if len(memory.chat_memory.messages) > 16:
        memory.chat_memory.messages = memory.chat_memory.messages[-16:]
    
    print(f"📝 RESPOSTA LLM:\n{raw_output}\n" + "="*50)

    if force_analysis:
        if "```" in raw_output:
            parts = raw_output.split("```")
            code_block = parts[1] if len(parts) > 1 else raw_output
            if code_block.startswith("python"):
                code_block = code_block[6:].strip()
            code = code_block
        else:
            code = raw_output.strip()

        has_fixed_grid = any(pattern in code for pattern in [
            "plt.subplot(3, 3,", "plt.subplot(2, 2,", "plt.subplot(4, 4,",
            "plt.subplot(2, 3,", "plt.subplot(3, 2,", "plt.subplot(5, 5,",
            "subplot(3, 3,", "subplot(2, 2,", "subplot(4, 4,",
            "subplot(2, 3,", "subplot(3, 2,", "subplot(5, 5,"
        ])
        
        if not ("plt.savefig" in code and "print(" in code) or has_fixed_grid:
            if has_fixed_grid:
                print("⚠️ Código com grid fixo detectado, usando template...")
            else:
                print("⚠️ Código incompleto, usando template...")

            if "exploratória" in question.lower() or "eda" in question.lower():
                total_rows = state.get('data_info', {}).get('total_rows', 'N/A')
                code = f'''
                    print("=== ANÁLISE EXPLORATÓRIA ===")
                    print(f"Dimensões do dataset: {{df.shape}}")
                    numeric_cols = df.select_dtypes(include=['number']).columns
                    n_cols = len(numeric_cols)
                    print(f"\\nColunas numéricas analisadas: {{n_cols}}")
                    print("\\nEstatísticas descritivas:")
                    print(df[numeric_cols].describe())
                    print("\\nValores ausentes:")
                    print(df.isnull().sum())

                    n_rows = (n_cols + 3) // 4
                    plt.figure(figsize=(16, 4*n_rows))

                    for i, col in enumerate(numeric_cols):
                        plt.subplot(n_rows, 4, i+1)
                        plt.hist(df[col].dropna(), bins=50, alpha=0.7)
                        plt.title(f'{{col}}', fontsize=10)
                        plt.xticks(rotation=45)
                    plt.tight_layout()
                    plt.savefig(img_path, dpi=150, bbox_inches='tight')
                    plt.close()
                '''

            elif "histograma" in question.lower():
                total_rows = state.get('data_info', {}).get('total_rows', 'N/A')
                code = f'''
                    numeric_cols = df.select_dtypes(include=['number']).columns
                    n_cols = len(numeric_cols)
                    n_rows = (n_cols + 3) // 4
                    plt.figure(figsize=(16, 4*n_rows))

                    for i, col in enumerate(numeric_cols):
                        plt.subplot(n_rows, 4, i+1)
                        plt.hist(df[col].dropna(), bins=50, alpha=0.7)
                        plt.title(f'{{col}}', fontsize=10)
                        plt.xticks(rotation=45)
                    plt.tight_layout()
                    plt.savefig(img_path, dpi=150, bbox_inches='tight')
                    plt.close()
                '''

            elif "boxplot" in question.lower() or "outliers" in question.lower():
                total_rows = state.get('data_info', {}).get('total_rows', 'N/A')
                code = f'''
                    numeric_cols = df.select_dtypes(include=['number']).columns
                    n_cols = len(numeric_cols)
                    n_rows = (n_cols + 3) // 4
                    plt.figure(figsize=(16, 4*n_rows))

                    for i, col in enumerate(numeric_cols):
                        plt.subplot(n_rows, 4, i+1)
                        sns.boxplot(x=df[col])
                        plt.title(f'{{col}}', fontsize=10)
                        plt.xticks(rotation=45)
                    plt.tight_layout()
                    plt.savefig(img_path, dpi=150, bbox_inches='tight')
                    plt.close()
                '''

            elif "correlação" in question.lower() or "heatmap" in question.lower():
                total_rows = state.get('data_info', {}).get('total_rows', 'N/A')
                code = f'''
                    numeric_df = df.select_dtypes(include=['number'])
                    plt.figure(figsize=(12, 10))
                    correlation_matrix = numeric_df.corr()
                    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0, fmt='.2f')
                    plt.title('Matriz de Correlação - Dataset Completo')
                    plt.tight_layout()
                    plt.savefig(img_path, dpi=150, bbox_inches='tight')
                    plt.close()
                '''

            else:
                total_rows = state.get('data_info', {}).get('total_rows', 'N/A')
                code = f'''
                    numeric_cols = df.select_dtypes(include=['number']).columns
                    n_cols = len(numeric_cols)
                    n_rows = (n_cols + 3) // 4
                    plt.figure(figsize=(16, 4*n_rows))

                    for i, col in enumerate(numeric_cols):
                        plt.subplot(n_rows, 4, i+1)
                        plt.hist(df[col].dropna(), bins=50, alpha=0.7)
                        plt.title(f'{{col}}', fontsize=10)
                        plt.xticks(rotation=45)
                    plt.tight_layout()
                    plt.savefig(img_path, dpi=150, bbox_inches='tight')
                    plt.close()
                '''
        
        state["code"] = code
        state["mode"] = "code"
        
    else:
        lines = []
        for line in raw_output.split('\n'):
            if any(marker in line for marker in ['```', 'import ', 'plt.', 'df.', 'print(']):
                break
            if line.strip():
                lines.append(line)

        clean_text = "\n\n".join(lines) if lines else raw_output
        state["final_answer"] = clean_text
        state["mode"] = "text"
        
    state["memory"] = memory
    return state

# ==========================
# Execute Code
# ==========================
def execute_code(state):
    if state.get("mode") == "text":
        return state

    if "cached_dataframe" not in state:
        csv_string = state["dataframe_csv"]
        state["cached_dataframe"] = pd.read_csv(StringIO(csv_string))
    
    df = state["cached_dataframe"]

    tmpdir = st.session_state.get("temp_dir")
    if not os.path.exists(tmpdir):
        os.makedirs(tmpdir, exist_ok=True)

    img_path = os.path.join(tmpdir, "plot.png")

    code = state["code"]
    lines = code.split("\n")
    cleaned_lines = []
    for line in lines:
        if "pd.read_csv" in line or "read_csv" in line:
            continue
        if "img_path" in line and "=" in line and not "savefig" in line:
            continue
        if "savefig(" in line:
            line = re.sub(r"'[^']*\.png'", "img_path", line)
            line = re.sub(r'"[^"]*\.png"', "img_path", line)
        cleaned_lines.append(line)
    code = "\n".join(cleaned_lines)

    local_env = {
        "df": df,
        "plt": plt,
        "pd": pd,
        "np": np,
        "sns": sns,
        "img_path": img_path
    }

    plt.switch_backend("Agg")
    plt.ioff()

    stdout, stderr = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        try:
            exec(code, local_env)
            plt.close("all")
        except Exception as e:
            error_msg = stderr.getvalue() or str(e)
            print(f"❌ Erro na execução: {error_msg}")
            state["final_answer"] = f"Erro ao executar código: {error_msg}"
            state["code_error"] = True
            return state

    state["raw_output"] = stdout.getvalue()
    state["code_error"] = False

    print(f"📁 Arquivo existe: {os.path.exists(img_path)}")
    if os.path.exists(img_path):
        with open(img_path, "rb") as f:
            state["image_bytes"] = f.read()
        print(f"✅ Imagem carregada com sucesso")
    else:
        print("⚠️ Nenhum gráfico gerado - arquivo não encontrado")
        if os.path.exists(tmpdir):
            files = os.listdir(tmpdir)
            print(f"📁 Arquivos no diretório temporário: {files}")
        state["image_bytes"] = None

    return state

# ===========================
# Format Output
# ===========================
def format_output(state):
    if state.get("mode") == "text":
        return state

    if state.get("code_error"):
        return state

    raw_output = state.get("raw_output", "")

    try:
        json_pattern = r'print\s*\(\s*[\'"](\{[^}]+\})[\'"]'
        match = re.search(json_pattern, raw_output)
        
        if match:
            json_str = match.group(1)
            parsed = json.loads(json_str)
            if "answer" in parsed:
                state["final_answer"] = parsed["answer"]
                return state
        
        python_dict_pattern = r"print\s*\(\s*\{['\"]answer['\"]\s*:\s*['\"]([^'\"]+)['\"]\s*\}\s*\)"
        dict_match = re.search(python_dict_pattern, raw_output)
        
        if dict_match:
            answer_text = dict_match.group(1)
            state["final_answer"] = answer_text
            print(f"Answer extraído: {answer_text}")
            return state
        
        lines = [line.strip() for line in raw_output.splitlines() if line.strip()]
        for line in reversed(lines):
            try:
                parsed = json.loads(line)
                if "answer" in parsed:
                    state["final_answer"] = parsed["answer"]
                    return state
            except:
                if line.startswith("{'answer':") and line.endswith("}"):
                    try:
                        json_str = line.replace("'", '"')
                        parsed = json.loads(json_str)
                        if "answer" in parsed:
                            state["final_answer"] = parsed["answer"]
                            return state
                    except:
                        continue
                    
        for line in reversed(lines):
            if line.startswith("{'answer':") and line.endswith("}"):
                try:
                    result = eval(line)
                    if isinstance(result, dict) and "answer" in result:
                        state["final_answer"] = result["answer"]
                        return state
                except:
                    continue
                
        state["final_answer"] = raw_output.strip()

    except Exception as e:
        print(f"Erro no format_output: {e}")
        state["final_answer"] = raw_output.strip()

    return state