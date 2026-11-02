import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FolderKanban, Search, Plus, ChevronRight, Filter } from 'lucide-react';
import { projectService } from '../services/projectService';
import { predictionService } from '../services/predictionService';
import RiskBadge from '../components/RiskBadge';
import LoadingSpinner from '../components/LoadingSpinner';

export default function ProjectRecordsPage() {
  const navigate = useNavigate();
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(0);

  useEffect(() => {
    loadRecords();
  }, [page]);

  const loadRecords = async () => {
    try {
      setLoading(true);
      const res = await predictionService.getPredictions(page, 20);
      setPredictions(res.predictions || []);
    } catch (err) {
      console.error('Failed to load predictions:', err);
    } finally {
      setLoading(false);
    }
  };

  const filtered = predictions.filter((p) => {
    const q = search.toLowerCase();
    const name = p.inputSnapshot?.projectName || '';
    const sector = p.inputSnapshot?.sector || '';
    const officer = p.officerName || '';
    return name.toLowerCase().includes(q) || sector.toLowerCase().includes(q) || officer.toLowerCase().includes(q);
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Project Records & History</h1>
          <p className="text-sm text-slate-500">
            Searchable historical archive of assessed government infrastructure projects
          </p>
        </div>
        <button
          onClick={() => navigate('/predict')}
          className="inline-flex items-center gap-2 bg-blue-700 hover:bg-blue-800 text-white px-4 py-2 rounded-lg text-sm font-semibold shadow-sm transition-colors self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" />
          New Assessment
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:w-96">
          <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
          <input
            type="text"
            placeholder="Search by project name, sector, or officer..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-600 focus:border-blue-600"
          />
        </div>
        <div className="text-xs text-slate-500 font-medium">
          Showing {filtered.length} of {predictions.length} records
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-8">
            <LoadingSpinner text="Loading records..." />
          </div>
        ) : filtered.length === 0 ? (
          <div className="p-12 text-center text-slate-400 space-y-2">
            <FolderKanban className="w-10 h-10 mx-auto text-slate-300" />
            <p className="text-sm font-medium text-slate-600">No matching projects found</p>
            <p className="text-xs">Adjust your search query or assess a new project.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50/70 text-slate-500 uppercase text-[11px] font-semibold border-b border-slate-100">
                <tr>
                  <th className="px-5 py-3">Project / Sector</th>
                  <th className="px-5 py-3">Approved Budget</th>
                  <th className="px-5 py-3">Physical Progress</th>
                  <th className="px-5 py-3">Cost Overrun</th>
                  <th className="px-5 py-3">Time Overrun</th>
                  <th className="px-5 py-3">Risk Category</th>
                  <th className="px-5 py-3">Officer</th>
                  <th className="px-5 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filtered.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="px-5 py-3.5">
                      <p className="font-semibold text-slate-800">
                        {item.inputSnapshot?.projectName || `Project #${item.id.slice(0, 8)}`}
                      </p>
                      <p className="text-xs text-slate-500">{item.inputSnapshot?.sector}</p>
                    </td>
                    <td className="px-5 py-3.5 text-slate-700">
                      ₹{item.inputSnapshot?.originalCost?.toFixed(2)} Cr
                    </td>
                    <td className="px-5 py-3.5 text-slate-700">
                      {item.inputSnapshot?.physicalProgress}%
                    </td>
                    <td className="px-5 py-3.5">
                      <span className="font-medium text-slate-800">
                        ₹{item.costOverrunCrore?.toFixed(2)} Cr
                      </span>
                      <span className="text-xs text-slate-500 ml-1">
                        ({item.costOverrunPercentage?.toFixed(1)}%)
                      </span>
                    </td>
                    <td className="px-5 py-3.5 font-medium text-slate-800">
                      {item.timeOverrunMonths?.toFixed(1)} mo
                    </td>
                    <td className="px-5 py-3.5">
                      <RiskBadge category={item.riskCategory} />
                    </td>
                    <td className="px-5 py-3.5 text-xs text-slate-600">
                      {item.officerName || 'Officer'}
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <button
                        onClick={() => navigate(`/predictions/${item.id}`)}
                        className="text-xs font-semibold text-blue-600 hover:text-blue-800 flex items-center gap-0.5 ml-auto"
                      >
                        Audit <ChevronRight className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

