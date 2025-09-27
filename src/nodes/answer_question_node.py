from openai import OpenAI
from langchain.memory import ConversationBufferMemory

from src.prompt.system_prompt import default_system_prompt
from src.prompt.react_prompt import react_analysis_prompt

# ===========================
# Answer Question
# ===========================
def answer_question(state):
    api_key = state["api_key"]
    question = state["question"]
    
    memory = state.get("memory")
    if not memory:
        print("⚠️ Memória não encontrada no state")
        memory = ConversationBufferMemory(return_messages=True)
    
    client = OpenAI(api_key=api_key)
    memory.chat_memory.add_user_message(question)

    analysis_keywords = [
        "gráfico", "plot", "histograma", "boxplot", "scatter", "correlação", 
        "distribuição", "exploratória", "eda", "análise", "estatística",
        "intervalo", "mínimo", "máximo", "média", "mediana", "moda",
        "desvio padrão", "variância", "variabilidade", "outliers",
        "tendência central", "amplitude", "calcul", "mostre", "crie",
        "padrões", "tendências"
    ]
    
    needs_analysis = any(kw in question.lower() for kw in analysis_keywords)
    
    print(f"🤖 Pergunta: '{question}'")
    print(f"🧠 Requer análise: {needs_analysis}")

    context_messages = []
    
    if needs_analysis:
        system_prompt = react_analysis_prompt(state)
        max_tokens = 800
    else:
        system_prompt = default_system_prompt(state)
        max_tokens = 600
    
    context_messages.append({"role": "system", "content": system_prompt})

    chat_history = memory.chat_memory.messages
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
        max_tokens=max_tokens,
        temperature=0.1
    )

    raw_output = response.choices[0].message.content.strip()
    memory.chat_memory.add_ai_message(raw_output)

    if len(memory.chat_memory.messages) > 16:
        memory.chat_memory.messages = memory.chat_memory.messages[-16:]

    print(f"📝 RESPOSTA ReAct:\n{raw_output}\n" + "="*50)

    if needs_analysis:
        code = extract_react_code(raw_output)
        
        if code:
            state["code"] = code
            state["mode"] = "code"
            state["react_response"] = raw_output
        else:
            print("⚠️ Não foi possível extrair código ReAct, usando resposta como texto")
            state["final_answer"] = raw_output
            state["mode"] = "text"
    else:
        clean_text = clean_text_response(raw_output)
        state["final_answer"] = clean_text
        state["mode"] = "text"
    
    state["memory"] = memory
    return state

def extract_react_code(raw_output: str) -> str | None:
    """
    Extrai o bloco único de código Python de uma resposta ReAct.
    Se não encontrar, retorna None.
    """
    try:
        code = None

        if "```python" in raw_output:
            code = raw_output.split("```python")[1].split("```")[0].strip()
        elif "```" in raw_output:
            code = raw_output.split("```")[1].split("```")[0].strip()

        if not code:
            lines = []
            for line in raw_output.splitlines():
                if line.strip().startswith(("import", "plt.", "df", "sns", "print", "numeric_cols", "fig,", "axes")):
                    lines.append(line)
            code = "\n".join(lines).strip() if lines else None

        return code if code else None

    except Exception as e:
        print(f"❌ Erro ao extrair código: {e}")
        return None

def clean_text_response(raw_output):
    """Limpa resposta textual removendo possível código"""
    lines = []
    for line in raw_output.split('\n'):
        if any(marker in line for marker in ['```', 'import ', 'plt.', 'df.', 'print(']):
            break
        if line.strip():
            lines.append(line)
    
    return "\n\n".join(lines) if lines else raw_output