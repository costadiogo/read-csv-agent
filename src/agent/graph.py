from langgraph.graph import StateGraph, END
from src.agent import nodes

def build_graph():
    graph = StateGraph(dict)
    
    graph.add_node("load_csv", nodes.load_csv)
    graph.add_node("answer_question", nodes.answer_question)
    graph.add_node("execute_code", nodes.execute_code)
    graph.add_node("format_output", nodes.format_output)

    graph.set_entry_point("load_csv")
    graph.add_edge("load_csv", "answer_question")
    graph.add_edge("answer_question", "execute_code")
    graph.add_edge("execute_code", "format_output")
    graph.add_edge("format_output", END)

    return graph.compile()