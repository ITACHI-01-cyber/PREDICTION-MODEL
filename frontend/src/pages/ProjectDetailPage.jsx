import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, FolderKanban, Calendar, Clock, DollarSign } from 'lucide-react';
import { projectService } from '../services/projectService';
import LoadingSpinner from '../components/LoadingSpinner';

export default function ProjectDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadProject();
  }, [id]);

  const loadProject = async () => {
    try {
      setLoading(true);
      const data = await projectService.getProjectById(id);
      setProject(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <LoadingSpinner text="Loading project details..." />;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate('/projects')}
          className="p-2 hover:bg-slate-100 rounded-lg text-slate-600 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{project?.projectName || 'Project Details'}</h1>
          <p className="text-xs text-slate-500">ID: {project?.id || id}</p>
        </div>
      </div>

      <div className="bg-white p-6 rounded-xl border border-slate-200/80 shadow-sm space-y-4">
        <h3 className="text-sm font-bold text-slate-900 border-b pb-2">Overview</h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-slate-500 block text-xs">Sector</span>
            <span className="font-semibold">{project?.sector || 'N/A'}</span>
          </div>
          <div>
            <span className="text-slate-500 block text-xs">Original Cost</span>
            <span className="font-semibold">₹{project?.originalCost || 0} Cr</span>
          </div>
          <div>
            <span className="text-slate-500 block text-xs">Physical Progress</span>
            <span className="font-semibold">{project?.physicalProgress || 0}%</span>
          </div>
          <div>
            <span className="text-slate-500 block text-xs">State / Region</span>
            <span className="font-semibold">{project?.state || 'N/A'}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

