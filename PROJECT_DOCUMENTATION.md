# DataProcessor Project Documentation

## Overview
**DataProcessor** (also referred to as "Analyst") is a universal data transformation and visualization platform designed to streamline the data analysis workflow. It allows users to upload raw datasets (CSV, Excel), perform complex data cleaning and reshaping operations, generate insightful visualizations, and interact with their data using an AI-powered chat interface.

## Key Features

### 1. Data Ingestion & Management
- **Universal Upload**: Supports CSV and Excel (.xlsx) file formats.
- **Auto-Detection**: robustly detects column types (numeric vs. categorical), handling "dirty" data effectively.
- **Dataset Management**: View, delete, and switch between multiple uploaded datasets.

### 2. Data Transformation
- **Melting**: Convert wide-format data to long-format for better analysis.
- **Pivoting**:
    - **Measure Pivoting**: Pivot measures to column headers without aggregation.
    - **Flexible Pivot**: Create standard pivot tables with customizable aggregation functions.
- **Cleaning**: Automated operations to fill nulls, remove duplicates, and ensure numeric types.
- **History Tracking**: Full undo/redo capabilities and reset functionality to revert to the original state.

### 3. Visualization
- **Rich Chart Library**:
    - Line Charts (Multi-line support)
    - Bar Charts (Grouped and Stacked)
    - Scatter Plots (with color/size encoding)
    - Histograms & Box Plots (Distribution analysis)
    - Heatmaps (Correlation analysis)
    - Pie Charts & Time Series
- **Auto-Dashboard**: Generate a comprehensive summary dashboard with a single click.
- **Interaction**: Zoom, download, and expanded views for charts.

### 4. AI Analyst
- **Chat Interface**: Natural language querying of datasets (e.g., "Show me the trend of sales over time").
- **Intelligent Response**: Returns both textual insights and automatically generated plots based on the query.

### 5. Export & Reporting
- **Multi-Format Export**: Export processed data to CSV, Excel, JSON, and PDF.
- **Dedicated Export View**: Streamlined interface for selecting export options.

## Technical Architecture

### Frontend
- **Framework**: React 19 (via Vite)
- **Styling**: Tailwind CSS v4, clsx, tailwind-merge
- **Icons**: Lucide React
- **Animations**: Framer Motion
- **HTTP Client**: Axios
- **Structure**:
    - `App.jsx`: Main routing and layout controller.
    - `components/`: Modular components for Upload, Data View, Operations, Visualization, Dashboard, and Export.
    - `api.js`: Centralized API service layer.

### Backend
- **Framework**: FastAPI (Python)
- **Server**: Uvicorn
- **Data Processing**: Pandas, NumPy
- **Excel Support**: OpenPyXL, XlsxWriter
- **Visualization**: Matplotlib, Seaborn (Base64 image generation)
- **AI/NLP**: Custom heuristic and rule-based query processing (`process_chat_query` in `ingest.py`).

## Project Structure
```
e:\analyst\
├── api\
│   └── api_server.py    # FastAPI application entry point, endpoints definition
├── app\
│   └── ingest.py        # Core logic: DataFrame operations, plotting, AI analysis
├── frontend\            # React application source code
├── uploads\             # Directory for storing uploaded datasets
├── static\              # Static assets serving
└── requirements.txt     # Python dependencies
```

## Setup & Running

### Prerequisites
- Python 3.8+
- Node.js & npm

### Backend Setup
1. Create a virtual environment:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the server:
   ```bash
   uvicorn api.api_server:app --reload --port 8007
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```

## Development Notes
- The backend runs on `http://localhost:8007`.
- The frontend proxy or API client is configured to communicate with this port.
- Visualizations are rendered server-side using Matplotlib (Agg backend) and sent as Base64 strings to the frontend.
