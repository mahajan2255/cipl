import os 
import shutil 
import tempfile 
import traceback 
import io 
import json 
from typing import Dict, Any, Optional, List, Tuple 
from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Body 
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse 
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel 
import pandas as pd 
import uvicorn 
import base64 
import numpy as np 
from fastapi.middleware.cors import CORSMiddleware
 
# Import from app.ingest 
from app.ingest import ( 
    load_sheet, 
    suggest_operations, 
    melt_wide_to_long, 
    pivot_measures_to_columns, 
    flexible_pivot, 
    get_data_summary, 
    generate_viz_suggestions, 
    get_visualization_types, 
    create_line_chart, 
    create_bar_chart, 
    create_scatter_plot, 
    create_histogram, 
    create_box_plot, 
    create_heatmap, 
    create_pie_chart, 
    create_time_series, 
    create_summary_dashboard, 
    create_treemap_data 
) 
 
app = FastAPI( 
    title="Universal Data Processor API", 
    description="Transform any dataset: Melt wide→long, Pivot measures→headers, Export results", 
    version="2.0.0", 
    docs_url="/docs", 
    redoc_url="/redoc" 
) 

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")
 
# In-memory storage for datasets 
DATASETS: Dict[str, Dict[str, Any]] = {} 
UPLOAD_DIR = "uploads" 
os.makedirs(UPLOAD_DIR, exist_ok=True) 
 
 
# DATA MODELS 
 
class UploadResponse(BaseModel): 
    dataset_id: str 
    filename: str 
    rows: int 
    columns: int 
    suggestions: Dict[str, Any] 
 
 
class MeltRequest(BaseModel): 
    id_cols: Optional[List[str]] = None 
    period_cols: Optional[List[str]] = None 
    value_name: str = "Value" 
    var_name: str = "Period" 
    auto_detect: bool = True 
 
 
class PivotRequest(BaseModel): 
    index_cols: List[str] 
    columns_col: str 
    values_col: str 
    aggfunc: str = "first"  # Changed from "sum" to "first" to preserve values 
 
 
class PivotMeasuresRequest(BaseModel): 
    core_cols: List[str] 
    measure_col: str = "Measure" 
    value_col: str = "Value" 
    period_col: str = "Period" 
 
 
class CleanRequest(BaseModel): 
    operations: List[str] = ["fill_nulls", "remove_duplicates"] 
 
 
class VisualizationRequest(BaseModel): 
    chart_type: str 
    parameters: Dict[str, Any] = {} 
    title: Optional[str] = None 
    figsize: Optional[Tuple[int, int]] = None 
 
 
 
# HELPER FUNCTIONS 
def get_dataset_or_404(dataset_id: str) -> Dict[str, Any]: 
    """Get dataset or raise 404 error""" 
    if dataset_id not in DATASETS: 
        raise HTTPException( 
            status_code=404, 
            detail=f"Dataset '{dataset_id}' not found. Available datasets: {list(DATASETS.keys())}" 
        ) 
    return DATASETS[dataset_id] 
 
 
 
# UPLOAD ENDPOINT 
 
@app.post("/upload", response_model=UploadResponse) 
async def upload_file(file: UploadFile = File(...)): 
    """Upload CSV or Excel file""" 
     
    if not file.filename: 
        raise HTTPException(400, "No filename provided") 
     
    # Create unique dataset ID 
    ds_id = f"ds_{len(DATASETS) + 1:04d}" 
     
    # Create temporary directory 
    tmpdir = tempfile.mkdtemp(dir=UPLOAD_DIR, prefix=f"{ds_id}_") 
    filepath = os.path.join(tmpdir, file.filename) 
     
    # Save uploaded file 
    try: 
        with open(filepath, "wb") as f: 
            shutil.copyfileobj(file.file, f) 
    except ValueError as e:
        raise HTTPException(400, f"{str(e)}")
    except Exception as e:
        raise HTTPException(500, f"Transformation failed: {str(e)}") 
     
    # Load and validate the data 
    try: 
        df = load_sheet(filepath) 
         
        # Get operation suggestions 
        suggestions = suggest_operations(df) 
         
        # Store dataset info 
        DATASETS[ds_id] = { 
            "id": ds_id, 
            "path": filepath, 
            "filename": file.filename, 
            "original": df.copy(), 
            "current": df.copy(),
            "dashboard_config": [], # List of saved charts 
            "processed": None, 
            "identities": None, 
            "history": [], 
            "metadata": { 
                "upload_time": pd.Timestamp.now().isoformat(), 
                "original_shape": df.shape, 
                "columns": df.columns.tolist(), 
                "suggestions": suggestions 
            } 
        } 
         
        return UploadResponse( 
            dataset_id=ds_id, 
            filename=file.filename, 
            rows=len(df), 
            columns=len(df.columns), 
            suggestions=suggestions 
        ) 
         
    except Exception as e: 
        # Clean up on error 
        if os.path.exists(tmpdir): 
            shutil.rmtree(tmpdir, ignore_errors=True) 
        traceback.print_exc() 
        raise HTTPException(500, f"Failed to process file: {str(e)}") 
 
 
 
# DATASET MANAGEMENT 
 
@app.get("/datasets") 
async def list_datasets(): 
    """List all uploaded datasets""" 
    result = [] 
    for ds_id, ds in DATASETS.items(): 
        result.append({ 
            "id": ds_id, 
            "filename": ds.get("filename", "unknown"), 
            "original_shape": ds.get("metadata", {}).get("original_shape", (0, 0)), 
            "current_shape": ds["current"].shape if ds["current"] is not None else (0, 0), 
            "has_processed": ds.get("processed") is not None, 
            "upload_time": ds.get("metadata", {}).get("upload_time") 
        }) 
    return {"datasets": result, "count": len(result)} 
 
 
@app.get("/dataset/{dataset_id}") 
async def get_dataset_info(dataset_id: str): 
    """Get dataset information""" 
    ds = get_dataset_or_404(dataset_id) 
     
    info = { 
        "id": dataset_id, 
        "filename": ds.get("filename"), 
        "upload_time": ds.get("metadata", {}).get("upload_time"), 
        "original_shape": ds.get("metadata", {}).get("original_shape"), 
        "current_shape": ds["current"].shape if ds["current"] is not None else None, 
        "current_columns": ds["current"].columns.tolist() if ds["current"] is not None else [], 
        "has_processed": ds.get("processed") is not None, 
        "has_identities": ds.get("identities") is not None, 
        "history_length": len(ds["history"]) 
    } 
     
    return info 
 
 
@app.delete("/dataset/{dataset_id}") 
async def delete_dataset(dataset_id: str): 
    """Delete dataset""" 
    if dataset_id not in DATASETS: 
        raise HTTPException(404, f"Dataset '{dataset_id}' not found") 
     
    ds = DATASETS[dataset_id] 
     
    try: 
        # Delete uploaded files 
        if "path" in ds: 
            file_dir = os.path.dirname(ds["path"]) 
            if os.path.exists(file_dir): 
                shutil.rmtree(file_dir, ignore_errors=True) 
         
        # Remove from memory 
        del DATASETS[dataset_id] 
         
        return {"status": "deleted", "dataset_id": dataset_id} 
     
    except Exception as e: 
        raise HTTPException(500, f"Failed to delete dataset: {str(e)}") 
 
 
 
# DATA VIEWING & ANALYSIS 
 
@app.get("/dataset/{dataset_id}/view") 
async def view_data( 
    dataset_id: str, 
    rows: int = Query(10, ge=1, le=1000), 
    start: int = Query(0, ge=0) 
): 
    """View dataset rows""" 
    ds = get_dataset_or_404(dataset_id) 
    df = ds["current"] 
     
    end = min(start + rows, len(df)) 
    
    # Handle NaN values before converting to dict (JSON compliant)
    df_view = df.iloc[start:end].replace({np.nan: None})
    data = df_view.to_dict(orient="records") 
     
    return { 
        "dataset_id": dataset_id, 
        "start": start, 
        "end": end, 
        "total_rows": len(df), 
        "columns": df.columns.tolist(), 
        "data": data 
    } 
 
 
@app.get("/dataset/{dataset_id}/summary") 
async def get_summary(dataset_id: str): 
    """Get dataset summary statistics""" 
    ds = get_dataset_or_404(dataset_id) 
    df = ds["current"] 
     
    summary = get_data_summary(df) 
     
    return { 
        "dataset_id": dataset_id, 
        "summary": summary 
    } 
 
 
@app.get("/dataset/{dataset_id}/suggestions") 
async def get_suggestions(dataset_id: str): 
    """Get operation suggestions""" 
    ds = get_dataset_or_404(dataset_id) 
     
    # Refresh suggestions based on current data 
    suggestions = suggest_operations(ds["current"]) 
    ds["metadata"]["suggestions"] = suggestions 
     
    return { 
        "dataset_id": dataset_id, 
        "suggestions": suggestions, 
        "current_shape": ds["current"].shape 
    } 
 
 
 
# MELT OPERATIONS 
 
@app.post("/dataset/{dataset_id}/melt") 
async def melt_dataset( 
    dataset_id: str, 
    request: MeltRequest 
): 
    """Convert wide format to long format""" 
    ds = get_dataset_or_404(dataset_id) 
     
    try: 
        # Save current state to history 
        ds["history"].append({ 
            "operation": "melt", 
            "timestamp": pd.Timestamp.now().isoformat(), 
            "previous_shape": ds["current"].shape, 
            "config": request.dict() 
        }) 
         
        # Perform melt 
        melted_df, identities = melt_wide_to_long( 
            df=ds["current"], 
            auto_detect=request.auto_detect, 
            id_cols=request.id_cols, 
            period_cols=request.period_cols, 
            value_name=request.value_name 
        ) 
         
        # Store results 
        ds["current"] = melted_df 
        ds["processed"] = melted_df 
        ds["identities"] = identities 
        ds["metadata"]["last_melt_config"] = request.dict() 
         
        return { 
            "status": "success", 
            "dataset_id": dataset_id, 
            "operation": "melt", 
            "melted_shape": melted_df.shape, 
            "unique_identities": len(identities), 
            "value_column": request.value_name, 
            "has_measure_column": "Measure" in melted_df.columns, 
            "has_period_column": "Period" in melted_df.columns, 
            "actual_period_column": "variable" if "variable" in melted_df.columns else "Period" 
        } 
         
    except Exception as e: 
        traceback.print_exc() 
        raise HTTPException(500, f"Melt operation failed: {str(e)}") 
 
 
 
# PIVOT OPERATIONS - FIXED VERSION 
 
@app.post("/dataset/{dataset_id}/pivot_measures") 
async def pivot_measures_dataset( 
    dataset_id: str, 
    request: PivotMeasuresRequest 
): 
    """Pivot measures to column headers (your original operation)""" 
    ds = get_dataset_or_404(dataset_id) 
     
    try: 
        # Check if we have the required columns 
        df = ds["current"] 
        available_cols = df.columns.tolist() 
         
        # Debug: Log available columns 
        print(f"Available columns: {available_cols}") 
        print(f"Looking for period_col: '{request.period_col}'") 
         
        # Check if period_col exists, if not try alternatives 
        if request.period_col not in available_cols: 
            # Try common alternatives 
            alternatives = ["variable", "Period", "month", "Month", "Date", "TIME_PERIOD"] 
            for alt in alternatives: 
                if alt in available_cols: 
                    print(f"Using alternative period column: '{alt}' instead of '{request.period_col}'") 
                    request.period_col = alt 
                    break 
             
            if request.period_col not in available_cols: 
                raise HTTPException(400, f"Period column '{request.period_col}' not found. Available columns: {available_cols}") 
         
        # Check other required columns 
        missing_cols = [] 
        for col in [request.measure_col, request.value_col]: 
            if col not in available_cols: 
                missing_cols.append(col) 
         
        if missing_cols: 
            raise HTTPException(400, f"Missing columns: {missing_cols}. Available: {available_cols}") 
         
        # Save to history 
        ds["history"].append({ 
            "operation": "pivot_measures", 
            "timestamp": pd.Timestamp.now().isoformat(), 
            "previous_shape": ds["current"].shape, 
            "config": request.dict() 
        }) 
         
        # Perform pivot 
        pivoted_df = pivot_measures_to_columns( 
            melted=ds["current"], 
            core_cols=request.core_cols, 
            measure_col=request.measure_col, 
            value_col=request.value_col, 
            period_col=request.period_col 
        ) 
         
        # Update dataset 
        ds["current"] = pivoted_df 
        ds["processed"] = pivoted_df 
        ds["metadata"]["last_pivot_config"] = request.dict() 
         
        return { 
            "status": "success", 
            "dataset_id": dataset_id, 
            "operation": "pivot_measures", 
            "pivoted_shape": pivoted_df.shape, 
            "core_columns": request.core_cols, 
            "measure_column": request.measure_col, 
            "period_column_used": request.period_col, 
            "new_columns_created": len(pivoted_df.columns) - len(request.core_cols) - 1 
        } 
         
    except Exception as e: 
        traceback.print_exc() 
        raise HTTPException(500, f"Pivot measures failed: {str(e)}") 
 
 
@app.post("/dataset/{dataset_id}/pivot") 
async def pivot_dataset( 
    dataset_id: str, 
    request: PivotRequest 
): 
    """Flexible pivot operation""" 
    ds = get_dataset_or_404(dataset_id) 
     
    try: 
        # Check if columns exist 
        df = ds["current"] 
        available_cols = df.columns.tolist() 
         
        missing_cols = [] 
        for col in request.index_cols + [request.columns_col, request.values_col]: 
            if col not in available_cols: 
                missing_cols.append(col) 
         
        if missing_cols: 
            raise HTTPException(400, f"Missing columns: {missing_cols}. Available: {available_cols}") 
         
        # Save to history 
        ds["history"].append({ 
            "operation": "pivot", 
            "timestamp": pd.Timestamp.now().isoformat(), 
            "previous_shape": ds["current"].shape, 
            "config": request.dict() 
        }) 
         
        # Perform pivot 
        pivoted_df = flexible_pivot( 
            df=ds["current"], 
            index_cols=request.index_cols, 
            columns_col=request.columns_col, 
            values_col=request.values_col, 
            aggfunc=request.aggfunc 
        ) 
         
        # Update dataset 
        ds["current"] = pivoted_df 
        ds["processed"] = pivoted_df 
         
        return { 
            "status": "success", 
            "dataset_id": dataset_id, 
            "operation": "pivot", 
            "pivoted_shape": pivoted_df.shape, 
            "index_columns": request.index_cols, 
            "pivot_column": request.columns_col, 
            "value_column": request.values_col, 
            "new_columns": [c for c in pivoted_df.columns if c not in request.index_cols] 
        } 
         
    except Exception as e: 
        traceback.print_exc() 
        raise HTTPException(500, f"Pivot operation failed: {str(e)}") 
 
 
 
# CLEAN OPERATIONS 
 
@app.post("/dataset/{dataset_id}/clean") 
async def clean_dataset( 
    dataset_id: str, 
    request: CleanRequest 
): 
    """Clean dataset""" 
    ds = get_dataset_or_404(dataset_id) 
     
    try: 
        # Save to history 
        ds["history"].append({ 
            "operation": "clean", 
            "timestamp": pd.Timestamp.now().isoformat(), 
            "previous_shape": ds["current"].shape, 
            "config": request.dict() 
        }) 
         
        df = ds["current"].copy() 
         
        # Apply cleaning operations 
        for op in request.operations: 
            if op == "fill_nulls": 
                # Fill numeric columns with 0, text columns with "Unknown" 
                for col in df.columns: 
                    if pd.api.types.is_numeric_dtype(df[col]): 
                        df[col] = df[col].fillna(0) 
                    else: 
                        df[col] = df[col].fillna("Unknown") 
                         
            elif op == "remove_duplicates": 
                initial_rows = len(df) 
                df = df.drop_duplicates() 
                removed = initial_rows - len(df) 
                print(f"Removed {removed} duplicate rows") 
                 
            elif op == "convert_types": 
                # Try to convert object columns to appropriate types 
                for col in df.select_dtypes(['object']).columns: 
                    try: 
                        converted = pd.to_numeric(df[col], errors='coerce') 
                        if not converted.isna().all(): 
                            df[col] = converted 
                    except: 
                        pass 
                         
            elif op == "standardize_text": 
                # Standardize text columns 
                for col in df.select_dtypes(['object']).columns: 
                    df[col] = df[col].astype(str).str.strip().str.title() 
         
        # Update dataset 
        ds["current"] = df 
        ds["processed"] = df 
         
        return { 
            "status": "success", 
            "dataset_id": dataset_id, 
            "operation": "clean", 
            "operations_performed": request.operations, 
            "new_shape": df.shape 
        } 
         
    except Exception as e: 
        traceback.print_exc() 
        raise HTTPException(500, f"Cleaning failed: {str(e)}") 
 
 
 
# UNDO / RESET 
 
@app.post("/dataset/{dataset_id}/undo") 
async def undo_operation(dataset_id: str, steps: int = Query(1, ge=1)): 
    """Undo previous operations""" 
    ds = get_dataset_or_404(dataset_id) 
     
    if steps > len(ds["history"]): 
        raise HTTPException(400, f"Only {len(ds['history'])} operations in history") 
     
    try: 
        # Restore original data 
        ds["current"] = ds["original"].copy() 
        undone_ops = ds["history"][-steps:] 
        ds["history"] = ds["history"][:-steps] 
        ds["processed"] = None 
        ds["identities"] = None 
         
        return { 
            "status": "success", 
            "dataset_id": dataset_id, 
            "undone_operations": [op["operation"] for op in undone_ops], 
            "current_shape": ds["current"].shape, 
            "remaining_history": len(ds["history"]) 
        } 
         
    except Exception as e: 
        traceback.print_exc() 
        raise HTTPException(500, f"Undo failed: {str(e)}") 
 
 
@app.post("/dataset/{dataset_id}/reset") 
async def reset_dataset(dataset_id: str): 
    """Reset to original data""" 
    ds = get_dataset_or_404(dataset_id) 
     
    ds["current"] = ds["original"].copy() 
    ds["processed"] = None 
    ds["identities"] = None 
    ds["history"] = [] 
     
    return { 
        "status": "reset", 
        "dataset_id": dataset_id, 
        "shape": ds["current"].shape 
    } 
 
 
 
# VISUALIZATION ENDPOINTS 
 

def identify_column_types(df: pd.DataFrame) -> Dict[str, List[str]]:
    """
    Identify numeric and categorical columns robustly.
    Handles dirty data where numeric columns might be read as objects.
    """
    numeric_cols = []
    categorical_cols = []
    
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            numeric_cols.append(col)
        else:
            # Check if object column is effectively numeric
            # Try converting to numeric, coerce errors to NaN
            try:
                converted = pd.to_numeric(df[col], errors='coerce')
                # If abundant valid numbers (>80%), treat as numeric
                # This handles currency ($10), commas (1,000), etc if pandas can parse them 
                # (Note: pd.to_numeric doesn't handle currency symbols by default without cleaning, 
                # but it handles strings of numbers. For currency, we accept that they might start as 0 
                # in the visualization if not cleaned, but we want to SHOW them in the dropdown at least)
                
                # Actually, standard pd.to_numeric won't handle '$15'. It becomes NaN.
                # So if we have ['$15', '10', '20'], it becomes [NaN, 10, 20]. 
                # 66% valid. So threshold should be lenient.
                valid_ratio = converted.notna().mean()
                if valid_ratio > 0.5: 
                    numeric_cols.append(col)
                else:
                    categorical_cols.append(col)
            except:
                categorical_cols.append(col)
                
    return {
        "numeric": numeric_cols,
        "categorical": categorical_cols,
        "all": df.columns.tolist()
    }

@app.get("/dataset/{dataset_id}/visualization/types") 
async def list_visualization_types(dataset_id: str): 
    """Get available visualization types""" 
    ds = get_dataset_or_404(dataset_id) 
     
    viz_types = get_visualization_types() 
    suggestions = generate_viz_suggestions(ds["current"]) 
    
    # Use robust column detection
    col_types = identify_column_types(ds["current"])
     
    return { 
        "dataset_id": dataset_id, 
        "available_visualizations": viz_types, 
        "suggestions": suggestions, 
        "current_columns": col_types
    } 
 
 
@app.post("/dataset/{dataset_id}/visualize") 
async def create_visualization( 
    dataset_id: str, 
    request: VisualizationRequest 
): 
    """Create visualization based on chart type""" 
    ds = get_dataset_or_404(dataset_id) 
    df = ds["current"] 
    
    if df.empty:
        raise HTTPException(400, "The dataset (or filtered result) is empty. Please adjust your filters or upload a valid dataset.")

     
    try: 
        chart_type = request.chart_type.lower() 
        params = request.parameters 
         
        if chart_type == "line_chart": 
            # Support both y_columns (new) and y_column (legacy)
            y_cols = params.get("y_columns")
            if not y_cols and "y_column" in params:
                 y_cols = [params["y_column"]]
            
            if not y_cols:
                raise HTTPException(400, "Missing y_columns. Please select at least one column for Y-axis.")

            img_data = create_line_chart( 
                df, 
                x_col=params["x_column"], 
                y_cols=y_cols, 
                title=request.title or f"Line Chart: {params['x_column']} vs {', '.join(y_cols)}", 
                figsize=request.figsize or (12, 6) 
            ) 
             
        elif chart_type == "bar_chart": 
            # Support both y_columns (new) and y_column (legacy)
            y_cols = params.get("y_columns")
            if not y_cols and "y_column" in params:
                 y_cols = [params["y_column"]]
            
            if not y_cols:
                raise HTTPException(400, "Missing y_columns. Please select at least one column for Y-axis.")
                
            img_data = create_bar_chart( 
                df, 
                x_col=params["x_column"], 
                y_cols=y_cols, 
                group_col=params.get("group_column"), 
                title=request.title or f"Bar Chart: {y_cols} by {params['x_column']}", 
                figsize=request.figsize or (10, 6) 
            ) 
             
        elif chart_type == "scatter_plot": 
            if "x_column" not in params or "y_column" not in params:
                 raise HTTPException(400, "Scatter plot requires both x_column and y_column")
            
            img_data = create_scatter_plot( 
                df, 
                x_col=params["x_column"], 
                y_col=params["y_column"], 
                color_col=params.get("color_column"), 
                size_col=params.get("size_column"), 
                title=request.title or f"Scatter Plot: {params['y_column']} vs {params['x_column']}", 
                figsize=request.figsize or (10, 8) 
            ) 
             
        elif chart_type == "histogram": 
            if "column" not in params:
                raise HTTPException(400, "Histogram requires a 'column' parameter")
                
            img_data = create_histogram( 
                df, 
                column=params["column"], 
                bins=int(params.get("bins", 20)), 
                title=request.title or f"Histogram: {params['column']}", 
                figsize=request.figsize or (10, 6) 
            ) 
             
        elif chart_type == "box_plot": 
            if "category_column" not in params or "value_column" not in params:
                raise HTTPException(400, "Box plot requires category_column and value_column")
                
            img_data = create_box_plot( 
                df, 
                category_col=params["category_column"], 
                value_col=params["value_column"], 
                title=request.title or f"Box Plot: {params['value_column']} by {params['category_column']}", 
                figsize=request.figsize or (12, 6) 
            ) 
             
        elif chart_type == "heatmap": 
            columns = params.get("columns") or df.select_dtypes(include=[np.number]).columns.tolist()[:10] 
            if not columns:
                raise HTTPException(400, "Heatmap requires numeric columns, but none found.")
                
            img_data = create_heatmap( 
                df, 
                columns=columns, 
                title=request.title or "Correlation Heatmap", 
                figsize=request.figsize or (10, 8) 
            ) 
             
        elif chart_type == "pie_chart": 
            if "column" not in params or "value_column" not in params:
                 raise HTTPException(400, "Pie chart requires 'column' (category) and 'value_column'")
                 
            img_data = create_pie_chart( 
                df, 
                column=params["column"], 
                value_col=params["value_column"], 
                top_n=int(params.get("top_n", 10)), 
                title=request.title or f"Pie Chart: {params['value_column']} by {params['column']}", 
                figsize=request.figsize or (8, 8) 
            ) 
             
        elif chart_type == "time_series": 
            if "date_column" not in params or "value_columns" not in params:
                raise HTTPException(400, "Time series requires date_column and value_columns")
                
            img_data = create_time_series( 
                df, 
                date_col=params["date_column"], 
                value_cols=params["value_columns"], 
                freq=params.get("frequency", "M"), 
                title=request.title or "Time Series Analysis", 
                figsize=request.figsize or (14, 7) 
            ) 
             
        elif chart_type == "summary_dashboard": 
            dashboard = create_summary_dashboard(df) 
            return { 
                "status": "success", 
                "dataset_id": dataset_id, 
                "chart_type": "summary_dashboard", 
                "dashboard": dashboard 
            } 
             
        elif chart_type == "treemap": 
            # Treemap returns data, not image 
            treemap_data = create_treemap_data( 
                df, 
                path_cols=params["path_columns"], 
                value_col=params["value_column"] 
            ) 
            return { 
                "status": "success", 
                "dataset_id": dataset_id, 
                "chart_type": "treemap", 
                "data": treemap_data 
            } 
             
        else: 
            raise HTTPException(400, f"Unknown chart type: {chart_type}") 
         
        # Save to history 
        ds["history"].append({ 
            "operation": "visualize", 
            "timestamp": pd.Timestamp.now().isoformat(), 
            "chart_type": chart_type, 
            "parameters": params 
        }) 
         
        return { 
            "status": "success", 
            "dataset_id": dataset_id, 
            "chart_type": chart_type, 
            "image_data": img_data, 
            "image_format": "base64_png", 
            "instructions": "Use data:image/png;base64,{image_data} in HTML img tag" 
        } 
         
    except Exception as e: 
        traceback.print_exc() 
        raise HTTPException(500, f"Visualization failed: {str(e)}") 


# DASHBOARD CONFIGURATION

@app.get("/dataset/{dataset_id}/dashboard/config")
async def get_dashboard_config(dataset_id: str):
    """Get saved dashboard layout"""
    ds = get_dataset_or_404(dataset_id)
    return {
        "dataset_id": dataset_id,
        "config": ds.get("dashboard_config", [])
    }

class DashboardConfigModel(BaseModel):
    config: List[Dict[str, Any]]

@app.post("/dataset/{dataset_id}/dashboard/config")
async def save_dashboard_config(dataset_id: str, request: DashboardConfigModel):
    """Save dashboard layout"""
    ds = get_dataset_or_404(dataset_id)
    ds["dashboard_config"] = request.config
    return {"status": "success", "message": "Dashboard saved", "count": len(request.config)} 
 
 
@app.get("/dataset/{dataset_id}/dashboard") 
async def get_data_dashboard(dataset_id: str): 
    """Get comprehensive data dashboard""" 
    ds = get_dataset_or_404(dataset_id) 
     
    try: 
        dashboard = create_summary_dashboard(ds["current"]) 
         
        return { 
            "status": "success", 
            "dataset_id": dataset_id, 
            "dashboard": dashboard, 
            "current_shape": ds["current"].shape, 
            "metadata": { 
                "numeric_columns": len(ds["current"].select_dtypes(include=[np.number]).columns), 
                "categorical_columns": len(ds["current"].select_dtypes(include=['object', 'category']).columns), 
                "total_rows": len(ds["current"]) 
            } 
        } 
         
    except Exception as e: 
        traceback.print_exc() 
        raise HTTPException(500, f"Dashboard creation failed: {str(e)}") 
 
 
 
# AI ANALYST

class ChatRequest(BaseModel):
    query: str

@app.post("/dataset/{dataset_id}/chat")
async def chat_with_data(dataset_id: str, request: ChatRequest):
    """Chat with the dataset (AI Analyst)"""
    ds = get_dataset_or_404(dataset_id)
    df = ds["current"]
    
    try:
        response = process_chat_query(df, request.query)
        return response
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"Chat processing failed: {str(e)}")


# ADVANCED TRANSFORMATION

class TransformRequest(BaseModel):
    operation: str # filter, sort, formula, rename
    params: Dict[str, Any]


def local_apply_transformation(df: pd.DataFrame, operation: str, params: Dict[str, Any]) -> pd.DataFrame:
    df_new = df.copy()
    if operation == "filter":
        col = params.get("column")
        op = params.get("operator")
        val = params.get("value")
        # Basic type inference for value
        if df_new[col].dtype != 'object':
             try: val = float(val) 
             except: pass
        
        if op == "==": df_new = df_new[df_new[col] == val]
        elif op == ">": df_new = df_new[df_new[col] > val]
        elif op == "<": df_new = df_new[df_new[col] < val]
        
    elif operation == "sort":
        col = params.get("column")
        asc = params.get("ascending", True)
        df_new = df_new.sort_values(by=col, ascending=asc)
        
    elif operation == "formula":
        new_col = params.get("new_column")
        expr = params.get("expression")
        if not new_col or not expr: raise ValueError("Missing params")
        # Use Python engine for formula
        df_new[new_col] = df_new.eval(expr, engine='python')
        
    elif operation == "rename":
        mapping = params.get("mapping")
        df_new = df_new.rename(columns=mapping)
        
    return df_new

@app.post("/dataset/{dataset_id}/transform")
async def transform_dataset(dataset_id: str, request: TransformRequest):
    """Apply advanced transformation"""
    print("API: Transform Request Received") # simplified print
    ds = get_dataset_or_404(dataset_id)
    
    try:
        print("API: Running local_apply_transformation...")
        new_df = local_apply_transformation(ds["current"], request.operation, request.params)
        
        # Save history
        ds["history"].append({
            "operation": request.operation,
            "timestamp": pd.Timestamp.now().isoformat(),
            "params": request.params
        })
        
        ds["current"] = new_df
        
        return {
            "status": "success", 
            "message": f"Operation {request.operation} completed",
            "rows": len(new_df),
            "columns": len(new_df.columns)
        }
    except ValueError as e:
        raise HTTPException(400, f"{str(e)}")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"Transformation failed: {str(e)}")

@app.get("/dataset/{dataset_id}/report")
async def download_report(dataset_id: str):
    """Download PDF Report"""
    ds = get_dataset_or_404(dataset_id)
    try:
        pdf_bytes = generate_pdf_summary(ds["current"], title=f"Report: {dataset_id}")
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={dataset_id}_report.pdf"
            }
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"Report generation failed: {str(e)}")


# EXPORT 
 
@app.get("/dataset/{dataset_id}/export") 
async def export_dataset( 
    dataset_id: str, 
    format: str = Query("excel", enum=["excel", "csv", "json"]) 
): 
    """Export dataset""" 
    ds = get_dataset_or_404(dataset_id) 
     
    try: 
        if format == "csv": 
            # Export current data as CSV 
            csv_buffer = io.StringIO() 
            ds["current"].to_csv(csv_buffer, index=False) 
            csv_data = csv_buffer.getvalue() 
            csv_buffer.close() 
             
            return StreamingResponse( 
                io.BytesIO(csv_data.encode()), 
                media_type="text/csv", 
                headers={ 
                    "Content-Disposition": f"attachment; filename={dataset_id}_export.csv" 
                } 
            ) 
         
        elif format == "json": 
            # Export as JSON 
            json_data = ds["current"].to_json(orient="records", date_format="iso") 
             
            return JSONResponse( 
                content=json.loads(json_data), 
                headers={ 
                    "Content-Disposition": f"attachment; filename={dataset_id}_export.json" 
                } 
            ) 
         
        else:  # Excel 
            # Create Excel with multiple sheets 
            excel_buffer = io.BytesIO() 
            with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer: 
                # Always include current data 
                ds["current"].to_excel(writer, index=False, sheet_name="Current_Data") 
                 
                # Include original 
                ds["original"].to_excel(writer, index=False, sheet_name="Original_Data") 
                 
                # Include identities if available 
                if ds.get("identities") is not None: 
                    ds["identities"].to_excel(writer, index=False, sheet_name="Identities") 
                 
                # Include history 
                if ds["history"]: 
                    history_df = pd.DataFrame(ds["history"]) 
                    history_df.to_excel(writer, index=False, sheet_name="Operation_History") 
             
            excel_data = excel_buffer.getvalue() 
            excel_buffer.close() 
             
            return StreamingResponse( 
                io.BytesIO(excel_data), 
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                headers={ 
                    "Content-Disposition": f"attachment; filename={dataset_id}_export.xlsx" 
                } 
            ) 
             
    except Exception as e: 
        traceback.print_exc() 
        raise HTTPException(500, f"Export failed: {str(e)}") 
 
 
 
# BACKWARD COMPATIBILITY - original commands 
 
@app.post("/command") 
async def run_command(cmd: dict): 
    """ 
    Backward compatibility endpoint for original command syntax 
    Example: {"dataset_id": "ds_0001", "command": "melt"} 
    """ 
    dataset_id = cmd.get("dataset_id") 
    command = cmd.get("command", "") 
     
    if not dataset_id or not command: 
        raise HTTPException(400, "Missing dataset_id or command") 
     
    ds = get_dataset_or_404(dataset_id) 
     
    # Parse command 
    import shlex 
    tokens = shlex.split(command) 
    if not tokens: 
        raise HTTPException(400, "Empty command") 
     
    op = tokens[0].lower() 
     
    try: 
        if op == "melt": 
            # Parse optional id_cols 
            args = {} 
            for token in tokens[1:]: 
                if "=" in token: 
                    key, value = token.split("=", 1) 
                    args[key.strip()] = value.strip() 
             
            melt_request = MeltRequest(auto_detect=True) 
            if "id_cols" in args: 
                melt_request.id_cols = [c.strip() for c in args["id_cols"].split(",")] 
                melt_request.auto_detect = False 
             
            return await melt_dataset(dataset_id, melt_request) 
         
        elif op == "pivot_measures": 
            # Parse core argument 
            args = {} 
            for token in tokens[1:]: 
                if "=" in token: 
                    key, value = token.split("=", 1) 
                    args[key.strip()] = value.strip() 
             
            if "core" not in args: 
                raise HTTPException(400, "Missing 'core' argument") 
             
            core_cols = [c.strip() for c in args["core"].split(",")] 
            pivot_request = PivotMeasuresRequest(core_cols=core_cols) 
             
            return await pivot_measures_dataset(dataset_id, pivot_request) 
         
        elif op == "export": 
            # Parse format and filename 
            args = {} 
            for token in tokens[1:]: 
                if "=" in token: 
                    key, value = token.split("=", 1) 
                    args[key.strip()] = value.strip() 
             
            format_type = args.get("format", "excel").lower() 
            return await export_dataset(dataset_id, format=format_type) 
         
        elif op == "clear": 
            # Clear processed data 
            return await reset_dataset(dataset_id) 
         
        else: 
            raise HTTPException(400, f"Unknown command: {op}") 
     
    except Exception as e: 
        traceback.print_exc() 
        raise HTTPException(500, f"Command failed: {str(e)}") 
 
 
 
# ROOT & DOCUMENTATION 
 
@app.get("/") 
async def root(): 
    """Serve frontend or API documentation if requested via API client"""
    if os.path.exists("static/index.html"):
        return FileResponse("static/index.html")
        
    return { 
        "message": "Universal Data Processor API", 
        "version": "2.0.0", 
        "description": "Transform any dataset: Melt wide→long, Pivot measures→headers", 
        "endpoints": { 
            "POST /upload": "Upload CSV/Excel file", 
            "GET /datasets": "List all datasets", 
            "GET /dataset/{id}": "Get dataset info", 
            "GET /dataset/{id}/view": "View data rows", 
            "GET /dataset/{id}/summary": "Get statistics", 
            "GET /dataset/{id}/suggestions": "Get operation suggestions", 
            "GET /dataset/{id}/visualization/types": "Get visualization options", 
            "POST /dataset/{id}/visualize": "Create visualizations", 
            "GET /dataset/{id}/dashboard": "Get data dashboard", 
            "POST /dataset/{id}/melt": "Convert wide to long format", 
            "POST /dataset/{id}/pivot_measures": "Pivot measures to headers", 
            "POST /dataset/{id}/pivot": "Flexible pivot operation", 
            "POST /dataset/{id}/clean": "Clean data", 
            "POST /dataset/{id}/undo": "Undo operations", 
            "POST /dataset/{id}/reset": "Reset to original", 
            "GET /dataset/{id}/export": "Export data", 
            "POST /command": "Backward compatibility endpoint", 
            "DELETE /dataset/{id}": "Delete dataset" 
        } 
    } 
 
 
 
# ERROR HANDLERS 
 
@app.exception_handler(HTTPException) 
async def http_exception_handler(request, exc): 
    return JSONResponse( 
        status_code=exc.status_code, 
        content={ 
            "error": exc.detail, 
            "status_code": exc.status_code, 
            "endpoint": str(request.url) 
        } 
    ) 
 
 
@app.exception_handler(Exception) 
async def general_exception_handler(request, exc): 
    traceback.print_exc() 
    return JSONResponse( 
        status_code=500, 
        content={ 
            "error": "Internal server error", 
            "details": str(exc), 
            "endpoint": str(request.url) 
        } 
    ) 
