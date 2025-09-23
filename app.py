import streamlit as st
import pandas as pd
import time
import io
import os
import tempfile, shutil
from src.agent.graph import build_graph

st.set_page_config(page_title="CSV Agent Chat", page_icon="📊", layout="wide")

# ===========================
# Inicializar session state
# ===========================
if "system_messages" not in st.session_state:
    st.session_state.system_messages = []
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "csv_loaded" not in st.session_state:
    st.session_state.csv_loaded = False
if "csv_info" not in st.session_state:
    st.session_state.csv_info = None
if "temp_dir" not in st.session_state:
    st.session_state.temp_dir = tempfile.mkdtemp()

st.title("📊 CSV Insight Bot")
st.markdown("Converse com seus dados de forma natural!")

# ===========================
# Sidebar para configurações
# ===========================
with st.sidebar:
    st.header("⚙️ Configuração")
    api_key = st.text_input("🔑 OpenAI API Key", type="password")
    uploaded_file = st.file_uploader("📁 Upload CSV", type="csv")

    if uploaded_file and api_key:
        if not st.session_state.csv_loaded or st.session_state.get("current_file") != uploaded_file.name:
            try:
                st.session_state.chat_messages = []

                file_copy = io.BytesIO(uploaded_file.getvalue())
                preview_df = pd.read_csv(file_copy)

                st.session_state.csv_info = {
                    "filename": uploaded_file.name,
                    "rows": len(preview_df),
                    "columns": len(preview_df.columns),
                    "column_names": list(preview_df.columns),
                    "dtypes": preview_df.dtypes.to_dict(),
                }
                st.session_state.csv_loaded = True
                st.session_state.current_file = uploaded_file.name

                welcome_msg = f"""
                📊 **Arquivo carregado com sucesso!**

                **{uploaded_file.name}**
                - 📝 {len(preview_df)} linhas
                - 📊 {len(preview_df.columns)} colunas
                - 🏷️ Colunas: {', '.join(preview_df.columns[:5])}{'...' if len(preview_df.columns) > 5 else ''}

                Pergunte, explore e visualize seus dados de forma simples.! 🚀
                """

                st.session_state.system_messages = [
                    {
                        "role": "assistant",
                        "content": welcome_msg,
                        "timestamp": time.time(),
                    }
                ]

            except Exception as e:
                st.error(f"Erro ao processar arquivo: {e}")
                st.session_state.csv_loaded = False

    st.header("💡 Exemplos")
    example_questions = [
        "📊 Resumo estatístico das principais variáveis",
        "📈 Histograma de uma amostra dos dados",
        "🔥 Correlação entre as principais variáveis numéricas",
        "📦 Boxplot para detectar outliers (amostra)",
        "🔍 Análise descritiva básica",
        "📉 Padrões em uma amostra aleatória",
        "🎯 Insights principais do dataset",
    ]

    for question in example_questions:
        if st.button(question, key=f"example_{question}", use_container_width=True):
            if st.session_state.csv_loaded and api_key:
                st.session_state.pending_question = question.split(" ", 1)[1]
            else:
                st.warning("⚠️ Configure API Key e carregue um CSV primeiro")

    if st.button("🗑️ Limpar Conversa", use_container_width=True):
        st.session_state.chat_messages = []
        if "temp_dir" in st.session_state and os.path.exists(st.session_state.temp_dir):
            shutil.rmtree(st.session_state.temp_dir, ignore_errors=True)
            st.session_state.temp_dir = tempfile.mkdtemp()

# ===========================
# Área principal do chat
# ===========================
st.header("🤖 Seu assistente de dados")
st.caption("Faça perguntas, gere análises e visualize seus dados em tempo real.")

messages_container = st.container()

with messages_container:
    for message in st.session_state.system_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

            if message.get("image"):
                st.image(message["image"], caption="Visualização gerada", use_container_width=True)
            if message.get("processing_time"):
                st.caption(f"⏱️ Processado em {message['processing_time']:.1f}s")

# ===========================
# Input do usuário
# ===========================
if st.session_state.csv_loaded and api_key:
    if hasattr(st.session_state, "pending_question"):
        user_input = st.session_state.pending_question
        del st.session_state.pending_question
        process_question = True
    else:
        user_input = st.chat_input("Digite sua pergunta sobre o CSV...")
        process_question = bool(user_input)

    if process_question and user_input:
        st.session_state.chat_messages.append(
            {"role": "user", "content": user_input, "timestamp": time.time()}
        )

        start_time = time.time()
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            status_text.text("🔄 Carregando dados...")
            progress_bar.progress(20)

            graph = build_graph()

            status_text.text("🧠 Analisando pergunta...")
            progress_bar.progress(40)

            status_text.text("⚡ Processando dados...")
            progress_bar.progress(60)

            result = graph.invoke(
                {"file": uploaded_file, "question": user_input, "api_key": api_key}
            )

            status_text.text("🎨 Gerando visualização...")
            progress_bar.progress(80)

            progress_bar.progress(100)
            processing_time = time.time() - start_time
            status_text.text(f"✅ Concluído em {processing_time:.1f}s")

            assistant_message = {
                "role": "assistant",
                "content": result.get("final_answer", "Desculpe, não consegui processar sua pergunta."),
                "timestamp": time.time(),
                "processing_time": processing_time,
            }

            if result.get("image_bytes"):
                assistant_message["image"] = result["image_bytes"]

            if result.get("code"):
                assistant_message["code"] = result["code"]

            st.session_state.chat_messages.append(assistant_message)

            progress_bar.empty()
            status_text.empty()

        except Exception as e:
            processing_time = time.time() - start_time
            progress_bar.empty()
            status_text.empty()

            st.session_state.chat_messages.append(
                {
                    "role": "assistant",
                    "content": f"❌ **Erro:** {str(e)}\n\n💡 **Dicas para datasets grandes:**\n- Seja mais específico na pergunta\n- Use palavras como 'amostra' ou 'resumo'\n- Evite gráficos com muitas variáveis",
                    "timestamp": time.time(),
                    "processing_time": processing_time,
                }
            )

        st.rerun()

else:
    if not api_key:
        st.info("🔑 **Configure sua API Key da OpenAI** na barra lateral para começar.")
    elif not st.session_state.csv_loaded:
        st.info("📁 **Faça upload de um arquivo CSV** na barra lateral para começar a conversar.")

# ===========================
# CSS customizado
# ===========================
st.markdown(
    """
<style>
    .stChatMessage {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.5rem;
    }
    .element-container:has(> .stVertical > .stMarkdown) {
        max-height: 60vh;
        overflow-y: auto;
    }
    .stButton > button {
        width: 100%;
        text-align: left;
        font-size: 0.9rem;
    }
</style>
""",
    unsafe_allow_html=True,
)
