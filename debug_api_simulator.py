import sys
import os
import pandas as pd

# Add current dir to path to mock 'app' module structure
sys.path.append(os.getcwd())

print("Attempting to import app.ingest...")
try:
    from app.ingest import apply_transformation
    print("Import SUCCESS")
except Exception as e:
    print(f"Import FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Create dummy DF
df = pd.DataFrame({'A': [10, 20], 'B': [1, 2]})
params = {"new_column": "C", "expression": "A - B"}

print(f"\nTesting formula: {params}")
try:
    df_new = apply_transformation(df, "formula", params)
    print("Execution SUCCESS")
    print(df_new)
except Exception as e:
    print(f"Execution FAILED: {e}")
    import traceback
    traceback.print_exc()
