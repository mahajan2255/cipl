import React, { useState, useEffect } from 'react';
import { getVizTypes, createVisualization } from '../api';
import { BarChart, LineChart, PieChart, Activity, Grid, Box, Image, Loader2, Maximize2, Download } from 'lucide-react';
import { clsx } from 'clsx';

const Visualization = ({ datasetId }) => {
    const [vizTypes, setVizTypes] = useState({});
    const [columns, setColumns] = useState({ numeric: [], categorical: [], all: [] });
    const [selectedType, setSelectedType] = useState('line_chart');
    // Default to larger figure size
    const [params, setParams] = useState({ figsize: [12, 8] });
    const [loading, setLoading] = useState(false);
    const [chartImage, setChartImage] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (datasetId) {
            loadVizOptions();
            setChartImage(null);
            setParams({});
        }
    }, [datasetId]);

    const loadVizOptions = async () => {
        try {
            const result = await getVizTypes(datasetId);
            setVizTypes(result.available_visualizations);
            setColumns(result.current_columns);
        } catch (err) {
            console.error("Failed to load visualization options", err);
        }
    };

    const handleGenerate = async () => {
        setLoading(true);
        setError(null);
        try {
            const result = await createVisualization(datasetId, selectedType, params);
            if (result.chart_type === 'treemap') {
                // Treemap returns data, not image in this API. 
                // For now, we'll just show a message or handle it if we implemented a client-side treemap.
                setError("Treemap visualization is currently data-only.");
            } else {
                setChartImage(`data:image/png;base64,${result.image_data}`);
            }
        } catch (err) {
            setError(err.response?.data?.detail || "Failed to generate visualization");
        } finally {
            setLoading(false);
        }
    };

    const handleDownloadChart = () => {
        if (!chartImage) return;
        const link = document.createElement('a');
        link.href = chartImage;
        link.download = `visualization_${datasetId}_${selectedType}.png`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    const updateParam = (key, value) => {
        // Handle multiple selects
        if (Array.isArray(value)) {
            setParams(prev => ({ ...prev, [key]: value }));
        } else {
            setParams(prev => ({ ...prev, [key]: value }));
        }
    };

    const renderParamInput = (key, typeParams) => {
        // Infer input type based on parameter name
        const isMulti = key.endsWith('s') && key !== 'bins'; // e.g. y_columns
        const isNumeric = key === 'bins' || key === 'top_n';

        // Determine options based on likely required column type
        let options = columns.all;
        if (['y_column', 'y_columns', 'value_column', 'value_columns', 'size_column'].includes(key)) {
            options = columns.numeric;
        } else if (['category_column', 'group_column', 'color_column'].includes(key)) {
            options = columns.categorical.length > 0 ? columns.categorical : columns.all;
        } else if (['date_column'].includes(key)) {
            options = columns.all; // Date might be object or datetime
        }

        if (isNumeric) {
            return (
                <input
                    type="number"
                    className="w-full bg-zinc-800 border-zinc-700 rounded-md p-2 text-sm"
                    onChange={e => updateParam(key, parseInt(e.target.value))}
                    placeholder={key}
                />
            );
        }

        if (isMulti) {
            return (
                <select
                    multiple
                    className="w-full bg-zinc-800 border-zinc-700 rounded-md p-2 text-sm h-32"
                    onChange={e => updateParam(key, Array.from(e.target.selectedOptions, option => option.value))}
                >
                    {options.map(col => <option key={col} value={col}>{col}</option>)}
                </select>
            );
        }

        return (
            <select
                className="w-full bg-zinc-800 border-zinc-700 rounded-md p-2 text-sm"
                onChange={e => updateParam(key, e.target.value)}
                value={params[key] || ""}
            >
                <option value="">Select Column...</option>
                {options.map(col => <option key={col} value={col}>{col}</option>)}
            </select>
        );
    };

    const chartIcons = {
        line_chart: <LineChart className="w-5 h-5" />,
        bar_chart: <BarChart className="w-5 h-5" />,
        scatter_plot: <Activity className="w-5 h-5" />,
        histogram: <BarChart className="w-5 h-5 rotate-90" />,
        box_plot: <Box className="w-5 h-5" />,
        heatmap: <Grid className="w-5 h-5" />,
        pie_chart: <PieChart className="w-5 h-5" />,
        time_series: <Activity className="w-5 h-5" />,
        treemap: <Grid className="w-5 h-5" />,
        summary_dashboard: <Maximize2 className="w-5 h-5" />
    };

    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-1 space-y-6">
                <div className="grid grid-cols-2 gap-2">
                    {Object.keys(vizTypes).filter(k => k !== 'summary_dashboard').map(type => (
                        <button
                            key={type}
                            onClick={() => { setSelectedType(type); setParams({ figsize: [12, 8] }); setChartImage(null); }}
                            className={clsx(
                                "flex flex-col items-center justify-center p-4 rounded-lg border transition-all gap-2",
                                selectedType === type
                                    ? "bg-blue-600 border-blue-500 text-white shadow-lg scale-105"
                                    : "bg-zinc-800 border-zinc-700 text-zinc-400 hover:bg-zinc-700"
                            )}
                        >
                            {chartIcons[type] || <Image className="w-5 h-5" />}
                            <span className="text-xs font-medium capitalize">{type.replace('_', ' ')}</span>
                        </button>
                    ))}
                </div>

                {selectedType && vizTypes[selectedType] && (
                    <div className="bg-zinc-900/50 p-6 rounded-xl border border-zinc-800">
                        <h3 className="text-md font-medium mb-4 capitalize">{selectedType.replace('_', ' ')} Configuration</h3>
                        <p className="text-xs text-zinc-500 mb-4">{vizTypes[selectedType].description}</p>

                        <div className="space-y-4">
                            {vizTypes[selectedType].required_params.map(param => (
                                <div key={param}>
                                    <label className="block text-xs font-medium text-zinc-400 mb-1 capitalize">
                                        {param.replace('_', ' ')} <span className="text-red-400">*</span>
                                    </label>
                                    {renderParamInput(param)}
                                </div>
                            ))}

                            {vizTypes[selectedType].optional_params.filter(p => !['title', 'figsize'].includes(p)).map(param => (
                                <div key={param}>
                                    <label className="block text-xs font-medium text-zinc-400 mb-1 capitalize">
                                        {param.replace('_', ' ')} (Optional)
                                    </label>
                                    {renderParamInput(param)}
                                </div>
                            ))}

                            <div>
                                <label className="block text-xs font-medium text-zinc-400 mb-1">Chart Title</label>
                                <input
                                    type="text"
                                    className="w-full bg-zinc-800 border-zinc-700 rounded-md p-2 text-sm"
                                    onChange={e => updateParam('title', e.target.value)}
                                />
                            </div>

                            <button
                                onClick={handleGenerate}
                                disabled={loading}
                                className="w-full mt-4 bg-blue-600 hover:bg-blue-500 text-white py-2 rounded-lg font-medium transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                            >
                                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Generate Visualization"}
                            </button>
                        </div>
                    </div>
                )}
            </div>

            <div className="lg:col-span-2 bg-zinc-900/30 rounded-xl border border-zinc-800 flex flex-col items-center justify-center min-h-[600px] relative overflow-hidden">
                {chartImage && (
                    <div className="absolute top-4 right-4 z-10">
                        <button
                            onClick={handleDownloadChart}
                            className="p-2 bg-zinc-800/80 hover:bg-zinc-700 text-zinc-200 rounded-md border border-zinc-700 transition-colors flex items-center gap-2 text-xs"
                        >
                            <Download className="w-4 h-4" />
                            Download PNG
                        </button>
                    </div>
                )}
                {loading && (
                    <div className="absolute inset-0 bg-black/50 flex items-center justify-center backdrop-blur-sm">
                        <Loader2 className="w-10 h-10 text-blue-500 animate-spin" />
                    </div>
                )}

                {chartImage ? (
                    <div className="w-full h-full p-4 overflow-auto flex items-center justify-center">
                        <img src={chartImage} alt="Visualization" className="max-w-full max-h-full rounded-lg shadow-2xl" />
                    </div>
                ) : (
                    <div className="text-center text-zinc-600">
                        <Image className="w-16 h-16 mx-auto mb-4 opacity-20" />
                        <p>Select a chart type and parameters to generate a visualization</p>
                    </div>
                )}

                {error && (
                    <div className="absolute bottom-4 left-4 right-4 bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-lg text-sm">
                        {error}
                    </div>
                )}
            </div>
        </div>
    );
};

export default Visualization;
