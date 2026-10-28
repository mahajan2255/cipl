import pandas as pd
from app.ingest import process_chat_query

# Create dummy dataframe
df = pd.DataFrame({
    'Revenue': [100, 200, 300],
    'Cost': [50, 100, 150],
    'Region': ['A', 'B', 'A']
})

print("Testing simple stats...")
res = process_chat_query(df, "average revenue")
print(res)

print("\nTesting plot...")
try:
    res = process_chat_query(df, "plot revenue by region")
    print("Plot result type:", res.get('type'))
    if res.get('content'): print("Content:", res['content'])
except Exception as e:
    print("CRASH:", e)
