import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Calendar,
  User,
  Cpu,
  ShieldCheck,
  CheckCircle2,
  FileText,
  Clock,
  Landmark,
  TrendingUp,
  Percent
} from 'lucide-react';
import { predictionService } from '../services/predictionService';
import RiskBadge from '../components/RiskBadge';
import LoadingSpinner from '../components/LoadingSpinner';

export default function PredictionResultPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadPrediction();
  }, [id]);

  const loadPrediction = async () => {
    try {
      setLoading(true);
      const data = await predictionService.getPredictionById(id);
      setPrediction(data);
    } catch (err) {
      setError('Unable to load prediction record.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <LoadingSpinner text="Fetching immutable audit record..." />;
  }

  if (error || !prediction) {
    return (
      <div className="p-6 bg-white rounded-xl border border-slate-200 text-center space-y-4">
        <p className="text-red-600 font-semibold">{error || 'Prediction not found.'}</p>
        <button
          onClick={() => navigate('/projects')}
          className="text-sm font-semibold text-blue-600 hover:underline"
        >
          ← Return to Records
        </button>
      </div>
    );
  }

  const snap = prediction.inputSnapshot || {};

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate(-1)}
          className="p-2 hover:bg-slate-100 rounded-lg text-slate-600 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            Prediction Audit Record
          </h1>
          <p className="text-xs text-slate-500 font-mono">ID: {prediction.id}</p>
        </div>
      </div>

      {/* Main card */}
      <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm p-6 space-y-6">
        {/* Status bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-3">
          <div className="flex items-center gap-3">
            <RiskBadge category={prediction.riskCategory} />
            <span className="text-xs text-slate-500 flex items-center gap-1">
              <Calendar className="w-3.5 h-3.5" />
              {prediction.createdAt ? new Date(prediction.createdAt).toLocaleString() : 'N/A'}
            </span>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-600 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-100">
            <Cpu className="w-3.5 h-3.5 text-blue-600" />
            <span>Model Version: <strong>{prediction.modelVersion || '1.0.0'}</strong></span>
          </div>
        </div>

        {/* Prediction Outputs */}
        <div>
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
            Predicted Risk Targets
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="p-4 bg-emerald-50/50 rounded-xl border border-emerald-100">
              <span className="text-xs font-semibold text-emerald-800">Cost Overrun Amount</span>
              <p className="text-2xl font-extrabold text-slate-900 mt-1">
                ₹{prediction.costOverrunCrore?.toFixed(2)} Cr
              </p>
              <p className="text-xs text-emerald-700 font-semibold mt-1">
                +{prediction.costOverrunPercentage?.toFixed(2)}% over approved budget
              </p>
            </div>

            <div className="p-4 bg-blue-50/50 rounded-xl border border-blue-100">
              <span className="text-xs font-semibold text-blue-800">Time Overrun Schedule</span>
              <p className="text-2xl font-extrabold text-slate-900 mt-1">
                {prediction.timeOverrunMonths?.toFixed(1)} months
              </p>
              <p className="text-xs text-blue-700 font-semibold mt-1">
                Estimated completion delay
              </p>
            </div>
          </div>
        </div>

        {/* Immutable Input Snapshot */}
        <div>
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
            Immutable Input Snapshot
          </h3>
          <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 grid grid-cols-2 sm:grid-cols-3 gap-4 text-xs">
            <div>
              <span className="text-slate-500 block">Project Name</span>
              <span className="font-semibold text-slate-800">{snap.projectName || 'Infrastructure Project'}</span>
            </div>
            <div>
              <span className="text-slate-500 block">Sector</span>
              <span className="font-semibold text-slate-800">{snap.sector || 'N/A'}</span>
            </div>
            <div>
              <span className="text-slate-500 block">Original Cost</span>
              <span className="font-semibold text-slate-800">₹{snap.originalCost?.toFixed(2)} Cr</span>
            </div>
            <div>
              <span className="text-slate-500 block">Physical Progress</span>
              <span className="font-semibold text-slate-800">{snap.physicalProgress}%</span>
            </div>
            <div>
              <span className="text-slate-500 block">Reported Delay</span>
              <span className="font-semibold text-slate-800">{snap.timeDelayMonths || 0} months</span>
            </div>
            <div>
              <span className="text-slate-500 block">Assessing Officer</span>
              <span className="font-semibold text-slate-800">{prediction.officerName || 'System Officer'}</span>
            </div>
          </div>
        </div>

        {/* Risk Drivers if available */}
        {prediction.riskDrivers && prediction.riskDrivers.length > 0 && (
          <div>
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
              SHAP Explainer Contributions
            </h3>
            <div className="space-y-2">
              {prediction.riskDrivers.map((driver, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-white border border-slate-100 rounded-lg text-xs">
                  <span className="font-medium text-slate-700 capitalize">{driver.feature.replace(/_/g, ' ')}</span>
                  <div className="flex items-center gap-4">
                    <span className="text-slate-400">Value: {driver.rawValue}</span>
                    <span className={`font-mono font-semibold ${driver.contribution >= 0 ? 'text-rose-600' : 'text-emerald-600'}`}>
                      {driver.contribution >= 0 ? `+${driver.contribution.toFixed(3)}` : driver.contribution.toFixed(3)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

