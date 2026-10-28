import pandas as pd
try:
    # Try tab separator
    df = pd.read_csv('test_data.csv', sep='\t')
    print("DataFrame Info:")
    print(df.info())
    print("\nColumns sample:", df.columns.tolist()[:10])
    
    # Check if Jan-18 exists
    if 'Jan-18' not in df.columns:
        print("Jan-18 NOT found in columns!")
    else:
        # Check type
        print(f"Jan-18 Type: {df['Jan-18'].dtype}")
        
    expr = "(`Feb-18` - `Jan-18`) / `Jan-18`"
    print(f"\nAttempting to eval: {expr}")
    
    df['Growth'] = df.eval(expr)
    print("\nSuccess!")
except Exception as e:
    print(f"\nFailed: {e}")
