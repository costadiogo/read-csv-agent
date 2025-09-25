from langgraph.graph import StateGraph, END

from src.nodes.load_csv_node import load_csv
from src.nodes.answer_question_node import answer_question
from src.nodes.execute_code_node import execute_code
from src.nodes.format_output_node import format_output

def build_graph():
    graph = StateGraph(dict)
    
    graph.add_node("load_csv", load_csv)
    graph.add_node("answer_question", answer_question)
    graph.add_node("execute_code", execute_code)
    graph.add_node("format_output", format_output)

    graph.set_entry_point("load_csv")
    graph.add_edge("load_csv", "answer_question")
    graph.add_edge("answer_question", "execute_code")
    graph.add_edge("execute_code", "format_output")
    graph.add_edge("format_output", END)

    return graph.compile()