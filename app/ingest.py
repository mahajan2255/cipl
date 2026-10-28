import pandas as pd 
import numpy as np 
from typing import List, Tuple, Optional, Dict, Any 
import re 
import matplotlib 
matplotlib.use('Agg')  # For non-interactive backend 
import matplotlib.pyplot as plt 
import seaborn as sns 
from io import BytesIO 
import base64 
import json 
 
# Color palette for consistent visuals 
COLOR_PALETTE = [ 
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf' 
] 
 
 
def load_sheet(path: str, sheet: Optional[str] = None) -> pd.DataFrame: 
    """Load CSV or Excel file""" 
    print(f"Loading file: {path}") 
     
    try: 
        if path.lower().endswith(".csv"):
            try:
                # Try auto-detecting separator
                df = pd.read_csv(path, sep=None, engine='python')
            except:
                # Fallback to default
                df = pd.read_csv(path) 
        else: 
            df = pd.read_excel(path, sheet_name=sheet) 
    except Exception as e: 
        raise ValueError(f"Failed to load file: {str(e)}") 
     
    # Clean column names 
    df.columns = [str(col).strip() for col in df.columns] 
     
    print(f"Loaded: {df.shape[0]} rows × {df.shape[1]} columns") 
    return df 
 
 
def auto_detect_columns(df: pd.DataFrame) -> Dict[str, Any]: 
    """ 
    Smart auto-detection of column types 
    Works for both your specific format and general datasets 
    """ 
    result = { 
        "id_cols": [], 
        "period_cols": [], 
        "measure_cols": [], 
        "value_cols": [], 
        "detection_method": "unknown" 
    } 
     
    # Check for your specific patterns first 
    standard_patterns = [ 
        'Market', 'Measure', 'Product', 'Corporate', 'Manufacturer', 'Trademark', 
        'Brand', 'Bev Category', 'Bev SubCategory', 'Bev Segment', 'Flavour', 'Adult', 
        'TCCC Global Segments', 'Joule', 'Carbonation', 'Packtype', 'Packsize', 
        'Size Type', 'Serve', 'Multiple', 'Multipack' 
    ] 
     
    # Look for columns matching patterns 
    pattern_matches = [] 
    for col in df.columns: 
        col_lower = str(col).lower() 
        for pattern in standard_patterns: 
            if pattern.lower() in col_lower: 
                pattern_matches.append(col) 
                break 
     
    if pattern_matches and len(pattern_matches) >= 3: 
        # Looks like your specific format 
        result["id_cols"] = pattern_matches 
        result["period_cols"] = [c for c in df.columns if c not in pattern_matches] 
        result["detection_method"] = "standard_patterns" 
        print(f"✓ Detected standard pattern columns: {pattern_matches}") 
        return result 
     
    # Smart detection for general datasets 
    print("No standard patterns found. Using smart detection...") 
     
    id_candidates = [] 
    period_candidates = [] 
    value_candidates = [] 
     
    for col in df.columns: 
        col_str = str(col) 
         
        # Check if column looks like a period/date 
        is_period = False 
         
        # Period patterns 
        period_patterns = [ 
            r'\d{4}[Qq]\d', r'\d{4}[Mm]\d', r'\d{4}-\d{2}', r'\d{4}/\d{2}', 
            r'[Qq]\d-\d{4}', r'[Mm]\d{2}', r'[Ww]eek\d', r'FY\d{2}', 
            r'\d{2}/\d{2}/\d{4}', r'\d{4}\.\d{2}', r'\d{6}', r'\d{8}' 
        ] 
         
        for pattern in period_patterns: 
            if re.search(pattern, col_str): 
                is_period = True 
                break 
         
        # Also check if column name contains digits (common for periods) 
        if not is_period and any(c.isdigit() for c in col_str): 
            # Could be a period column 
            if df[col].dtype in ['int64', 'float64']: 
                period_candidates.append(col) 
            else: 
                # Check sample values 
                sample = df[col].dropna().head(3).tolist() 
                if sample and any(isinstance(v, str) and any(c.isdigit() for c in str(v)) for v in sample): 
                    period_candidates.append(col) 
                else: 
                    id_candidates.append(col) 
        else: 
            # Check data characteristics 
            unique_ratio = df[col].nunique() / len(df) 
             
            if df[col].dtype in ['int64', 'float64']: 
                value_candidates.append(col) 
            elif df[col].dtype == 'object' and unique_ratio < 0.7: 
                id_candidates.append(col) 
            elif is_period: 
                period_candidates.append(col) 
            else: 
                id_candidates.append(col) 
     
    # Final assignment 
    if id_candidates and (period_candidates or value_candidates): 
        result["id_cols"] = id_candidates 
        result["period_cols"] = period_candidates 
        result["value_cols"] = value_candidates 
        result["detection_method"] = "smart_detection" 
    else: 
        # Fallback: first 3-5 columns as IDs, rest as values 
        result["id_cols"] = df.columns[:min(5, len(df.columns))].tolist() 
        result["period_cols"] = df.columns[min(5, len(df.columns)):].tolist() 
        result["detection_method"] = "fallback" 
     
    print(f"✓ Detection complete: {result['detection_method']}") 
    print(f"  ID columns: {len(result['id_cols'])}") 
    print(f"  Period/Value columns: {len(result['period_cols'])}") 
     
    return result 
 
 
def melt_wide_to_long(df: pd.DataFrame,  
                     auto_detect: bool = True, 
                     id_cols: Optional[List[str]] = None, 
                     period_cols: Optional[List[str]] = None, 
                     value_name: str = "Value") -> Tuple[pd.DataFrame, pd.DataFrame]: 
    """ 
    Convert wide format to long format 
    Works with any dataset structure 
    """ 
     
    print("\n" + "="*80) 
    print("MELTING: Wide → Long Format") 
    print("="*80) 
     
    # Auto-detect if needed 
    if auto_detect and (id_cols is None or period_cols is None): 
        print("Auto-detecting columns...") 
        detection = auto_detect_columns(df) 
        id_cols = detection["id_cols"] if id_cols is None else id_cols 
        period_cols = detection["period_cols"] if period_cols is None else period_cols 
         
        if detection["detection_method"] == "standard_patterns": 
            print("✓ Using your specific data pattern detection") 
     
    # Validate 
    if not id_cols: 
        # Use non-numeric columns as IDs 
        id_cols = [c for c in df.columns if df[c].dtype == 'object'] 
        if not id_cols: 
            id_cols = df.columns[:3].tolist() 
     
    if not period_cols: 
        period_cols = [c for c in df.columns if c not in id_cols] 
     
    print(f"\nID columns ({len(id_cols)}):") 
    for i, col in enumerate(id_cols[:10]): 
        print(f"  {i+1}. {col}") 
    if len(id_cols) > 10: 
        print(f"  ... and {len(id_cols) - 10} more") 
     
    print(f"\nPeriod/Value columns ({len(period_cols)}):") 
    for i, col in enumerate(period_cols[:10]): 
        print(f"  {i+1}. {col}") 
    if len(period_cols) > 10: 
        print(f"  ... and {len(period_cols) - 10} more") 
     
    # Create identities 
    identities = df[id_cols].drop_duplicates().reset_index(drop=True) 
    print(f"\nUnique identity combinations: {len(identities)}") 
     
    # Melt the dataframe 
    print(f"\nMelting {len(df)} rows...") 
    melted = pd.melt( 
        df, 
        id_vars=id_cols, 
        value_vars=period_cols, 
        var_name="Period", 
        value_name=value_name 
    ) 
     
    # Clean and convert 
    melted["Period"] = melted["Period"].astype(str).str.strip() 
     
    # Extract measure from period if needed (e.g., "2024Q1_Revenue" -> Period="2024Q1", Measure="Revenue") 
    if melted["Period"].str.contains("_").any(): 
        print("Extracting measures from period names...") 
        split_data = melted["Period"].str.split("_", n=1, expand=True) 
        if split_data.shape[1] == 2: 
            melted["Period"] = split_data[0] 
            melted["Measure"] = split_data[1] 
            print("✓ Created separate 'Measure' column") 
     
    # Convert values to numeric and handle NumPy types 
    try: 
        melted[value_name] = pd.to_numeric(melted[value_name], errors='coerce') 
        # Convert NumPy types to Python native types 
        melted[value_name] = melted[value_name].astype('float64') 
        null_count = melted[value_name].isna().sum() 
        if null_count > 0: 
            print(f"  Converted {len(melted) - null_count} values to numeric") 
            print(f"  {null_count} values could not be converted (set to 0)") 
            melted[value_name] = melted[value_name].fillna(0) 
    except: 
        print("  Values kept as original type") 
     
    print(f"\n✓ Melt completed successfully!") 
    print(f"  Original shape: {df.shape}") 
    print(f"  Melted shape: {melted.shape}") 
    print(f"  Expected rows: {len(identities)} × {len(period_cols)} = {len(identities) * len(period_cols)}") 
    print(f"  Actual rows: {len(melted)}") 
     
    return melted.reset_index(drop=True), identities 
 
 
def pivot_measures_to_columns( 
    melted: pd.DataFrame, 
    core_cols: List[str], 
    measure_col: str = "Measure", 
    value_col: str = "Value", 
    period_col: str = "Period" 
) -> pd.DataFrame: 
    """ 
    Pivot measures to column headers WITHOUT AGGREGATION 
    This preserves individual values instead of summing/averaging 
    """ 
     
    print("\n" + "="*80) 
    print(f"PIVOT: {measure_col} → Column Headers (No Aggregation)") 
    print("="*80) 
     
    # Check required columns 
    required_cols = core_cols + [period_col, measure_col, value_col] 
    missing_cols = [c for c in required_cols if c not in melted.columns] 
     
    if missing_cols: 
        raise ValueError(f"Missing columns: {missing_cols}. Available: {melted.columns.tolist()}") 
     
    print(f"Core columns (stay as rows): {core_cols}") 
    print(f"Pivoting column: '{measure_col}' → will become headers") 
    print(f"Values column: '{value_col}'") 
    print(f"Period column: '{period_col}'") 
     
    # Check for duplicates that would cause aggregation 
    key_cols = core_cols + [period_col, measure_col] 
    duplicate_check = melted.duplicated(subset=key_cols, keep=False) 
    duplicate_count = duplicate_check.sum() 
     
    if duplicate_count > 0: 
        print(f"⚠️  WARNING: Found {duplicate_count} potential duplicate combinations!") 
        print("   Attempting to pivot with first occurrence only...") 
         
        # Remove duplicates by keeping first occurrence 
        melted_clean = melted.drop_duplicates(subset=key_cols, keep='first') 
        removed_rows = len(melted) - len(melted_clean) 
        print(f"   Removed {removed_rows} duplicate rows") 
         
        melted = melted_clean 
     
    print("✓ Pivoting without aggregation (using set_index + unstack)") 
     
    # Method 1: Set index and unstack (no aggregation) 
    # This preserves exact values without summing 
    try: 
        # Create multi-index 
        melted_indexed = melted.set_index(core_cols + [period_col] + [measure_col]) 
         
        # Unstack the measure column to create columns 
        pivoted = melted_indexed[value_col].unstack().reset_index() 
         
        # Fill NaN values with 0 
        pivoted = pivoted.fillna(0) 
         
    except Exception as e: 
        print(f"  Fallback to pivot_table due to: {str(e)}") 
        # Fallback to pivot_table but without aggregation 
        # Add a unique identifier to prevent aggregation 
        melted['unique_id'] = range(len(melted)) 
        pivoted = melted.pivot_table( 
            index=core_cols + [period_col], 
            columns=measure_col, 
            values=value_col, 
            aggfunc='first',  # Take first value if duplicates 
            fill_value=0 
        ).reset_index() 
     
    # Clean column names if multi-index 
    if isinstance(pivoted.columns, pd.MultiIndex): 
        pivoted.columns = [col[1] if col[1] else col[0] for col in pivoted.columns] 
     
    print(f"\n✓ Pivot completed!") 
    print(f"  Original shape: {melted.shape}") 
    print(f"  Pivoted shape: {pivoted.shape}") 
     
    # Count new columns (measures that became headers) 
    measure_columns = [col for col in pivoted.columns  
                      if col not in core_cols and col != period_col] 
    print(f"  New measure columns created: {len(measure_columns)}") 
     
    # Show sample of new columns 
    print(f"\nSample of new columns:") 
    for i, col in enumerate(pivoted.columns[:15]):  # Show first 15 
        if i < len(core_cols) + 1:  # core_cols + period 
            print(f"  * {col}") 
        else: 
            print(f"    {col}") 
    if len(pivoted.columns) > 15: 
        print(f"    ... and {len(pivoted.columns) - 15} more columns") 
     
    return pivoted 
 
 
def flexible_pivot( 
    df: pd.DataFrame, 
    index_cols: List[str], 
    columns_col: str, 
    values_col: str, 
    aggfunc: str = "sum" 
) -> pd.DataFrame: 
    """ 
    Flexible pivot for any dataset 
    """ 
    print(f"\nFlexible pivot:") 
    print(f"  Index columns: {index_cols}") 
    print(f"  Columns from: '{columns_col}' → will become headers") 
    print(f"  Values from: '{values_col}'") 
    print(f"  Aggregation: {aggfunc}") 
     
    # Check for duplicates that would cause unintended aggregation 
    duplicate_check = df.duplicated(subset=index_cols + [columns_col], keep=False) 
    duplicate_count = duplicate_check.sum() 
     
    if duplicate_count > 0 and aggfunc == "sum": 
        print(f"⚠️  WARNING: Found {duplicate_count} duplicate index+column combinations") 
        print(f"   Using 'first' aggregation instead of 'sum' to preserve values") 
        aggfunc = "first" 
     
    # Perform pivot 
    pivoted = df.pivot_table( 
        index=index_cols, 
        columns=columns_col, 
        values=values_col, 
        aggfunc=aggfunc, 
        fill_value=0 
    ).reset_index() 
     
    # Flatten column names 
    if isinstance(pivoted.columns, pd.MultiIndex): 
        pivoted.columns = [f"{col[1]}" if col[0] == values_col else col[0]  
                          for col in pivoted.columns] 
     
    print(f"  Result shape: {pivoted.shape}") 
    return pivoted 
 
 
def get_data_summary(df: pd.DataFrame) -> Dict[str, Any]: 
    """Get comprehensive data summary""" 
    # Convert all numeric columns to Python types first 
    df_summary = df.copy() 
    for col in df_summary.select_dtypes(include=[np.number]).columns: 
        df_summary[col] = df_summary[col].astype('float64') 
     
    summary = { 
        "shape": df_summary.shape, 
        "columns": df_summary.columns.tolist(), 
        "dtypes": {col: str(dtype) for col, dtype in df_summary.dtypes.items()}, 
        "memory_mb": round(df_summary.memory_usage(deep=True).sum() / (1024 * 1024), 2), 
        "null_counts": df_summary.isnull().sum().to_dict(), 
        "unique_counts": {col: df_summary[col].nunique() for col in df_summary.columns} 
    } 
     
    # Numeric columns stats 
    numeric_cols = df_summary.select_dtypes(include=[np.number]).columns 
    if len(numeric_cols) > 0: 
        stats = df_summary[numeric_cols].describe() 
        # Convert to Python types 
        stats_dict = {} 
        for col in stats.columns: 
            stats_dict[col] = { 
                k: float(v) if isinstance(v, (np.floating, np.integer)) else v 
                for k, v in stats[col].to_dict().items() 
            } 
        summary["numeric_stats"] = stats_dict 
     
    return summary 
 
 
def suggest_operations(df: pd.DataFrame) -> Dict[str, Any]: 
    """Suggest operations based on data structure""" 
    suggestions = { 
        "available_operations": ["view", "summary", "melt", "pivot", "export", "visualize"], 
        "column_analysis": {}, 
        "recommendations": [] 
    } 
     
    # Analyze each column 
    for col in df.columns: 
        col_info = { 
            "dtype": str(df[col].dtype), 
            "unique": int(df[col].nunique()), 
            "sample": df[col].dropna().head(3).tolist(), 
            "nulls": int(df[col].isnull().sum()), 
            "is_numeric": bool(pd.api.types.is_numeric_dtype(df[col])) 
        } 
        suggestions["column_analysis"][col] = col_info 
     
    # Check if data is wide format (many columns) 
    if len(df.columns) > 8: 
        suggestions["recommendations"].append("Data appears to be in wide format - consider 'melt' operation") 
        suggestions["available_operations"].append("melt_wide_to_long") 
     
    # Check if data has measure-like structure 
    measure_keywords = ['measure', 'metric', 'kpi', 'indicator'] 
    value_keywords = ['value', 'amount', 'score', 'quantity', 'volume'] 
     
    for col in df.columns: 
        col_lower = col.lower() 
        if any(kw in col_lower for kw in measure_keywords): 
            suggestions["recommendations"].append(f"Column '{col}' looks like a measure column - suitable for pivot") 
        if any(kw in col_lower for kw in value_keywords): 
            suggestions["recommendations"].append(f"Column '{col}' looks like a value column") 
     
    # Auto-detect columns 
    detection = auto_detect_columns(df) 
    # Convert detection to JSON-serializable format 
    detection["id_cols"] = detection.get("id_cols", []) 
    detection["period_cols"] = detection.get("period_cols", []) 
    detection["measure_cols"] = detection.get("measure_cols", []) 
    detection["value_cols"] = detection.get("value_cols", []) 
    suggestions["detection"] = detection 
     
    # Add visualization suggestions 
    suggestions["visualization_recommendations"] = generate_viz_suggestions(df) 
     
    return suggestions 
 
 
# ============================================================================ 
# VISUALIZATION FUNCTIONS 
# ============================================================================ 
 
def generate_viz_suggestions(df: pd.DataFrame) -> Dict[str, Any]: 
    """Generate visualization suggestions based on data structure""" 
    suggestions = { 
        "available_charts": [], 
        "recommended_charts": [], 
        "dimensions": [], 
        "measures": [] 
    } 
     
    # Identify numeric columns (measures) 
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist() 
    if numeric_cols: 
        suggestions["measures"] = numeric_cols[:5]  # Limit to 5 measures 
        suggestions["available_charts"].extend([ 
            "line_chart", "bar_chart", "scatter_plot", "histogram",  
            "box_plot", "heatmap", "treemap" 
        ]) 
     
    # Identify categorical columns (dimensions) 
    cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist() 
    if cat_cols: 
        suggestions["dimensions"] = cat_cols[:5]  # Limit to 5 dimensions 
        suggestions["available_charts"].extend(["pie_chart", "donut_chart"]) 
     
    # Time-based columns 
    date_cols = [] 
    for col in df.columns: 
        if any(keyword in str(col).lower() for keyword in ['date', 'time', 'period', 'year', 'month', 'quarter']): 
            date_cols.append(col) 
            try: 
                # Try to convert to datetime 
                pd.to_datetime(df[col], errors='coerce') 
                suggestions["available_charts"].append("time_series") 
            except: 
                pass 
     
    # Remove duplicates 
    suggestions["available_charts"] = list(set(suggestions["available_charts"])) 
     
    # Generate specific recommendations 
    if numeric_cols and cat_cols: 
        suggestions["recommended_charts"].append({ 
            "type": "grouped_bar", 
            "description": f"Compare {' and '.join(numeric_cols[:2])} across {cat_cols[0]}", 
            "x_axis": cat_cols[0], 
            "y_axis": numeric_cols[0], 
            "group_by": cat_cols[1] if len(cat_cols) > 1 else None 
        }) 
     
    if len(numeric_cols) >= 2: 
        suggestions["recommended_charts"].append({ 
            "type": "scatter_plot", 
            "description": f"Relationship between {numeric_cols[0]} and {numeric_cols[1]}", 
            "x_axis": numeric_cols[0], 
            "y_axis": numeric_cols[1] 
        }) 
     
    if date_cols and numeric_cols: 
        suggestions["recommended_charts"].append({ 
            "type": "time_series", 
            "description": f"Trend of {numeric_cols[0]} over time", 
            "date_column": date_cols[0], 
            "value_column": numeric_cols[0] 
        }) 
     
    return suggestions 
 
 

def _plot_to_base64() -> str:
    """Save current matplotlib figure to base64 string"""
    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    
    # Critical: Clear the figure to prevent memory leaks and interference
    plt.close() 
    
    graphic = base64.b64encode(image_png)
    return graphic.decode('utf-8')



def _ensure_numeric(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    """Helper to ensure specific columns are numeric"""
    df_clean = df.copy()
    for col in cols:
        df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0)
    return df_clean

def create_line_chart(df: pd.DataFrame, x_col: str, y_cols: List[str],  
                     title: str = "Line Chart", figsize: tuple = (12, 6)) -> str: 
    """Create multi-line chart and return base64 encoded image""" 
    plt.figure(figsize=figsize) 
     
    # Ensure value columns are numeric before aggregation
    df_clean = _ensure_numeric(df, y_cols)

    # Aggregate by x_col to handle duplicates and ensure unique X values
    # For line charts, sorting by X is critical
    agg_df = df_clean.groupby(x_col)[y_cols].sum().sort_index()
    
    # Limit to top 100 points to avoid overcrowding
    if len(agg_df) > 100:
        # If too many points, maybe just take the first 100 or resample? 
        # For now, let's just warn or take head, but for line chart usually we want the full trend.
        # If it's categorical, 100 is a lot. if it's time, 100 is fine.
        pass

    for i, y_col in enumerate(y_cols): 
        plt.plot(agg_df.index, agg_df[y_col], marker='o', label=y_col, color=COLOR_PALETTE[i % len(COLOR_PALETTE)]) 
     
    plt.title(title, fontsize=14, fontweight='bold') 
    plt.xlabel(x_col, fontsize=12) 
    plt.ylabel('Value', fontsize=12) 
    plt.legend(title='Metrics') 
    plt.grid(True, alpha=0.3) 
    plt.xticks(rotation=45) 
    plt.tight_layout() 
     
    return _plot_to_base64() 
 
 
def create_bar_chart(df: pd.DataFrame, x_col: str, y_cols: List[str],  
                    group_col: Optional[str] = None, title: str = "Bar Chart",  
                    figsize: tuple = (10, 6)) -> str: 
    """Create bar chart (grouped or stacked)""" 
    plt.figure(figsize=figsize) 
    
    # Ensure value columns are numeric
    df_clean = _ensure_numeric(df, y_cols)

    if group_col: 
        # Grouped bar chart with specific group column
        y_col = y_cols[0] if isinstance(y_cols, list) else y_cols
        grouped = df_clean.groupby([x_col, group_col])[y_col].sum().unstack() 
        ax = grouped.plot(kind='bar', color=COLOR_PALETTE[:len(grouped.columns)]) 
    else: 
        # Multi-column bar chart (side-by-side)
        # Aggregate by x_col to handle duplicates and ensure unique X values
        agg_df = df_clean.groupby(x_col)[y_cols].sum()
        
        # Limit to top 50 categories to avoid overcrowding if too many
        if len(agg_df) > 50:
            agg_df = agg_df.head(50) 
            
        ax = agg_df.plot(kind='bar', color=COLOR_PALETTE[:len(y_cols)]) 
     
    plt.title(title, fontsize=14, fontweight='bold') 
    plt.xlabel(x_col, fontsize=12) 
    plt.ylabel("Value", fontsize=12) 
    plt.legend(title=group_col if group_col else "Metrics") 
    plt.grid(axis='y', alpha=0.3) 
    plt.xticks(rotation=45) 
    plt.tight_layout() 
     
    return _plot_to_base64() 
 
 
def create_scatter_plot(df: pd.DataFrame, x_col: str, y_col: str,  
                       color_col: Optional[str] = None, size_col: Optional[str] = None, 
                       title: str = "Scatter Plot", figsize: tuple = (10, 8)) -> str: 
    """Create scatter plot with optional color and size encoding""" 
    plt.figure(figsize=figsize) 
     
    # Create a copy to avoid modifying original info
    plot_df = df.copy()
    
    # Try to convert X and Y to numeric if possible, but keep original if not (Seaborn can plot categorical X/Y)
    # However, for scatter plots, usually we want numeric X/Y.
    for col in [x_col, y_col]:
        plot_df[col] = pd.to_numeric(plot_df[col], errors='ignore')

    # Handle size column - must be numeric
    if size_col:
        plot_df[size_col] = pd.to_numeric(plot_df[size_col], errors='coerce')
        plot_df = plot_df.dropna(subset=[size_col])

    # Use Seaborn which handles categorical 'hue' (color) better than matplotlib
    sns.scatterplot(
        data=plot_df,
        x=x_col,
        y=y_col,
        hue=color_col if color_col else None,
        size=size_col if size_col else None,
        palette="viridis" if color_col and pd.api.types.is_numeric_dtype(plot_df[color_col]) else (COLOR_PALETTE if color_col else None),
        alpha=0.6,
        sizes=(20, 200) if size_col else None
    )
    
    # Move legend outside if it exists
    if color_col or size_col:
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
     
    plt.title(title, fontsize=14, fontweight='bold') 
    plt.grid(True, alpha=0.3) 
    plt.tight_layout() 
     
    return _plot_to_base64() 
 
 
def create_histogram(df: pd.DataFrame, column: str, bins: int = 20, 
                    title: str = "Histogram", figsize: tuple = (10, 6)) -> str: 
    """Create histogram with distribution curve""" 
    plt.figure(figsize=figsize) 
     
    plt.hist(df[column].dropna(), bins=bins, color=COLOR_PALETTE[0],  
             alpha=0.7, edgecolor='black', density=True) 
     
    # Add KDE curve 
    try:
        from scipy import stats 
        data = df[column].dropna() 
        if len(data) > 1: 
            kde = stats.gaussian_kde(data) 
            x_range = np.linspace(data.min(), data.max(), 100) 
            plt.plot(x_range, kde(x_range), color=COLOR_PALETTE[1], linewidth=2) 
    except ImportError:
        print("Warning: scipy not installed, skipping KDE curve")
    except Exception as e:
        print(f"Warning: KDE curve generation failed: {e}") 
     
    plt.title(title, fontsize=14, fontweight='bold') 
    plt.xlabel(column, fontsize=12) 
    plt.ylabel('Density', fontsize=12) 
    plt.grid(True, alpha=0.3) 
    plt.tight_layout() 
     
    return _plot_to_base64() 
 
 
def create_box_plot(df: pd.DataFrame, category_col: str, value_col: str, 
                   title: str = "Box Plot", figsize: tuple = (12, 6)) -> str: 
    """Create box plot for distribution comparison""" 
    plt.figure(figsize=figsize) 
     
    # Ensure value column is numeric
    plot_df = df.copy()
    plot_df[value_col] = pd.to_numeric(plot_df[value_col], errors='coerce')
    plot_df = plot_df.dropna(subset=[value_col])

    # Prepare data - Limit to top 20 categories to prevent overcrowding
    # Sort by median value
    top_categories = plot_df.groupby(category_col)[value_col].median().sort_values(ascending=False).head(20).index
    data_to_plot = [plot_df[plot_df[category_col] == cat][value_col] for cat in top_categories] 
     
    box = plt.boxplot(data_to_plot, labels=top_categories, patch_artist=True) 
     
    # Color boxes 
    for i, patch in enumerate(box['boxes']): 
        patch.set_facecolor(COLOR_PALETTE[i % len(COLOR_PALETTE)]) 
        patch.set_alpha(0.7) 
     
    plt.title(title, fontsize=14, fontweight='bold') 
    plt.xlabel(category_col, fontsize=12) 
    plt.ylabel(value_col, fontsize=12) 
    plt.grid(True, alpha=0.3, axis='y') 
    plt.xticks(rotation=45) 
    plt.tight_layout() 
     
    return _plot_to_base64() 
 
 
def create_heatmap(df: pd.DataFrame, columns: List[str] = None, 
                  title: str = "Correlation Heatmap", figsize: tuple = (10, 8)) -> str: 
    """Create correlation heatmap""" 
    if columns is None: 
        columns = df.select_dtypes(include=[np.number]).columns.tolist() 
     
    if len(columns) < 2: 
        raise ValueError("Need at least 2 numeric columns for heatmap") 
     
    plt.figure(figsize=figsize) 
    
    # Ensure all columns are numeric
    numeric_df = df[columns].apply(pd.to_numeric, errors='coerce')
     
    # Calculate correlation matrix 
    corr_matrix = numeric_df.corr() 
     
    # Create heatmap 
    sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap="coolwarm", 
                square=True, linewidths=0.5, cbar_kws={"shrink": 0.8}) 
     
    plt.title(title, fontsize=14, fontweight='bold') 
    plt.tight_layout() 
     
    return _plot_to_base64() 
 
 
def create_pie_chart(df: pd.DataFrame, column: str, value_col: str, 
                    top_n: int = 10, title: str = "Pie Chart",  
                    figsize: tuple = (8, 8)) -> str: 
    """Create pie chart for top categories""" 
    plt.figure(figsize=figsize) 
    
    # Ensure value column is numeric
    df_clean = _ensure_numeric(df, [value_col])
     
    # Group and sort 
    # Ensure numeric
    grouped = df_clean.groupby(column)[value_col].sum().sort_values(ascending=False) 
    
    # Filter out negative or zero values (Pie chart requirement)
    grouped = grouped[grouped > 0]
    
    if grouped.empty:
         raise ValueError("No positive values to plot in Pie Chart")
     
    # Take top N and combine rest as "Other" 
    if len(grouped) > top_n: 
        top_data = grouped.head(top_n) 
        other_sum = grouped[top_n:].sum() 
        top_data["Other"] = other_sum 
    else: 
        top_data = grouped 
     
    # Create pie chart 
    colors = plt.cm.Set3(np.linspace(0, 1, len(top_data))) 
    wedges, texts, autotexts = plt.pie(top_data.values, labels=top_data.index, 
                                       autopct='%1.1f%%', colors=colors, 
                                       startangle=90, shadow=True) 
     
    # Improve label appearance 
    for text in texts: 
        text.set_fontsize(9) 
    for autotext in autotexts: 
        autotext.set_color('white') 
        autotext.set_fontweight('bold') 
     
    plt.title(title, fontsize=14, fontweight='bold') 
    plt.tight_layout() 
     
    return _plot_to_base64() 
 
 
def create_time_series(df: pd.DataFrame, date_col: str, value_cols: List[str], 
                      freq: str = 'M', title: str = "Time Series",  
                      figsize: tuple = (14, 7)) -> str: 
    """Create time series plot""" 
    plt.figure(figsize=figsize) 
     
    # Convert to datetime if needed 
    df_copy = df.copy() 
    try:
        df_copy[date_col] = pd.to_datetime(df_copy[date_col], errors='coerce')
        # Drop rows with invalid dates
        if df_copy[date_col].isna().all():
            raise ValueError(f"Column '{date_col}' could not be converted to datetime.")
        df_copy = df_copy.dropna(subset=[date_col])
        df_copy.set_index(date_col, inplace=True) 
    except Exception as e:
        raise ValueError(f"Failed to process date column '{date_col}': {str(e)}")

    # Ensure value columns are numeric
    for col in value_cols:
        df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce')

    # Resample if needed 
    if freq: 
        for col in value_cols: 
            try:
                resampled = df_copy[col].resample(freq).mean() 
                plt.plot(resampled.index, resampled.values, marker='o', label=col, 
                        color=COLOR_PALETTE[value_cols.index(col) % len(COLOR_PALETTE)]) 
            except Exception as e:
                print(f"Resampling failed for {col}: {e}")
                # Fallback to plotting without resampling
                plt.plot(df_copy.index, df_copy[col], marker='o', label=col, 
                        color=COLOR_PALETTE[value_cols.index(col) % len(COLOR_PALETTE)])
    else: 
        for col in value_cols: 
            plt.plot(df_copy.index, df_copy[col], marker='o', label=col, 
                    color=COLOR_PALETTE[value_cols.index(col) % len(COLOR_PALETTE)]) 
     
    plt.title(title, fontsize=14, fontweight='bold') 
    plt.xlabel('Date', fontsize=12) 
    plt.ylabel('Value', fontsize=12) 
    plt.legend(title='Metrics') 
    plt.grid(True, alpha=0.3) 
    plt.xticks(rotation=45) 
    plt.tight_layout() 
     
    return _plot_to_base64() 
 
 
def create_treemap_data(df: pd.DataFrame, path_cols: List[str], value_col: str) -> Dict: 
    """Prepare data for treemap visualization""" 
    import plotly.express as px 
     
    # Group data 
    grouped = df.groupby(path_cols)[value_col].sum().reset_index() 
     
    # Create hierarchical structure 
    hierarchy = [] 
    for i in range(len(path_cols)): 
        level_cols = path_cols[:i+1] 
        level_data = grouped.groupby(level_cols)[value_col].sum().reset_index() 
        hierarchy.append({ 
            "level": i, 
            "columns": level_cols, 
            "data": level_data.to_dict('records') 
        }) 
     
    return { 
        "hierarchy": hierarchy, 
        "max_value": float(grouped[value_col].max()), 
        "min_value": float(grouped[value_col].min()), 
        "total_value": float(grouped[value_col].sum()) 
    } 
 
 
def create_summary_dashboard(df: pd.DataFrame) -> Dict[str, Any]: 
    """Create comprehensive summary dashboard with multiple visualizations""" 
    dashboard = { 
        "summary_stats": get_data_summary(df), 
        "visualizations": [], 
        "insights": [] 
    } 
     
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist() 
    cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist() 
     
    # Create distribution charts for top 3 numeric columns 
    # Skip ID-like columns (high cardinality relative to count, unless it's unique but we generally don't want partial histograms of IDs)
    for i, col in enumerate(numeric_cols[:3]): 
        try: 
            img_data = create_histogram(df, col, title=f"Distribution of {col}") 
            dashboard["visualizations"].append({ 
                "type": "histogram", 
                "title": f"Distribution of {col}", 
                "image_data": img_data, 
                "column": col 
            }) 
        except Exception as e: 
            print(f"Dashboard Histogram error for {col}: {e}")
     
    # Create correlation heatmap if enough numeric columns 
    if len(numeric_cols) >= 3: 
        try: 
            img_data = create_heatmap(df, numeric_cols[:8], "Correlation Matrix") 
            dashboard["visualizations"].append({ 
                "type": "heatmap", 
                "title": "Correlation Matrix", 
                "image_data": img_data, 
                "columns": numeric_cols[:8] 
            }) 
        except Exception as e: 
             print(f"Dashboard Heatmap error: {e}")
     
    # Create top categories pie chart if available (First Categorical vs First Numeric)
    if cat_cols and numeric_cols: 
        try: 
            img_data = create_pie_chart(df, cat_cols[0], numeric_cols[0],  
                                       title=f"Top {cat_cols[0]} Share by {numeric_cols[0]}") 
            dashboard["visualizations"].append({ 
                "type": "pie_chart", 
                "title": f"Top {cat_cols[0]} by {numeric_cols[0]}", 
                "image_data": img_data 
            }) 
        except Exception as e: 
             print(f"Dashboard Pie Chart error: {e}")

    # NEW: Create Multi-Column Bar Chart (Top Categories)
    if cat_cols and len(numeric_cols) >= 1:
        try:
            # Use up to 2 numeric columns for comparison
            y_cols = numeric_cols[:2]
            img_data = create_bar_chart(df, cat_cols[0], y_cols, 
                                       title=f"Top {cat_cols[0]} by {', '.join(y_cols)}")
            dashboard["visualizations"].append({
                "type": "bar_chart",
                "title": f"Comparison: {', '.join(y_cols)} by {cat_cols[0]}",
                "image_data": img_data
            })
        except Exception as e:
            print(f"Dashboard Bar Chart error: {e}")

    # NEW: Try to find a date column for Time Series
    date_col = None
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]) or 'date' in col.lower() or 'period' in col.lower():
            date_col = col
            break
            
    if date_col and numeric_cols:
        try:
            img_data = create_time_series(df, date_col, numeric_cols[:2], 
                                         title=f"Trends over time ({date_col})")
            dashboard["visualizations"].append({
                "type": "time_series",
                "title": f"Trends of {', '.join(numeric_cols[:2])}",
                "image_data": img_data
            })
        except Exception as e:
            print(f"Dashboard Time Series error: {e}")
     
    # Generate insights 
    if numeric_cols: 
        for col in numeric_cols[:3]: 
            stats = df[col].describe() 
            dashboard["insights"].append({ 
                "column": col, 
                "mean": float(stats['mean']), 
                "median": float(df[col].median()), 
                "std": float(stats['std']), 
                "range": float(stats['max'] - stats['min']) 
            }) 
     
    return dashboard

# --- AI DATA ANALYST ---

def process_chat_query(df: pd.DataFrame, query: str) -> Dict[str, Any]:
    """
    Process natural language query using heuristic/rule-based logic.
    Returns: { "type": "text"|"plot", "content": str, "data": ... }
    """
    query = query.lower().strip()
    
    # RESPONSE TEMPLATE
    response = {"type": "text", "content": "I didn't understand that. Try asking for 'stats', 'plot', or specific columns."}
    
    # 1. SIMPLE STATS
    if "count" in query or "rows" in query:
        response["content"] = f"The dataset has {len(df)} rows and {len(df.columns)} columns."
        
    elif "column" in query or "header" in query:
        response["content"] = f"Columns in dataset: {', '.join(df.columns.tolist())}"
        
    elif "average" in query or "mean" in query:
        # Find numeric columns mentioned in query
        col = next((c for c in df.columns if c.lower() in query), None)
        if col:
             if pd.api.types.is_numeric_dtype(df[col]):
                 val = df[col].mean()
                 response["content"] = f"The average of '{col}' is {val:.2f}"
             else:
                 response["content"] = f"Column '{col}' is not numeric."
        else:
             # Default to first numeric
             nums = df.select_dtypes(include=[np.number]).columns
             if not nums.empty:
                 response["content"] = f"Average of '{nums[0]}': {df[nums[0]].mean():.2f}"
    
    elif "sum" in query or "total" in query:
        col = next((c for c in df.columns if c.lower() in query), None)
        if col and pd.api.types.is_numeric_dtype(df[col]):
             val = df[col].sum()
             response["content"] = f"Total of '{col}' is {val:,.2f}"
             
    elif "describe" in query or "summary" in query:
        response["content"] = df.describe().to_html(classes="table table-striped")
        response["html"] = True

    # 2. PLOTTING TRIGGERS
    elif "plot" in query or "chart" in query or "graph" in query or "visualize" in query:
        # Heuristic: try to find chart type
        chart_type = "bar_chart" # Default
        if "line" in query: chart_type = "line_chart"
        elif "scatter" in query: chart_type = "scatter_plot"
        elif "hist" in query: chart_type = "histogram"
        elif "pie" in query: chart_type = "pie_chart"
        
        # Find Mentioned Columns
    return response

def _fuzzy_match_columns(df: pd.DataFrame, query: str) -> List[str]:
    """Find columns mentioned in query with simple fuzzy matching"""
    cols_found = []
    query_lower = query.lower()
    
    # 1. Exact/Case-insensitive match
    for col in df.columns:
        if col.lower() in query_lower:
            cols_found.append(col)
            
    # 2. Partial word match (if no exact found) - e.g. "rev" matching "Revenue"
    if not cols_found:
        tokens = query_lower.split()
        for token in tokens:
            if len(token) < 3: continue # Skip short words
            for col in df.columns:
                if token in col.lower():
                    cols_found.append(col)
                    
    return list(set(cols_found)) # Unique

def process_chat_query(df: pd.DataFrame, query: str) -> Dict[str, Any]:
    """
    Process natural language query using heuristic/rule-based logic.
    Returns: { "type": "text"|"plot", "content": str, "data": ... }
    """
    query = query.lower().strip()
    
    # RESPONSE TEMPLATE
    response = {"type": "text", "content": "I didn't understand that. Try asking for 'stats', 'plot', or specific columns."}
    
    try:
        # 1. SIMPLE STATS
        if "count" in query or "rows" in query:
            response["content"] = f"The dataset has {len(df)} rows and {len(df.columns)} columns."
            return response
            
        elif "column" in query or "header" in query:
            response["content"] = f"Columns in dataset: {', '.join(df.columns.tolist())}"
            return response

        # 2. NUMERIC STATS (Avg, Sum, Max, Min)
        stat_map = {
            "average": "mean", "mean": "mean", "avg": "mean",
            "sum": "sum", "total": "sum",
            "max": "max", "highest": "max",
            "min": "min", "lowest": "min"
        }
        
        found_stat = next((k for k in stat_map if k in query), None)
        
        if found_stat:
            # Find column
            cols = _fuzzy_match_columns(df, query)
            target_col = cols[0] if cols else first_numeric_col(df)
            
            if target_col and pd.api.types.is_numeric_dtype(df[target_col]):
                op = stat_map[found_stat]
                val = getattr(df[target_col], op)()
                response["content"] = f"The {found_stat} of '{target_col}' is {val:,.2f}"
            elif target_col:
                response["content"] = f"Column '{target_col}' is not numeric, so I can't calculate {found_stat}."
            else:
                response["content"] = f"I couldn't find a numeric column to calculate {found_stat}."
            return response

        elif "describe" in query or "summary" in query:
            response["content"] = df.describe().to_html(classes="table table-striped")
            response["html"] = True
            return response

        # 3. PLOTTING TRIGGERS
        if "plot" in query or "chart" in query or "graph" in query or "visualize" in query or "show me" in query:
            # Heuristic: try to find chart type
            chart_type = "bar_chart" # Default
            if "line" in query: chart_type = "line_chart"
            elif "scatter" in query: chart_type = "scatter_plot"
            elif "hist" in query: chart_type = "histogram"
            elif "pie" in query: chart_type = "pie_chart"
            
            # Find Mentioned Columns
            mentioned_cols = _fuzzy_match_columns(df, query)
            
            img_data = None
            
            if chart_type == "histogram":
                col = mentioned_cols[0] if mentioned_cols else first_numeric_col(df)
                if col: img_data = create_histogram(df, col, title=f"Distribution of {col}")
                    
            elif chart_type == "scatter_plot":
                # Need 2 cols
                if len(mentioned_cols) >= 2:
                    img_data = create_scatter_plot(df, mentioned_cols[0], mentioned_cols[1])
                elif len(mentioned_cols) == 1:
                    # Provide hints
                    response["content"] = "For a scatter plot, I need two columns (X and Y). I only found one."
                    return response

            elif chart_type == "bar_chart":
                cat_cols = df.select_dtypes(include=['object', 'category']).columns
                num_cols = df.select_dtypes(include=[np.number]).columns
                
                x = next((c for c in mentioned_cols if c in cat_cols), cat_cols[0] if not cat_cols.empty else None)
                y = next((c for c in mentioned_cols if c in num_cols), num_cols[0] if not num_cols.empty else None)
                
                if x and y:
                    img_data = create_bar_chart(df, x, [y], title=f"{y} by {x}")
            
            elif chart_type == "line_chart":
                 # Trend
                 x = mentioned_cols[0] if mentioned_cols else df.columns[0]
                 y_list = [c for c in mentioned_cols if c != x]
                 if not y_list:
                     nums = df.select_dtypes(include=[np.number]).columns
                     if not nums.empty: y_list = [nums[0]]
                 
                 if y_list:
                     img_data = create_line_chart(df, x, y_list)

            if img_data:
                response["type"] = "plot"
                response["content"] = f"Here is the {chart_type} for {', '.join(mentioned_cols)}."
                response["image_data"] = img_data
            elif not response["content"].startswith("For a scatter"): # Don't overwrite specific errors
                 response["content"] = "I couldn't generate the plot. Please specify valid columns."

    except Exception as e:
        print(f"Chat Logic Error: {e}")
        response["content"] = f"I ran into an issue processing that: {str(e)}"

    return response 

def first_numeric_col(df):
    nums = df.select_dtypes(include=[np.number]).columns
    return nums[0] if not nums.empty else None 
 
 
def _plot_to_base64() -> str: 
    """Convert matplotlib plot to base64 string""" 
    buffer = BytesIO() 
    plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight') 
    buffer.seek(0) 
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8') 
    plt.close() 
    return image_base64 

# --- ADVANCED TRANSFORMATIONS ---

def apply_transformation(df: pd.DataFrame, operation: str, params: Dict[str, Any]) -> pd.DataFrame:
    """Apply advanced Transformations: filter, sort, formula"""
    df_new = df.copy()
    
    if operation == "filter":
        col = params.get("column")
        op = params.get("operator") # ==, !=, >, <, >=, <=, contains
        val = params.get("value")
        
        # Safe numeric conversion for values
        if isinstance(val, str) and val.replace('.','',1).isdigit() and op in [">", "<", ">=", "<="]:
             val = float(val)

        if op == "==": df_new = df_new[df_new[col] == val]
        elif op == "!=": df_new = df_new[df_new[col] != val]
        elif op == ">": df_new = df_new[df_new[col] > val]
        elif op == "<": df_new = df_new[df_new[col] < val]
        elif op == ">=": df_new = df_new[df_new[col] >= val]
        elif op == "<=": df_new = df_new[df_new[col] <= val]
        elif op == "contains": df_new = df_new[df_new[col].astype(str).str.contains(str(val), case=False, na=False)]
        
    elif operation == "sort":
        col = params.get("column")
        ascending = params.get("ascending", True)
        df_new = df_new.sort_values(by=col, ascending=ascending)
        
    elif operation == "formula":
        print(f"DEBUG: Entering formula block. Params: {params}")
        new_col = params.get("new_column")
        expr = params.get("expression")
        print(f"DEBUG: New Col: {new_col}, Expr: {expr}")
        
        if not new_col or not expr:
             print("DEBUG: Missing params")
             raise ValueError("Missing new column name or expression.")
             
        try:
             # Robust Eval using Python engine
             # Note: Columns with spaces must be backticked in the expression
             df_new[new_col] = df_new.eval(expr, engine='python')
        except Exception as e:
             raise ValueError(f"Formula Error: {str(e)}")
             
    elif operation == "rename":
        mapping = params.get("mapping") # {"old": "new"}
        df_new = df_new.rename(columns=mapping)
        
    return df_new

# --- REPORT GENERATION ---
from fpdf import FPDF

def generate_pdf_summary(df: pd.DataFrame, title: str = "Dataset Report") -> bytes:
    """Generate simple PDF report"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(40, 10, title)
    pdf.ln(20)
    
    # Summary Stats
    pdf.set_font("Arial", "B", 12)
    pdf.cell(40, 10, "Summary Statistics")
    pdf.ln(10)
    
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 10, f"Rows: {len(df)}")
    pdf.ln(6)
    pdf.cell(0, 10, f"Columns: {len(df.columns)}")
    pdf.ln(10)
    
    # Numeric Summary
    desc = df.describe().round(2)
    col_width = 30
    
    pdf.set_font("Arial", "B", 8)
    # Header
    pdf.cell(20, 10, "") # index col
    for col in desc.columns[:5]: # limit to 5 cols for page width
        pdf.cell(col_width, 10, str(col)[:12], border=1)
    pdf.ln()
    
    # Rows
    pdf.set_font("Arial", "", 8)
    for idx, row in desc.iterrows():
        pdf.cell(20, 10, str(idx), border=1)
        for val in row[:5]:
             pdf.cell(col_width, 10, str(val), border=1)
        pdf.ln()

    return pdf.output(dest='S').encode('latin-1') 
 
 
def get_visualization_types() -> Dict[str, Any]: 
    """Return available visualization types and their parameters""" 
    return { 
        "line_chart": { 
            "description": "Multi-line chart for trends over categories or time", 
            "required_params": ["x_column", "y_columns"], 
            "optional_params": ["title", "figsize"] 
        }, 
        "bar_chart": { 
            "description": "Bar chart for categorical comparisons", 
            "required_params": ["x_column", "y_columns"], 
            "optional_params": ["group_column", "title", "figsize"] 
        }, 
        "scatter_plot": { 
            "description": "Scatter plot for relationship analysis", 
            "required_params": ["x_column", "y_column"], 
            "optional_params": ["color_column", "size_column", "title", "figsize"] 
        }, 
        "histogram": { 
            "description": "Histogram for distribution analysis", 
            "required_params": ["column"], 
            "optional_params": ["bins", "title", "figsize"] 
        }, 
        "box_plot": { 
            "description": "Box plot for distribution comparison", 
            "required_params": ["category_column", "value_column"], 
            "optional_params": ["title", "figsize"] 
        }, 
        "heatmap": { 
            "description": "Correlation heatmap for numeric columns", 
            "required_params": ["columns"], 
            "optional_params": ["title", "figsize"] 
        }, 
        "pie_chart": { 
            "description": "Pie chart for composition analysis", 
            "required_params": ["column", "value_column"], 
            "optional_params": ["top_n", "title", "figsize"] 
        }, 
        "time_series": { 
            "description": "Time series plot for temporal data", 
            "required_params": ["date_column", "value_columns"], 
            "optional_params": ["frequency", "title", "figsize"] 
        }, 
        "summary_dashboard": { 
            "description": "Comprehensive dashboard with multiple visualizations", 
            "required_params": [], 
            "optional_params": [] 
        } 
    }