from openai import OpenAI
from langchain.memory import ConversationBufferMemory

from src.cases.exploratory_case import exploratory_code
from src.cases.histogram_case import histogram_code
from src.cases.boxplot_case import boxplot_code
from src.cases.correlation_case import correlation_code
from src.cases.interval_case import interval_code
from src.cases.average_case import average_code
from src.cases.variability_case import variability_code
from src.cases.default_case import default_code

from src.prompt.analysis_prompt import analysis_system_prompt
from src.prompt.system_prompt import default_system_prompt

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
        "gráfico", "plot", "histograma", "boxplot", "scatter",
        "heatmap", "correlação", "distribuição", "exploratória", 
        "eda", "amostra", "visualizar", "plots", "outliers",
        "intervalo", "mínimo", "máximo", "média", "mediana", "moda",
        "desvio padrão", "variância", "tendência central", "variabilidade"
    ]
    
    force_analysis = any(kw in question.lower() for kw in analysis_keywords)
    if force_analysis:
        matched_keywords = [kw for kw in analysis_keywords if kw in question.lower()]
        print(f"🔍 Palavras-chave encontradas: {matched_keywords}")

    chat_history = memory.chat_memory.messages
    context_messages = []

    if force_analysis:        
        system_prompt = analysis_system_prompt(state)
    else:
        system_prompt = default_system_prompt(state)
    
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
        max_tokens=600 if force_analysis else 1000,
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
                code = exploratory_code

            elif "histograma" in question.lower():
                code = histogram_code

            elif "boxplot" in question.lower() or "outliers" in question.lower():
                code = boxplot_code

            elif "correlação" in question.lower() or "heatmap" in question.lower():
                code = correlation_code
                
            elif "intervalo" in question.lower() or ("mínimo" in question.lower() and "máximo" in question.lower()):
                code = interval_code

            elif "tendência central" in question.lower() or ("média" in question.lower() and "mediana" in question.lower()):
                code = average_code

            elif "variabilidade" in question.lower() or "desvio padrão" in question.lower() or "variância" in question.lower():
                code = variability_code

            else:
                code = default_code
        
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