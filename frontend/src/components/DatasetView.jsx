import React, { useEffect, useState } from 'react';
import { viewData, exportDataset } from '../api';
import { ChevronLeft, ChevronRight, Loader2, Download } from 'lucide-react';

const DatasetView = ({ datasetId, refreshTrigger }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const ROWS_PER_PAGE = 20;

  useEffect(() => {
    setPage(0); // Reset page on dataset change
  }, [datasetId, refreshTrigger]);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const result = await viewData(datasetId, page, ROWS_PER_PAGE);
        setData(result);
      } catch (err) {
        console.error("Failed to fetch data view", err);
      } finally {
        setLoading(false);
      }
    };

    if (datasetId) {
      fetchData();
    }
  }, [datasetId, page, refreshTrigger]);

  if (!datasetId) return null;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-zinc-400">
        <Loader2 className="w-6 h-6 animate-spin mr-2" />
        Loading data...
      </div>
    );
  }

  if (!data) return <div className="text-zinc-500 p-4">Failed to load data</div>;

  if (!data) return <div className="text-zinc-500 p-4">Failed to load data</div>;

  const handleDownload = async () => {
    try {
      const response = await exportDataset(datasetId, 'csv');
      // response is the Axios response object, response.data is the Blob
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `processed_data_${datasetId}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Download failed", err);
    }
  };

  const totalPages = Math.ceil(data.total_rows / ROWS_PER_PAGE);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h3 className="text-lg font-medium text-zinc-200">Data Preview</h3>
          <button
            onClick={handleDownload}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white text-xs px-3 py-1.5 rounded-md transition-colors"
          >
            <Download className="w-3 h-3" />
            Export CSV
          </button>
        </div>
        <span className="text-xs text-zinc-500">
          Showing {data.start + 1}-{data.end} of {data.total_rows} rows
        </span>
      </div>

      <div className="overflow-x-auto border border-zinc-800 rounded-lg">
        <table className="w-full text-sm text-left text-zinc-400">
          <thead className="text-xs text-zinc-200 uppercase bg-zinc-800/50">
            <tr>
              {data.columns.map((col) => (
                <th key={col} className="px-4 py-3 whitespace-nowrap font-medium border-b border-zinc-700">
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.data.map((row, idx) => (
              <tr key={idx} className="bg-zinc-900 border-b border-zinc-800 hover:bg-zinc-800/30 transition-colors">
                {data.columns.map((col) => (
                  <td key={`${idx}-${col}`} className="px-4 py-3 whitespace-nowrap truncate max-w-xs">
                    {row[col]?.toString() || ""}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-end gap-2">
        <button
          disabled={page === 0}
          onClick={() => setPage(p => Math.max(0, p - 1))}
          className="p-2 rounded-md bg-zinc-800 hover:bg-zinc-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
        <span className="text-sm text-zinc-400">
          Page {page + 1} of {totalPages}
        </span>
        <button
          disabled={page >= totalPages - 1}
          onClick={() => setPage(p => p + 1)}
          className="p-2 rounded-md bg-zinc-800 hover:bg-zinc-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

export default DatasetView;
