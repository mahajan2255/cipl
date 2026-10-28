import React, { useState, useEffect } from 'react';
import { Play, RotateCcw, Save, Download, Info, Calculator } from 'lucide-react';
import {
  meltDataset,
  pivotMeasures,
  flexiblePivot,
  cleanDataset,
  undoOperation,
  resetDataset,
  getSuggestions,
  transformDataset
} from '../api';
import { clsx } from 'clsx';

const Operations = ({ datasetId, onOperationComplete }) => {
  const [activeTab, setActiveTab] = useState('melt');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [suggestions, setSuggestions] = useState(null);

  // Forms State
  const [meltConfig, setMeltConfig] = useState({ auto_detect: true, id_cols: '', period_cols: '', value_name: 'Value' });
  const [pivotMConfig, setPivotMConfig] = useState({ core_cols: '', period_col: 'Period', measure_col: 'Measure', value_col: 'Value' });
  const [flexPivotConfig, setFlexPivotConfig] = useState({ index_cols: '', columns_col: '', values_col: '', aggfunc: 'sum' });
  const [cleanConfig, setCleanConfig] = useState({ operations: ['fill_nulls', 'remove_duplicates'] });
  const [formulaConfig, setFormulaConfig] = useState({ new_column: '', expression: '' });

  // Advanced State
  const [filterConfig, setFilterConfig] = useState({ column: '', operator: '==', value: '' });
  const [sortConfig, setSortConfig] = useState({ column: '', ascending: true });

  useEffect(() => {
    if (datasetId) {
      loadSuggestions();
    }
  }, [datasetId]);

  const loadSuggestions = async () => {
    try {
      const result = await getSuggestions(datasetId);
      setSuggestions(result.suggestions);
    } catch (err) {
      console.error("Failed to load suggestions", err);
    }
  };

  const handleOperation = async (operationFn, config) => {
    setLoading(true);
    setMessage(null);
    try {
      const result = await operationFn(datasetId, config);
      setMessage({ type: 'success', text: 'Operation completed successfully!' });
      onOperationComplete();
      loadSuggestions(); // Refresh suggestions
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || "Operation failed";
      // If errorMsg is an object (validation error), stringify it
      const finalText = typeof errorMsg === 'object' ? JSON.stringify(errorMsg) : errorMsg;
      setMessage({ type: 'error', text: finalText });
    } finally {
      setLoading(false);
    }
  };

  const parseList = (str) => str.split(',').map(s => s.trim()).filter(Boolean);

  const executeMelt = () => {
    const config = { ...meltConfig };
    if (!config.auto_detect) {
      config.id_cols = parseList(config.id_cols);
      config.period_cols = parseList(config.period_cols);
    } else {
      // Remove empty strings if auto_detect is true to avoid validation errors
      delete config.id_cols;
      delete config.period_cols;
    }
    handleOperation(meltDataset, config);
  };

  const executePivotMeasures = () => {
    handleOperation(pivotMeasures, {
      ...pivotMConfig,
      core_cols: parseList(pivotMConfig.core_cols)
    });
  };

  const executeFlexPivot = () => {
    handleOperation(flexiblePivot, {
      ...flexPivotConfig,
      index_cols: parseList(flexPivotConfig.index_cols)
    });
  };

  const columns = suggestions?.column_analysis ? Object.keys(suggestions.column_analysis) : [];

  const executeClean = () => {
    handleOperation(cleanDataset, cleanConfig.operations);
  };

  const executeUndo = () => handleOperation(undoOperation, 1);
  const executeReset = () => handleOperation(resetDataset);

  const executeFilter = () => handleOperation(transformDataset, { operation: 'filter', params: filterConfig });
  const executeSort = () => handleOperation(transformDataset, { operation: 'sort', params: sortConfig });
  const executeFormula = () => handleOperation(transformDataset, { operation: 'formula', params: formulaConfig });

  const tabs = [
    { id: 'melt', label: 'Melt' },

    { id: 'formula', label: 'Calculated Columns' },
    { id: 'advanced', label: 'Filter & Sort' },
    { id: 'pivot_m', label: 'Pivot Measures' },
    { id: 'pivot', label: 'General Pivot' },
    { id: 'clean', label: 'Clean' }
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 overflow-x-auto pb-2 border-b border-zinc-800">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={clsx(
              "px-4 py-2 text-sm font-medium whitespace-nowrap rounded-lg transition-colors",
              activeTab === tab.id
                ? "bg-blue-600 text-white"
                : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800"
            )}
          >
            {tab.label}
          </button>
        ))}
        <div className="flex-1"></div>
        <button onClick={executeUndo} className="p-2 text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-md" title="Undo Last">
          <RotateCcw className="w-4 h-4" />
        </button>
        <button onClick={executeReset} className="p-2 text-red-400 hover:text-red-300 hover:bg-zinc-800 rounded-md" title="Reset All">
          <span className="text-xs font-bold">RESET</span>
        </button>
      </div>

      <div className="bg-zinc-900/50 rounded-xl p-6 border border-zinc-800/50 min-h-[300px]">
        {/* MELT TAB */}
        {activeTab === 'melt' && (
          <div className="space-y-4 max-w-lg">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium">Melt Operation</h3>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="auto_detect"
                  checked={meltConfig.auto_detect}
                  onChange={e => setMeltConfig({ ...meltConfig, auto_detect: e.target.checked })}
                  className="rounded border-zinc-700 bg-zinc-800 text-blue-600 focus:ring-blue-500"
                />
                <label htmlFor="auto_detect" className="text-sm text-zinc-300">Auto-detect columns</label>
              </div>
            </div>

            {!meltConfig.auto_detect && (
              <>
                <div>
                  <label className="block text-xs font-medium text-zinc-400 mb-1">ID Columns (comma separated)</label>
                  <input
                    type="text"
                    value={meltConfig.id_cols}
                    onChange={e => setMeltConfig({ ...meltConfig, id_cols: e.target.value })}
                    className="w-full bg-zinc-800 border-zinc-700 rounded-md text-sm p-2 focus:ring-1 focus:ring-blue-500 outline-none"
                    placeholder="e.g., Market, Product, Brand"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-zinc-400 mb-1">Period Columns (comma separated)</label>
                  <input
                    type="text"
                    value={meltConfig.period_cols}
                    onChange={e => setMeltConfig({ ...meltConfig, period_cols: e.target.value })}
                    className="w-full bg-zinc-800 border-zinc-700 rounded-md text-sm p-2 focus:ring-1 focus:ring-blue-500 outline-none"
                    placeholder="e.g., 2024Q1, 2024Q2"
                  />
                </div>
              </>
            )}
            <div>
              <label className="block text-xs font-medium text-zinc-400 mb-1">Value Column Name</label>
              <input
                type="text"
                value={meltConfig.value_name}
                onChange={e => setMeltConfig({ ...meltConfig, value_name: e.target.value })}
                className="w-full bg-zinc-800 border-zinc-700 rounded-md text-sm p-2 focus:ring-1 focus:ring-blue-500 outline-none"
              />
            </div>

            <div className="pt-4">
              <button
                onClick={executeMelt}
                disabled={loading}
                className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white py-2 rounded-lg font-medium transition-colors disabled:opacity-50"
              >
                {loading ? "Processing..." : "Run Melt"}
                {!loading && <Play className="w-4 h-4" />}
              </button>
            </div>

            {suggestions?.detection && (
              <div className="mt-4 p-4 bg-zinc-800/50 rounded-lg text-xs text-zinc-400">
                <p className="font-semibold text-zinc-300 mb-2 flex items-center gap-2">
                  <Info className="w-3 h-3" /> Auto-detection found:
                </p>
                <p>ID Cols: {suggestions.detection.id_cols.slice(0, 5).join(', ')}...</p>
                <p>Period Cols: {suggestions.detection.period_cols.slice(0, 5).join(', ')}...</p>
              </div>
            )}
          </div>
        )}

        {/* FORMULA TAB */}
        {activeTab === 'formula' && (
          <div className="space-y-4 max-w-lg">
            <h3 className="text-lg font-medium mb-4">Create Calculated Column</h3>
            <p className="text-sm text-zinc-400 mb-4">
              Create a new column using a mathematical expression.
              <br />
              <span className="text-yellow-500 font-mono text-xs">
                Important: Use backticks for column names with spaces! Example: `Revenue` - `Cost`
              </span>
            </p>

            <div>
              <label className="block text-xs font-medium text-zinc-400 mb-1">New Column Name</label>
              <input
                type="text"
                value={formulaConfig.new_column}
                onChange={e => setFormulaConfig({ ...formulaConfig, new_column: e.target.value })}
                className="w-full bg-zinc-800 border-zinc-700 rounded-md text-sm p-2 focus:ring-1 focus:ring-blue-500 outline-none"
                placeholder="e.g., Profit"
              />
            </div>

            {/* Column Suggestions */}
            {columns.length > 0 && (
              <div className="bg-zinc-800/40 p-3 rounded-md border border-zinc-700/50">
                <p className="text-xs text-zinc-400 mb-2 font-medium">Insert Column:</p>
                <div className="flex flex-wrap gap-2">
                  {columns.map(col => (
                    <button
                      key={col}
                      onClick={() => setFormulaConfig(prev => ({
                        ...prev,
                        expression: prev.expression + (prev.expression ? ' ' : '') + '`' + col + '`'
                      }))}
                      className="text-xs bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 hover:border-blue-500/50 px-2 py-1 rounded text-zinc-300 transition-colors"
                      title="Click to insert"
                    >
                      {col}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div>
              <label className="block text-xs font-medium text-zinc-400 mb-1">Expression</label>
              <div className="relative">
                <input
                  type="text"
                  value={formulaConfig.expression}
                  onChange={e => setFormulaConfig({ ...formulaConfig, expression: e.target.value })}
                  className="w-full bg-zinc-800 border-zinc-700 rounded-md text-sm p-2 focus:ring-1 focus:ring-blue-500 outline-none font-mono"
                  placeholder="e.g., `Revenue` - `Cost`"
                />
                <div className="absolute right-2 top-2 text-zinc-500">
                  <Calculator className="w-4 h-4" />
                </div>
              </div>
              <p className="text-xs text-zinc-500 mt-2">
                Use standard math operators (+, -, *, /).
              </p>
            </div>

            <div className="pt-4">
              <button
                onClick={executeFormula}
                disabled={loading || !formulaConfig.new_column || !formulaConfig.expression}
                className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md font-medium text-sm disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? (
                  <RotateCcw className="w-4 h-4 animate-spin" />
                ) : (
                  <Play className="w-4 h-4" />
                )}
                Calculate
              </button>
            </div>
          </div>
        )}





        {/* ADVANCED TAB */}
        {activeTab === 'advanced' && (
          <div className="space-y-6 max-w-lg">
            {/* Filter */}
            <div className="bg-zinc-800/30 p-4 rounded-lg border border-zinc-700/50">
              <h3 className="text-md font-medium mb-3">Filter Rows</h3>
              <div className="grid grid-cols-3 gap-2 mb-2">
                <select
                  value={filterConfig.column} onChange={e => setFilterConfig({ ...filterConfig, column: e.target.value })}
                  className="bg-zinc-800 border-zinc-700 rounded p-2 text-sm"
                >
                  <option value="">Column...</option>
                  {columns.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
                <select
                  value={filterConfig.operator} onChange={e => setFilterConfig({ ...filterConfig, operator: e.target.value })}
                  className="bg-zinc-800 border-zinc-700 rounded p-2 text-sm"
                >
                  <option value="==">Equals</option>
                  <option value="!=">Not Equals</option>
                  <option value=">">Greater</option>
                  <option value="<">Less</option>
                  <option value="contains">Contains</option>
                </select>
                <input
                  type="text" placeholder="Value"
                  value={filterConfig.value} onChange={e => setFilterConfig({ ...filterConfig, value: e.target.value })}
                  className="bg-zinc-800 border-zinc-700 rounded p-2 text-sm"
                />
              </div>
              <button onClick={executeFilter} disabled={loading} className="w-full bg-blue-600/20 hover:bg-blue-600 text-blue-400 hover:text-white py-1.5 rounded transition-colors text-sm">
                Apply Filter
              </button>
            </div>

            {/* Sort */}
            <div className="bg-zinc-800/30 p-4 rounded-lg border border-zinc-700/50">
              <h3 className="text-md font-medium mb-3">Sort Data</h3>
              <div className="flex gap-2 mb-2">
                <select
                  value={sortConfig.column} onChange={e => setSortConfig({ ...sortConfig, column: e.target.value })}
                  className="flex-1 bg-zinc-800 border-zinc-700 rounded p-2 text-sm"
                >
                  <option value="">Column...</option>
                  {columns.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
                <label className="flex items-center gap-2 text-sm text-zinc-300">
                  <input type="checkbox" checked={sortConfig.ascending} onChange={e => setSortConfig({ ...sortConfig, ascending: e.target.checked })} />
                  Ascending
                </label>
              </div>
              <button onClick={executeSort} disabled={loading} className="w-full bg-green-600/20 hover:bg-green-600 text-green-400 hover:text-white py-1.5 rounded transition-colors text-sm">
                Apply Sort
              </button>
            </div>
          </div>
        )}

        {/* PIVOT MEASURES TAB */}
        {activeTab === 'pivot_m' && (
          <div className="space-y-4 max-w-lg">
            <h3 className="text-lg font-medium mb-4">Pivot Measures to Headers</h3>
            <p className="text-sm text-zinc-400 mb-4">
              Convert a column containing measure names (e.g. "Metric") into multiple columns.
            </p>

            <div>
              <label className="block text-xs font-medium text-zinc-400 mb-1">Core Columns (comma separated)</label>
              <input
                type="text"
                value={pivotMConfig.core_cols}
                onChange={e => setPivotMConfig({ ...pivotMConfig, core_cols: e.target.value })}
                className="w-full bg-zinc-800 border-zinc-700 rounded-md text-sm p-2 focus:ring-1 focus:ring-blue-500 outline-none"
                placeholder="e.g., Market, Product"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-zinc-400 mb-1">Measure Column</label>
                <input
                  type="text"
                  value={pivotMConfig.measure_col}
                  onChange={e => setPivotMConfig({ ...pivotMConfig, measure_col: e.target.value })}
                  className="w-full bg-zinc-800 border-zinc-700 rounded-md text-sm p-2 focus:ring-1 focus:ring-blue-500 outline-none"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-zinc-400 mb-1">Value Column</label>
                <input
                  type="text"
                  value={pivotMConfig.value_col}
                  onChange={e => setPivotMConfig({ ...pivotMConfig, value_col: e.target.value })}
                  className="w-full bg-zinc-800 border-zinc-700 rounded-md text-sm p-2 focus:ring-1 focus:ring-blue-500 outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-zinc-400 mb-1">Period Column</label>
              <input
                type="text"
                value={pivotMConfig.period_col}
                onChange={e => setPivotMConfig({ ...pivotMConfig, period_col: e.target.value })}
                className="w-full bg-zinc-800 border-zinc-700 rounded-md text-sm p-2 focus:ring-1 focus:ring-blue-500 outline-none"
              />
            </div>

            <div className="pt-4">
              <button
                onClick={executePivotMeasures}
                disabled={loading}
                className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white py-2 rounded-lg font-medium transition-colors disabled:opacity-50"
              >
                {loading ? "Processing..." : "Run Pivot Measures"}
                {!loading && <Play className="w-4 h-4" />}
              </button>
            </div>
          </div>
        )}

        {/* GENERAL PIVOT TAB */}
        {activeTab === 'pivot' && (
          <div className="space-y-4 max-w-lg">
            <h3 className="text-lg font-medium mb-4">General Pivot Table</h3>

            <div>
              <label className="block text-xs font-medium text-zinc-400 mb-1">Index Columns (Rows)</label>
              <select
                multiple
                value={flexPivotConfig.index_cols ? flexPivotConfig.index_cols.split(',').map(s => s.trim()).filter(Boolean) : []}
                onChange={e => {
                  const selected = Array.from(e.target.selectedOptions, option => option.value);
                  setFlexPivotConfig({ ...flexPivotConfig, index_cols: selected.join(',') });
                }}
                className="w-full bg-zinc-800 border-zinc-700 rounded-md text-sm p-2 focus:ring-1 focus:ring-blue-500 outline-none h-32"
              >
                {columns.map(col => (
                  <option key={col} value={col}>{col}</option>
                ))}
              </select>
              <p className="text-xs text-zinc-500 mt-1">Hold Ctrl/Cmd to select multiple</p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-zinc-400 mb-1">Columns (Headers)</label>
                <select
                  value={flexPivotConfig.columns_col}
                  onChange={e => setFlexPivotConfig({ ...flexPivotConfig, columns_col: e.target.value })}
                  className="w-full bg-zinc-800 border-zinc-700 rounded-md text-sm p-2 focus:ring-1 focus:ring-blue-500 outline-none"
                >
                  <option value="">Select Column...</option>
                  {columns.map(col => (
                    <option key={col} value={col}>{col}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-zinc-400 mb-1">Values</label>
                <select
                  value={flexPivotConfig.values_col}
                  onChange={e => setFlexPivotConfig({ ...flexPivotConfig, values_col: e.target.value })}
                  className="w-full bg-zinc-800 border-zinc-700 rounded-md text-sm p-2 focus:ring-1 focus:ring-blue-500 outline-none"
                >
                  <option value="">Select Column...</option>
                  {columns.map(col => (
                    <option key={col} value={col}>{col}</option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-zinc-400 mb-1">Aggregation Function</label>
              <select
                value={flexPivotConfig.aggfunc}
                onChange={e => setFlexPivotConfig({ ...flexPivotConfig, aggfunc: e.target.value })}
                className="w-full bg-zinc-800 border-zinc-700 rounded-md text-sm p-2 focus:ring-1 focus:ring-blue-500 outline-none"
              >
                <option value="sum">Sum</option>
                <option value="mean">Mean (Average)</option>
                <option value="count">Count</option>
                <option value="min">Min</option>
                <option value="max">Max</option>
                <option value="first">First</option>
              </select>
            </div>

            <div className="pt-4">
              <button
                onClick={executeFlexPivot}
                disabled={loading}
                className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white py-2 rounded-lg font-medium transition-colors disabled:opacity-50"
              >
                {loading ? "Processing..." : "Run Pivot"}
                {!loading && <Play className="w-4 h-4" />}
              </button>
            </div>
          </div>
        )}

        {/* CLEAN TAB */}
        {activeTab === 'clean' && (
          <div className="space-y-4 max-w-lg">
            <h3 className="text-lg font-medium mb-4">Data Cleaning</h3>

            <div className="space-y-3">
              {['fill_nulls', 'remove_duplicates', 'convert_types', 'standardize_text'].map(op => (
                <label key={op} className="flex items-center gap-3 p-3 bg-zinc-800/50 rounded-lg cursor-pointer hover:bg-zinc-800 transition-colors">
                  <input
                    type="checkbox"
                    checked={cleanConfig.operations.includes(op)}
                    onChange={e => {
                      const newOps = e.target.checked
                        ? [...cleanConfig.operations, op]
                        : cleanConfig.operations.filter(o => o !== op);
                      setCleanConfig({ operations: newOps });
                    }}
                    className="rounded border-zinc-600 bg-zinc-700 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm font-medium text-zinc-200 capitalize">{op.replace('_', ' ')}</span>
                </label>
              ))}
            </div>

            <div className="pt-4">
              <button
                onClick={executeClean}
                disabled={loading}
                className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white py-2 rounded-lg font-medium transition-colors disabled:opacity-50"
              >
                {loading ? "Processing..." : "Clean Data"}
                {!loading && <Play className="w-4 h-4" />}
              </button>
            </div>
          </div>
        )}

        {/* EXPORT TAB */}

      </div>

      {message && (
        <div className={clsx(
          "p-4 rounded-lg flex items-center gap-3",
          message.type === 'error' ? "bg-red-500/10 text-red-400 border border-red-500/20" : "bg-green-500/10 text-green-400 border border-green-500/20"
        )}>
          <Info className="w-5 h-5" />
          {message.text}
        </div>
      )}
    </div>
  );
};

// Helper icons
const FileSpreadsheet = (props) => (
  <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" /><polyline points="14 2 14 8 20 8" /><path d="M8 13h2" /><path d="M8 17h2" /><path d="M14 13h2" /><path d="M14 17h2" /></svg>
);
const FileText = (props) => (
  <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" /><polyline points="14 2 14 8 20 8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" /><line x1="10" y1="9" x2="8" y2="9" /></svg>
);

export default Operations;
