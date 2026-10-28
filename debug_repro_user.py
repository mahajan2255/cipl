import pandas as pd
import io

# Exact header provided by user
header = "Market\tMeasure\tProduct\tCorporate\tManufacturer\tTrademark\tBrand\tBev Category\tBev SubCategory\tBev Segment\tFlavour\tAdult\tTCCC Global Segments\tJoule\tCarbonation\tPacktype\tPacksize\tSize Type\tServe\tMultiple\tMultipack\tJanuary 2018\tFebruary 2018\tMarch 2018"
# Dummy data row matching columns
row = "Mkt\tMsr\tProd\tCorp\tMfg\tTM\tBrand\tCat\tSub\tSeg\tFlav\tAdult\tTCCC\tJoule\tCarb\tPack\tSize\tType\tServe\tMult\tMulti\t100\t110\t120"

content = f"{header}\n{row}"

print("Creating dummy file with user headers...")
with open("debug_user_repro.csv", "w") as f:
    f.write(content)

try:
    print("Loading file (auto detect sep)...")
    # Simulate ingest.py logic
    df = pd.read_csv("debug_user_repro.csv", sep=None, engine='python')
    print("Columns loaded:", df.columns.tolist())
    
    # Simulate column cleaning in ingest.py
    df.columns = [str(col).strip() for col in df.columns]
    
    expr = "`February 2018` - `January 2018`"
    print(f"\nAttempting to eval: {expr}")
    
    df['Check'] = df.eval(expr)
    print("\nSuccess! Result:")
    print(df[['January 2018', 'February 2018', 'Check']])
    
except Exception as e:
    print(f"\nFAILED: {e}")
