import React, { useState } from 'react';
import { Download, FileSpreadsheet, ShieldAlert, CheckCircle, BarChart3 } from 'lucide-react';
import { reportService } from '../services/reportService';

export default function ReportsPage() {
  const [downloading, setDownloading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleExport = async () => {
    try {
      setDownloading(true);
      await reportService.exportCSV();
      setSuccess(true);
      setTimeout(() => setSuccess(false), 4000);
    } catch (err) {
      alert('Export failed. Ensure backend has accessible prediction records.');
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Audit & Analytical Reports</h1>
        <p className="text-sm text-slate-500">
          Export verified government project overrun risk assessments for executive reviews
        </p>
      </div>

      <div className="bg-white p-6 rounded-xl border border-slate-200/80 shadow-sm space-y-6">
        <div className="flex items-start gap-4">
          <div className="p-3 bg-blue-50 text-blue-700 rounded-xl">
            <FileSpreadsheet className="w-8 h-8" />
          </div>
          <div className="flex-1">
            <h3 className="font-bold text-slate-900 text-base">Consolidated Risk Register (CSV)</h3>
            <p className="text-sm text-slate-500 mt-1">
              Complete historical dump including immutable input snapshots (Sector, Cost, Delay, Progress),
              XGBoost target predictions (Cost Overrun in Cr, Time Overrun in Months), risk tiers, and officer timestamps.
            </p>
          </div>
        </div>

        {success && (
          <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm rounded-lg flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-600" />
            Export generated and downloaded successfully.
          </div>
        )}

        <div className="pt-2">
          <button
            onClick={handleExport}
            disabled={downloading}
            className="flex items-center gap-2 px-5 py-2.5 bg-blue-700 hover:bg-blue-800 text-white rounded-lg text-sm font-semibold shadow-sm transition-colors disabled:opacity-50"
          >
            <Download className="w-4 h-4" />
            {downloading ? 'Preparing CSV...' : 'Download Project Risk Export'}
          </button>
        </div>
      </div>
    </div>
  );
}

