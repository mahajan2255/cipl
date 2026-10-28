import React, { useState } from 'react';
import { LayoutDashboard, Database, BarChart2, Settings, Layers, Menu } from 'lucide-react';
import { clsx } from 'clsx';
import Upload from './components/Upload';
import DatasetList from './components/DatasetList';
import DatasetView from './components/DatasetView';
import Operations from './components/Operations';
import Visualization from './components/Visualization';

import Dashboard from './components/Dashboard';
import ExportView from './components/ExportView';
import { Bot, Download } from 'lucide-react';

function App() {
  const [selectedDatasetId, setSelectedDatasetId] = useState(null);
  const [activeView, setActiveView] = useState('data'); // data, analysis, visualize, dashboard
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const refreshData = () => setRefreshTrigger(prev => prev + 1);

  const handleUploadSuccess = (result) => {
    refreshData();
    setSelectedDatasetId(result.dataset_id);
    setActiveView('data');
  };

  const menuItems = [
    { id: 'data', label: 'Data View', icon: <Database className="w-5 h-5" /> },
    { id: 'analysis', label: 'Transformations', icon: <Layers className="w-5 h-5" /> },
    { id: 'visualize', label: 'Visualization', icon: <BarChart2 className="w-5 h-5" /> },
    { id: 'dashboard', label: 'Auto Dashboard', icon: <LayoutDashboard className="w-5 h-5" /> },
    { id: 'export', label: 'Export', icon: <Download className="w-5 h-5" /> },

  ];

  return (
    <div className="flex h-screen bg-black text-white overflow-hidden">
      {/* Sidebar */}
      <div className="w-64 bg-zinc-900 border-r border-zinc-800 flex flex-col">
        <div className="p-6 border-b border-zinc-800">
          <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-teal-400 bg-clip-text text-transparent">
            DataProcessor
          </h1>
          <p className="text-xs text-zinc-500 mt-1">Universal Data Transformer</p>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {/* Main Navigation */}
          {selectedDatasetId && (
            <div className="space-y-1">
              <h2 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2 px-2">Workspace</h2>
              {menuItems.map((item) => (
                <button
                  key={item.id}
                  onClick={() => setActiveView(item.id)}
                  className={clsx(
                    "w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                    activeView === item.id
                      ? "bg-blue-600 text-white shadow-lg shadow-blue-900/20"
                      : "text-zinc-400 hover:text-white hover:bg-zinc-800"
                  )}
                >
                  {item.icon}
                  {item.label}
                </button>
              ))}
            </div>
          )}

          <DatasetList
            onSelect={setSelectedDatasetId}
            selectedId={selectedDatasetId}
            refreshTrigger={refreshTrigger}
          />
        </div>

        <div className="p-4 border-t border-zinc-800 text-xs text-zinc-500 flex justify-between">
          <span>v2.0.0</span>
          <span>Jules Agent</span>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="h-16 border-b border-zinc-800 bg-zinc-900/50 flex items-center px-8 justify-between backdrop-blur-sm">
          <h2 className="text-lg font-medium text-zinc-200">
            {selectedDatasetId ? (
              menuItems.find(m => m.id === activeView)?.label
            ) : "Welcome"}
          </h2>
          {selectedDatasetId && (
            <div className="flex items-center gap-2 text-xs bg-zinc-800 px-3 py-1.5 rounded-full border border-zinc-700">
              <span className="w-2 h-2 rounded-full bg-green-500"></span>
              <span className="text-zinc-300 font-mono">{selectedDatasetId}</span>
            </div>
          )}
        </header>

        {/* Content Area */}
        <main className="flex-1 overflow-y-auto p-8 scrollbar-thin scrollbar-thumb-zinc-700 scrollbar-track-transparent">
          {!selectedDatasetId ? (
            <div className="h-full flex flex-col items-center justify-center -mt-20">
              <div className="max-w-2xl w-full text-center space-y-8">
                <div className="space-y-2">
                  <h2 className="text-3xl font-bold text-white">Upload your dataset</h2>
                  <p className="text-zinc-400">Transform, clean, and visualize your data in seconds.</p>
                </div>
                <Upload onUploadSuccess={handleUploadSuccess} />
              </div>
            </div>
          ) : (
            <div className="max-w-7xl mx-auto">
              {activeView === 'data' && (
                <div className="space-y-6">
                  <DatasetView datasetId={selectedDatasetId} refreshTrigger={refreshTrigger} />
                </div>
              )}

              {activeView === 'analysis' && (
                <div className="space-y-8">
                  <Operations datasetId={selectedDatasetId} onOperationComplete={refreshData} />
                  <div className="border-t border-zinc-800 pt-8">
                    <h3 className="text-md font-medium text-zinc-400 mb-4 px-1">Result Preview</h3>
                    <DatasetView datasetId={selectedDatasetId} refreshTrigger={refreshTrigger} />
                  </div>
                </div>
              )}

              {activeView === 'visualize' && (
                <Visualization datasetId={selectedDatasetId} />
              )}

              {activeView === 'dashboard' && (
                <Dashboard datasetId={selectedDatasetId} />
              )}

              {activeView === 'export' && (
                <ExportView datasetId={selectedDatasetId} />
              )}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
