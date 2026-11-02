import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Sparkles,
  Calculator,
  AlertCircle,
  HelpCircle,
  Clock,
  Landmark,
  Percent,
  CheckCircle2,
  TrendingUp,
  ShieldAlert,
  Info
} from 'lucide-react';
import { predictionService } from '../services/predictionService';
import RiskBadge from '../components/RiskBadge';

const SECTORS = [
  'Road Transport & Highways',
  'Railways',
  'Power',
  'Petroleum',
  'Water Resources',
  'Urban Development',
  'Telecommunication'
];

export default function NewPredictionPage() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    projectName: 'Dehradun – Rishikesh Road Widening Project',
    projectType: 'Road Infrastructure',
    sector: 'Road Transport & Highways',
    originalCost: 48.5,
    plannedDuration: 24,
    physicalProgress: 58,
    timeDelayMonths: 4,
    tenderMethod: 'Open Tender',
    region: 'Uttarakhand'
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  const handleChange = (e) => {
    const { name, value, type } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'number' ? (value === '' ? '' : parseFloat(value)) : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const payload = {
        projectName: formData.projectName,
        sector: formData.sector,
        originalCost: Number(formData.originalCost),
        physicalProgress: Number(formData.physicalProgress),
        timeDelayMonths: Number(formData.timeDelayMonths || 0),
        plannedDuration: Number(formData.plannedDuration || 0),
        projectType: formData.projectType,
        tenderMethod: formData.tenderMethod,
        region: formData.region,
      };

      const res = await predictionService.createPrediction(payload);
      setResult(res);
    } catch (err) {
      setError(err.response?.data?.message || err.message || 'Prediction execution failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Project Risk Assessment</h1>
        <p className="text-sm text-slate-500">
          Run multi-target XGBoost prediction for infrastructure cost & schedule variance
        </p>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3 text-red-700 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold">Assessment Error</p>
            <p>{error}</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Form */}
        <div className="lg:col-span-7 bg-white p-6 rounded-xl border border-slate-200/80 shadow-sm">
          <div className="flex items-center gap-2 mb-5 pb-3 border-b border-slate-100">
            <Calculator className="w-5 h-5 text-blue-600" />
            <h2 className="font-bold text-slate-900 text-base">Project Assessment Parameters</h2>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Project Name
              </label>
              <input
                type="text"
                name="projectName"
                required
                value={formData.projectName}
                onChange={handleChange}
                placeholder="e.g. Dehradun – Rishikesh Road Widening"
                className="w-full px-3.5 py-2 border border-slate-300 rounded-lg text-sm text-slate-900 focus:ring-2 focus:ring-blue-600 focus:border-blue-600"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Sector (Model Feature)
                </label>
                <select
                  name="sector"
                  value={formData.sector}
                  onChange={handleChange}
                  className="w-full px-3.5 py-2 border border-slate-300 rounded-lg text-sm text-slate-900 focus:ring-2 focus:ring-blue-600 focus:border-blue-600 bg-white"
                >
                  {SECTORS.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Region / State
                </label>
                <input
                  type="text"
                  name="region"
                  value={formData.region}
                  onChange={handleChange}
                  placeholder="e.g. Uttarakhand"
                  className="w-full px-3.5 py-2 border border-slate-300 rounded-lg text-sm text-slate-900 focus:ring-2 focus:ring-blue-600 focus:border-blue-600"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Original Approved Budget (₹ Crore)
                </label>
                <div className="relative rounded-md shadow-sm">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400 text-sm font-semibold">
                    ₹
                  </div>
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    required
                    name="originalCost"
                    value={formData.originalCost}
                    onChange={handleChange}
                    className="w-full pl-8 pr-3 py-2 border border-slate-300 rounded-lg text-sm text-slate-900 focus:ring-2 focus:ring-blue-600 focus:border-blue-600"
                    placeholder="48.50"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Current Physical Progress (%)
                </label>
                <div className="relative rounded-md shadow-sm">
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="100"
                    required
                    name="physicalProgress"
                    value={formData.physicalProgress}
                    onChange={handleChange}
                    className="w-full pl-3 pr-8 py-2 border border-slate-300 rounded-lg text-sm text-slate-900 focus:ring-2 focus:ring-blue-600 focus:border-blue-600"
                    placeholder="58"
                  />
                  <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none text-slate-400 text-sm">
                    %
                  </div>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Existing Delay (Months)
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  name="timeDelayMonths"
                  value={formData.timeDelayMonths}
                  onChange={handleChange}
                  placeholder="0"
                  className="w-full px-3.5 py-2 border border-slate-300 rounded-lg text-sm text-slate-900 focus:ring-2 focus:ring-blue-600 focus:border-blue-600"
                />
                <span className="text-[11px] text-slate-400 mt-1 block">
                  Current schedule delay already incurred
                </span>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Planned Duration (Months)
                </label>
                <input
                  type="number"
                  step="1"
                  min="1"
                  name="plannedDuration"
                  value={formData.plannedDuration}
                  onChange={handleChange}
                  placeholder="24"
                  className="w-full px-3.5 py-2 border border-slate-300 rounded-lg text-sm text-slate-900 focus:ring-2 focus:ring-blue-600 focus:border-blue-600"
                />
                <span className="text-[11px] text-slate-400 mt-1 block">
                  Originally planned contract duration
                </span>
              </div>
            </div>

            <div className="pt-4 flex items-center gap-3">
              <button
                type="submit"
                disabled={loading}
                className="flex-1 flex justify-center items-center gap-2 py-2.5 px-4 rounded-lg text-sm font-semibold text-white bg-blue-700 hover:bg-blue-800 disabled:opacity-50 transition-colors shadow-sm"
              >
                <Sparkles className="w-4 h-4" />
                {loading ? 'Evaluating Model...' : 'Calculate Risk Overrun'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setFormData({
                    projectName: 'National Highway Expansion Phase 2',
                    projectType: 'Road Transport',
                    sector: 'Road Transport & Highways',
                    originalCost: 1500,
                    plannedDuration: 36,
                    physicalProgress: 35,
                    timeDelayMonths: 8,
                    tenderMethod: 'EPC',
                    region: 'Maharashtra',
                  });
                }}
                className="px-3 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-lg border border-slate-200"
              >
                Load Sample
              </button>
            </div>
          </form>
        </div>

        {/* Right Column: Results card matching image */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-white p-6 rounded-xl border border-slate-200/80 shadow-sm">
            <div className="flex items-center justify-between mb-4 pb-2 border-b border-slate-100">
              <h3 className="font-bold text-slate-900 text-base">Prediction Results</h3>
              {result && <RiskBadge category={result.riskCategory} />}
            </div>

            {!result ? (
              <div className="py-12 text-center text-slate-400 space-y-3">
                <Calculator className="w-12 h-12 mx-auto text-slate-300" />
                <p className="text-sm">
                  Complete the project parameters on the left and submit to view ML predictions.
                </p>
                <div className="text-xs bg-slate-50 p-3 rounded-lg text-slate-500 text-left border border-slate-100">
                  <p className="font-semibold text-slate-700 mb-1">Standard Government Audit Schema:</p>
                  <ul className="list-disc pl-4 space-y-0.5">
                    <li>Sector canonicalization (7 MoSPI groups)</li>
                    <li>Cost Overrun in ₹ Crore</li>
                    <li>Schedule Overrun in Months</li>
                    <li>SAFE / MODERATE / RISKY tiering</li>
                  </ul>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Visual Category Banner */}
                <div className="grid grid-cols-3 gap-2 text-center text-xs font-bold py-1">
                  <div
                    className={`py-2 rounded-lg border ${
                      result.riskCategory === 'SAFE'
                        ? 'bg-emerald-50 border-emerald-500 text-emerald-700'
                        : 'bg-slate-50 text-slate-400 border-slate-200'
                    }`}
                  >
                    ✓ SAFE
                  </div>
                  <div
                    className={`py-2 rounded-lg border ${
                      result.riskCategory === 'MODERATE'
                        ? 'bg-amber-50 border-amber-500 text-amber-700'
                        : 'bg-slate-50 text-slate-400 border-slate-200'
                    }`}
                  >
                    ⦿ MODERATE
                  </div>
                  <div
                    className={`py-2 rounded-lg border ${
                      result.riskCategory === 'RISKY'
                        ? 'bg-rose-50 border-rose-500 text-rose-700'
                        : 'bg-slate-50 text-slate-400 border-slate-200'
                    }`}
                  >
                    ⚠ RISKY
                  </div>
                </div>

                {/* Overrun output cards */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                  <div className="p-4 bg-emerald-50/60 rounded-xl border border-emerald-100">
                    <span className="text-xs font-medium text-emerald-800 block mb-1">
                      Predicted Cost Overrun
                    </span>
                    <p className="text-xl font-extrabold text-slate-900">
                      ₹{result.costOverrunCrore?.toFixed(2)} Cr
                    </p>
                    <p className="text-xs text-emerald-700 font-semibold mt-0.5">
                      +{result.costOverrunPercentage?.toFixed(1)}% of budget
                    </p>
                  </div>

                  <div className="p-4 bg-blue-50/60 rounded-xl border border-blue-100">
                    <span className="text-xs font-medium text-blue-800 block mb-1">
                      Predicted Time Overrun
                    </span>
                    <p className="text-xl font-extrabold text-slate-900">
                      {result.timeOverrunMonths?.toFixed(1)} months
                    </p>
                    <p className="text-xs text-blue-700 font-semibold mt-0.5">
                      Schedule delay estimate
                    </p>
                  </div>
                </div>

                {/* Key Risk Drivers */}
                {result.riskDrivers && result.riskDrivers.length > 0 && (
                  <div className="p-3 bg-amber-50/80 rounded-lg border border-amber-200 text-xs text-amber-900">
                    <p className="font-semibold flex items-center gap-1.5 mb-1 text-amber-800">
                      <ShieldAlert className="w-4 h-4 text-amber-600" />
                      Key Risk Drivers (SHAP Feature Importance)
                    </p>
                    <div className="space-y-1">
                      {result.riskDrivers.slice(0, 3).map((driver, idx) => (
                        <div key={idx} className="flex justify-between items-center text-[11px]">
                          <span className="capitalize">{driver.feature.replace(/_/g, ' ')}</span>
                          <span className="font-mono font-medium">
                            {driver.contribution > 0 ? `+${driver.contribution.toFixed(2)}` : driver.contribution.toFixed(2)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="pt-2 flex justify-end">
                  <button
                    onClick={() => navigate(`/predictions/${result.id}`)}
                    className="text-xs font-semibold text-blue-700 hover:text-blue-900 flex items-center gap-1"
                  >
                    View Full Prediction Audit Record →
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

