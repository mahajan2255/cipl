import React, { useState } from 'react';
import { Download, Database, Info, FileText } from 'lucide-react'; // Removing duplicate FileText
import { exportDataset, downloadReport } from '../api';
import { clsx } from 'clsx';

const ExportView = ({ datasetId }) => {
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState(null);

    const handleExport = async (format) => {
        setLoading(true);
        setMessage(null);
        try {
            const response = await exportDataset(datasetId, format);
            // response.data IS the blob here
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;

            // Try to get filename from content-disposition
            const contentDisposition = response.headers['content-disposition'];
            let filename = `dataset_${datasetId}.${format === 'excel' ? 'xlsx' : format}`;
            if (contentDisposition) {
                const match = contentDisposition.match(/filename=(.+)/);
                if (match) filename = match[1];
            }

            link.setAttribute('download', filename);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);

            setMessage({ type: 'success', text: `Exported ${format} successfully!` });
        } catch (err) {
            console.error("Export failed", err);
            setMessage({ type: 'error', text: "Export failed" });
        } finally {
            setLoading(false);
        }
    };

    const handleReport = async () => {
        setLoading(true);
        setMessage(null);
        try {
            const response = await downloadReport(datasetId);
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `report_${datasetId}.pdf`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);

            setMessage({ type: 'success', text: "Report generated successfully!" });
        } catch (err) {
            console.error("Report generation failed", err);
            setMessage({ type: 'error', text: "Report generation failed" });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h3 className="text-xl font-medium text-zinc-200">Export & Reports</h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {/* Excel */}
                <button
                    type="button"
                    onClick={() => handleExport('excel')}
                    disabled={loading}
                    className="flex flex-col items-center justify-center p-8 bg-zinc-900 border border-zinc-800 rounded-xl hover:bg-zinc-800 hover:border-green-800/50 transition-all group disabled:opacity-50"
                >
                    <div className="w-12 h-12 rounded-full bg-green-500/10 flex items-center justify-center mb-4 group-hover:bg-green-500/20 transition-colors">
                        <FileSpreadsheet className="w-6 h-6 text-green-500" />
                    </div>
                    <h4 className="font-medium text-zinc-200 mb-2">Excel Export</h4>
                    <p className="text-sm text-zinc-500 text-center">Download processed data as .xlsx spreadsheet</p>
                </button>

                {/* CSV */}
                <button
                    type="button"
                    onClick={() => handleExport('csv')}
                    disabled={loading}
                    className="flex flex-col items-center justify-center p-8 bg-zinc-900 border border-zinc-800 rounded-xl hover:bg-zinc-800 hover:border-blue-800/50 transition-all group disabled:opacity-50"
                >
                    <div className="w-12 h-12 rounded-full bg-blue-500/10 flex items-center justify-center mb-4 group-hover:bg-blue-500/20 transition-colors">
                        <FileText className="w-6 h-6 text-blue-500" />
                    </div>
                    <h4 className="font-medium text-zinc-200 mb-2">CSV Export</h4>
                    <p className="text-sm text-zinc-500 text-center">Standard Comma Separated Values file</p>
                </button>

                {/* JSON */}
                <button
                    type="button"
                    onClick={() => handleExport('json')}
                    disabled={loading}
                    className="flex flex-col items-center justify-center p-8 bg-zinc-900 border border-zinc-800 rounded-xl hover:bg-zinc-800 hover:border-yellow-800/50 transition-all group disabled:opacity-50"
                >
                    <div className="w-12 h-12 rounded-full bg-yellow-500/10 flex items-center justify-center mb-4 group-hover:bg-yellow-500/20 transition-colors">
                        <Database className="w-6 h-6 text-yellow-500" />
                    </div>
                    <h4 className="font-medium text-zinc-200 mb-2">JSON Export</h4>
                    <p className="text-sm text-zinc-500 text-center">Structured JSON data format</p>
                </button>

                {/* PDF Report */}
                <button
                    type="button"
                    onClick={handleReport}
                    disabled={loading}
                    className="flex flex-col items-center justify-center p-8 bg-zinc-900 border border-zinc-800 rounded-xl hover:bg-zinc-800 hover:border-purple-800/50 transition-all group disabled:opacity-50"
                >
                    <div className="w-12 h-12 rounded-full bg-purple-500/10 flex items-center justify-center mb-4 group-hover:bg-purple-500/20 transition-colors">
                        <FileText className="w-6 h-6 text-purple-500" />
                    </div>
                    <h4 className="font-medium text-zinc-200 mb-2">PDF Summary Report</h4>
                    <p className="text-sm text-zinc-500 text-center">Comprehensive analysis summary document</p>
                </button>
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

export default ExportView;
