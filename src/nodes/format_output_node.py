import json
import re

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