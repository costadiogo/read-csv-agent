import os
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st
import io
from io import StringIO
import contextlib 
import re

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
