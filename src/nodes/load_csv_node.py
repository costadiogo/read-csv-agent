import io
import pandas as pd

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