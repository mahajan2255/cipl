import pandas as pd
try:
    # creating dummy data similar to user's
    data = {
        'Jan-18': [100, 200, 300],
        'Feb-18': [110, 210, 330]
    }
    df = pd.DataFrame(data)
    print("DataFrame Info:")
    print(df.info())
    
    expr = "(`Feb-18` - `Jan-18`) / `Jan-18`"
    print(f"\nAttempting to eval: {expr}")
    
    df['Growth'] = df.eval(expr)
    print("\nSuccess! Result:")
    print(df)
except Exception as e:
    print(f"\nFailed: {e}")
