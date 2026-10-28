import pandas as pd
try:
    df = pd.read_csv('test_data.csv')
    print("DataFrame Info:")
    print(df.info())
    print("\nColumns:", df.columns.tolist())
    
    expr = "(`Feb-18` - `Jan-18`) / `Jan-18`"
    print(f"\nAttempting to eval: {expr}")
    
    df['Growth'] = df.eval(expr)
    print("\nSuccess!")
except Exception as e:
    print(f"\nFailed: {e}")
