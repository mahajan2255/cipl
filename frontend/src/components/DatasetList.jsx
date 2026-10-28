import React, { useEffect, useState } from 'react';
import { Trash2, FileText, Calendar, Table, Database } from 'lucide-react';
import { getDatasets, deleteDataset } from '../api';
import { clsx } from 'clsx';

const DatasetList = ({ onSelect, selectedId, refreshTrigger }) => {
  const [datasets, setDatasets] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchDatasets = async () => {
    try {
      const result = await getDatasets();
      setDatasets(result.datasets);
    } catch (err) {
      console.error("Failed to load datasets", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDatasets();
  }, [refreshTrigger]);

  const handleDelete = async (e, id) => {
    e.stopPropagation();
    if (confirm("Are you sure you want to delete this dataset?")) {
      await deleteDataset(id);
      fetchDatasets();
      if (selectedId === id) onSelect(null);
    }
  };

  if (loading) {
    return <div className="p-4 text-zinc-400 text-sm animate-pulse">Loading datasets...</div>;
  }

  if (datasets.length === 0) {
    return (
      <div className="p-8 text-center text-zinc-500 border border-zinc-800 rounded-lg bg-zinc-900/50">
        <Database className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p className="text-sm">No datasets found</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <h2 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-3 px-2">Your Datasets</h2>
      <div className="space-y-1">
        {datasets.map((ds) => (
          <div
            key={ds.id}
            onClick={() => onSelect(ds.id)}
            className={clsx(
              "group flex items-center justify-between p-3 rounded-lg cursor-pointer transition-all duration-200 border",
              selectedId === ds.id
                ? "bg-blue-500/10 border-blue-500/20 shadow-sm"
                : "bg-zinc-900/30 border-transparent hover:bg-zinc-800 hover:border-zinc-700"
            )}
          >
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                 <FileText className={clsx("w-4 h-4", selectedId === ds.id ? "text-blue-400" : "text-zinc-400")} />
                 <h3 className={clsx("text-sm font-medium truncate", selectedId === ds.id ? "text-blue-100" : "text-zinc-300")}>
                   {ds.filename}
                 </h3>
              </div>
              <div className="flex items-center gap-3 text-xs text-zinc-500">
                <span className="flex items-center gap-1">
                  <Calendar className="w-3 h-3" />
                  {new Date(ds.upload_time).toLocaleDateString()}
                </span>
                <span className="flex items-center gap-1">
                   <Table className="w-3 h-3" />
                   {ds.current_shape[0]} × {ds.current_shape[1]}
                </span>
              </div>
            </div>
            
            <button
              onClick={(e) => handleDelete(e, ds.id)}
              className="p-2 text-zinc-600 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity rounded-md hover:bg-red-500/10"
              title="Delete dataset"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default DatasetList;
