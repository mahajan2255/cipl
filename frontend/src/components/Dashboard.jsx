import React, { useEffect, useState } from 'react';
import { getDashboard, getDashboardConfig, saveDashboardConfig, createVisualization } from '../api';
import { Loader2, Plus, Edit, X, Save, BarChart, Activity, PieChart, Box } from 'lucide-react';
import { clsx } from 'clsx';

const Dashboard = ({ datasetId }) => {
    const [dashboard, setDashboard] = useState(null);
    const [loading, setLoading] = useState(true);
    const [customCharts, setCustomCharts] = useState([]);
    const [isEditing, setIsEditing] = useState(false);

    // Adding Chart State
    const [isAdding, setIsAdding] = useState(false);
    const [newChart, setNewChart] = useState({ type: 'bar_chart', x: '', y: '' });

    useEffect(() => {
        if (datasetId) {
            fetchDashboard();
        }
    }, [datasetId]);

    const fetchDashboard = async () => {
        setLoading(true);
        try {
            const [dashResult, configResult] = await Promise.all([
                getDashboard(datasetId),
                getDashboardConfig(datasetId)
            ]);
            setDashboard(dashResult.dashboard);
            setCustomCharts(configResult.config || []);
        } catch (err) {
            console.error("Failed to fetch dashboard", err);
        } finally {
            setLoading(false);
        }
    };

    const handleSaveLayout = async () => {
        try {
            await saveDashboardConfig(datasetId, customCharts);
            setIsEditing(false);
        } catch (err) {
            console.error("Failed to save", err);
        }
    };

    const handleAddChart = () => {
        if (!newChart.x) return; // Basic validation

        const config = {
            id: Date.now().toString(),
            type: newChart.type,
            params: {
                x_column: newChart.x,
                y_column: newChart.y, // Can be empty for histograms
                title: `${newChart.type} of ${newChart.x}`
            }
        };

        // Map to API params
        if (newChart.type === 'bar_chart') {
            config.params = { category_column: newChart.x, value_column: newChart.y };
        } else if (newChart.type === 'line_chart') {
            config.params = { x_column: newChart.x, y_column: newChart.y };
        } else if (newChart.type === 'scatter_plot') {
            config.params = { x_column: newChart.x, y_column: newChart.y };
        } else if (newChart.type === 'histogram') {
            config.params = { value_column: newChart.x };
        } else if (newChart.type === 'box_plot') {
            config.params = { value_column: newChart.x, category_column: newChart.y };
        }

        setCustomCharts([...customCharts, config]);
        setIsAdding(false);
        setNewChart({ type: 'bar_chart', x: '', y: '' });
    };

    const handleRemoveChart = (id) => {
        setCustomCharts(customCharts.filter(c => c.id !== id));
    };

    if (loading) return <div className="flex justify-center p-12"><Loader2 className="animate-spin w-8 h-8 text-blue-500" /></div>;
    if (!dashboard) return null;

    const { summary_stats } = dashboard;
    const columns = summary_stats.columns;

    return (
        <div className="space-y-8">
            {/* Header & Controls */}
            <div className="flex justify-between items-center bg-zinc-900/50 p-4 rounded-xl border border-zinc-800 backdrop-blur-sm">
                <div>
                    <h2 className="text-xl font-bold text-white">Dashboard</h2>
                    <p className="text-xs text-zinc-500">Overview of {datasetId}</p>
                </div>
                <div className="flex items-center gap-2">
                    {isEditing ? (
                        <>
                            <button onClick={() => setIsAdding(true)} className="flex items-center gap-2 bg-zinc-800 hover:bg-zinc-700 text-white px-3 py-1.5 rounded-lg text-sm border border-zinc-700 transition-colors">
                                <Plus className="w-4 h-4" /> Add Chart
                            </button>
                            <button onClick={handleSaveLayout} className="flex items-center gap-2 bg-green-600 hover:bg-green-500 text-white px-3 py-1.5 rounded-lg text-sm transition-colors">
                                <Save className="w-4 h-4" /> Save
                            </button>
                        </>
                    ) : (
                        <button onClick={() => setIsEditing(true)} className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white px-3 py-1.5 rounded-lg text-sm transition-colors">
                            <Edit className="w-4 h-4" /> Customize
                        </button>
                    )}
                </div>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <StatCard label="Rows" value={summary_stats.shape[0]} />
                <StatCard label="Columns" value={summary_stats.shape[1]} />
                <StatCard label="Memory" value={`${summary_stats.memory_mb} MB`} />
                <StatCard label="Missing" value={Object.values(summary_stats.null_counts).reduce((a, b) => a + b, 0)} />
            </div>

            {/* Main Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Default Auto-Generated Visualizations */}
                {dashboard.visualizations.map((viz, idx) => (
                    <div key={`auto-${idx}`} className="bg-zinc-900 rounded-xl border border-zinc-800 overflow-hidden group">
                        <div className="p-4 border-b border-zinc-800 bg-zinc-800/30 flex justify-between items-start">
                            <h4 className="font-medium text-sm text-zinc-200">{viz.title}</h4>
                            <span className="text-[10px] text-zinc-500 bg-zinc-900 px-2 py-0.5 rounded border border-zinc-800">Auto</span>
                        </div>
                        <div className="p-4">
                            <img src={`data:image/png;base64,${viz.image_data}`} alt={viz.title} className="w-full h-auto rounded" />
                        </div>
                    </div>
                ))}

                {/* User Custom Charts */}
                {customCharts.map((chart) => (
                    <AsyncChart
                        key={chart.id}
                        datasetId={datasetId}
                        config={chart}
                        isEditing={isEditing}
                        onRemove={() => handleRemoveChart(chart.id)}
                    />
                ))}
            </div>

            {/* Add Chart Modal */}
            {isAdding && (
                <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 backdrop-blur-sm">
                    <div className="bg-zinc-900 p-6 rounded-xl border border-zinc-800 w-full max-w-md space-y-4">
                        <div className="flex justify-between items-center">
                            <h3 className="text-lg font-bold">Add Chart</h3>
                            <button onClick={() => setIsAdding(false)}><X className="w-5 h-5 text-zinc-400 hover:text-white" /></button>
                        </div>

                        <div className="space-y-3">
                            <div>
                                <label className="text-xs text-zinc-400 block mb-1">Chart Type</label>
                                <select
                                    value={newChart.type}
                                    onChange={e => setNewChart({ ...newChart, type: e.target.value })}
                                    className="w-full bg-zinc-800 border border-zinc-700 rounded p-2 text-sm"
                                >
                                    <option value="bar_chart">Bar Chart</option>
                                    <option value="line_chart">Line Chart</option>
                                    <option value="scatter_plot">Scatter Plot</option>
                                    <option value="histogram">Histogram</option>
                                    <option value="box_plot">Box Plot</option>
                                </select>
                            </div>

                            <div>
                                <label className="text-xs text-zinc-400 block mb-1">Primary Column (X-Axis/Category)</label>
                                <select
                                    value={newChart.x}
                                    onChange={e => setNewChart({ ...newChart, x: e.target.value })}
                                    className="w-full bg-zinc-800 border border-zinc-700 rounded p-2 text-sm"
                                >
                                    <option value="">Select Column...</option>
                                    {columns.map(c => <option key={c} value={c}>{c}</option>)}
                                </select>
                            </div>

                            {newChart.type !== 'histogram' && (
                                <div>
                                    <label className="text-xs text-zinc-400 block mb-1">Secondary Column (Y-Axis/Value)</label>
                                    <select
                                        value={newChart.y}
                                        onChange={e => setNewChart({ ...newChart, y: e.target.value })}
                                        className="w-full bg-zinc-800 border border-zinc-700 rounded p-2 text-sm"
                                    >
                                        <option value="">Select Column... (Optional for count)</option>
                                        {columns.map(c => <option key={c} value={c}>{c}</option>)}
                                    </select>
                                </div>
                            )}

                            <button onClick={handleAddChart} className="w-full bg-blue-600 hover:bg-blue-500 text-white py-2 rounded-lg font-medium mt-4">
                                Add to Dashboard
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

// Sub-component for Async Charts
const AsyncChart = ({ datasetId, config, isEditing, onRemove }) => {
    const [image, setImage] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const load = async () => {
            try {
                // Ensure figsize is consistent for grid
                const params = { ...config.params, figsize: [10, 6] };
                const res = await createVisualization(datasetId, config.type, params);
                setImage(res.image_data);
            } catch (err) {
                setError("Failed to load");
            } finally {
                setLoading(false);
            }
        };
        load();
    }, [datasetId, config]);

    return (
        <div className="bg-zinc-900 rounded-xl border border-zinc-800 overflow-hidden relative group hover:border-blue-500/30 transition-colors">
            <div className="p-4 border-b border-zinc-800 bg-zinc-800/30 flex justify-between items-center">
                <h4 className="font-medium text-sm text-zinc-200 truncate">{config.params.title || config.type}</h4>
                {isEditing && (
                    <button onClick={onRemove} className="text-red-400 hover:text-red-300 p-1 hover:bg-red-900/30 rounded">
                        <X className="w-3 h-3" />
                    </button>
                )}
            </div>
            <div className="p-4 min-h-[250px] flex items-center justify-center">
                {loading && <Loader2 className="w-6 h-6 animate-spin text-zinc-500" />}
                {error && <span className="text-xs text-red-400">{error}</span>}
                {image && <img src={`data:image/png;base64,${image}`} className="w-full h-auto rounded" />}
            </div>
        </div>
    );
};

const StatCard = ({ label, value }) => (
    <div className="bg-zinc-900 p-4 rounded-xl border border-zinc-800">
        <div className="text-zinc-500 text-xs uppercase font-medium mb-1">{label}</div>
        <div className="text-2xl font-bold text-white">{value}</div>
    </div>
);

export default Dashboard;
