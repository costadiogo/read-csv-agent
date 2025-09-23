import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import tempfile, io, os, json, contextlib, time, re
import streamlit as st
from openai import OpenAI

df_global = None

# ===========================
# Load CSV
# ===========================
def load_csv(state):
    file = state["file"]
    global df_global

    df_global = pd.read_csv(file)
    df_global.columns = df_global.columns.str.strip()

    schema_lite = {col: str(dtype) for col, dtype in list(df_global.dtypes.items())[:10]}

    state["schema"] = schema_lite
    state["data_info"] = {
        "shape": df_global.shape,
        "columns": list(df_global.columns)
    }
    return state

# ===========================
# Answer Question (LLM único)
# ===========================
def answer_question(state):
    api_key = state["api_key"]
    question = state["question"]
    schema = state["schema"]

    client = OpenAI(api_key=api_key)

    # Heurística para análise
    analysis_keywords = [
        "gráfico", "plot", "histograma", "boxplot", "scatter",
        "heatmap", "curva", "linha", "barras", "visualização",
        "correlação", "distribuição"
    ]
    force_analysis = any(kw in question.lower() for kw in analysis_keywords)

    prompt = f"""
    Você é um assistente de análise de dados.

    REGRAS:
    1. Se a pergunta pede EXPLICAÇÃO GERAL:
       - Responda apenas com TEXTO.
    2. Se a pergunta pede ANÁLISE ou VISUALIZAÇÃO:
       - Responda apenas com CÓDIGO PYTHON válido.
       - Use df_small = df.sample(min(1000, len(df)), random_state=42)
       - OBRIGATÓRIO: Termine SEMPRE com:
         plt.savefig(img_path, dpi=150, bbox_inches='tight')
         plt.close()
         print({{"answer": "explicação da análise"}})

    EXEMPLO DE CÓDIGO:
    df_small = df.sample(min(1000, len(df)), random_state=42)
    plt.figure(figsize=(8, 6))
    # análise aqui
    plt.savefig(img_path, dpi=150, bbox_inches='tight')
    plt.close()
    print({{"answer": "Descrição do gráfico"}})

    Pergunta: {question}
    Colunas: {list(schema.keys())}
    """

    t0 = time.time()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": prompt}],
        max_tokens=500,
        temperature=0
    )
    llm_time = time.time() - t0
    print(f"⏱️ LLM respondeu em {llm_time:.2f}s")

    raw_output = response.choices[0].message.content.strip()
    print(f"📝 RESPOSTA LLM:\n{raw_output}\n" + "="*50)

    is_code = False
    if raw_output.startswith("```") or "plt." in raw_output or "df_small" in raw_output:
        is_code = True
        
        if "```" in raw_output:
            parts = raw_output.split("```")
            code_block = parts[1] if len(parts) > 1 else raw_output
            if code_block.startswith("python"):
                code_block = code_block[6:].strip()
            code = code_block
        else:
            code = raw_output.strip()
            
    if force_analysis and not is_code:
        print("⚠️ Forçando geração de código para análise...")
        
        # Determinar tipo de gráfico
        if "histograma" in question.lower():
            code = """
                df_small = df.sample(min(1000, len(df)), random_state=42)
                numeric_cols = df_small.select_dtypes(include=['number']).columns[:4]
                plt.figure(figsize=(10, 6))
                for i, col in enumerate(numeric_cols):
                    plt.subplot(2, 2, i+1)
                    plt.hist(df_small[col].dropna(), bins=20, alpha=0.7)
                    plt.title(f'Distribuição de {col}')
                plt.tight_layout()
                plt.savefig(img_path, dpi=150, bbox_inches='tight')
                plt.close()
                print('{"answer": "Histogramas das principais variáveis numéricas"}')
            """
        elif "correlação" in question.lower() or "heatmap" in question.lower():
            code = """
                df_small = df.sample(min(1000, len(df)), random_state=42)
                numeric_df = df_small.select_dtypes(include=['number'])
                plt.figure(figsize=(8, 6))
                correlation_matrix = numeric_df.corr()
                sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0)
                plt.title('Matriz de Correlação')
                plt.tight_layout()
                plt.savefig(img_path, dpi=150, bbox_inches='tight')
                plt.close()
                print('{"answer": "Matriz de correlação entre variáveis numéricas"}')
            """
        else:
            code = """
                df_small = df.sample(min(500, len(df)), random_state=42)
                numeric_cols = df_small.select_dtypes(include=['number']).columns[:3]
                plt.figure(figsize=(8, 6))
                for i, col in enumerate(numeric_cols):
                    plt.subplot(2, 2, i+1)
                    plt.hist(df_small[col].dropna(), bins=15)
                    plt.title(col)
                plt.tight_layout()
                plt.savefig(img_path, dpi=150, bbox_inches='tight')
                plt.close()
                print('{"answer": "Análise visual das principais variáveis"}')
            """
        is_code = True

    if is_code:
        state["code"] = code
        state["mode"] = "code"
    else:
        state["final_answer"] = raw_output
        state["mode"] = "text"

    return state

# ==========================
# Execute Code
# ==========================
def execute_code(state):
    if state.get("mode") == "text":
        return state

    global df_global
    code = state["code"]

    tmpdir = st.session_state.get("temp_dir")
    img_path = os.path.join(tmpdir, "plot.png")
    lines = code.split("\n")
    cleaned_lines = []
    for line in lines:
        if "savefig(" in line:
            line = re.sub(r"'[^']*\.png'", "img_path", line)
            line = re.sub(r'"[^"]*\.png"', "img_path", line)
        cleaned_lines.append(line)
    code = "\n".join(cleaned_lines)

    local_env = {
        "df": df_global,
        "df_small": df_global.sample(min(1000, len(df_global)), random_state=42),
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
            state["final_answer"] = f"Erro ao executar código: {error_msg}"
            state["code_error"] = True
            return state

    state["raw_output"] = stdout.getvalue()
    state["code_error"] = False

    if os.path.exists(img_path):
        with open(img_path, "rb") as f:
            state["image_bytes"] = f.read()
    else:
        state["image_bytes"] = None

    return state

# ===========================
# Format Output
# ===========================
def format_output(state):
    if state.get("mode") == "text":
        if "final_answer" in state:
            answer = state["final_answer"]
            if answer.startswith('{"answer":') and answer.endswith('}'):
                try:
                    json_data = json.loads(answer)
                    state["final_answer"] = json_data["answer"]
                except:
                    pass
        return state

    if state.get("code_error"):
        return state

    raw_output = state.get("raw_output", "")
    
    try:
        lines = [line.strip() for line in raw_output.splitlines() if line.strip()]
        parsed = None
        
        for line in reversed(lines):
            try:
                parsed = json.loads(line)
                if "answer" in parsed:
                    break
            except json.JSONDecodeError:
                if line.startswith("{'answer':") and line.endswith("}"):
                    try:
                        json_str = line.replace("'", '"')
                        parsed = json.loads(json_str)
                        if "answer" in parsed:
                            break
                    except:
                        continue
                continue
        
        if parsed and "answer" in parsed:
            state["final_answer"] = parsed["answer"]
        else:
            print("⚠️ Nenhum JSON válido encontrado, usando fallback")
            state["final_answer"] = "Análise concluída com sucesso."
            
    except Exception as e:
        print(f"❌ Erro no format_output: {e}")
        state["final_answer"] = "Análise concluída. Gráfico gerado com sucesso."

    return state
