import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Cpu, RefreshCw, CheckCircle, XCircle, X } from 'lucide-react';

const API_BASE = 'http://localhost:8000/api';

interface LastCompleted {
  test_id: string | null;
  part: number | null;
  completed_at: string | null;
  status?: string;
}

interface PipelineStatus {
  running: boolean;
  test_id: string | null;
  part: number | null;
  started_at: string | null;
  last_completed: LastCompleted;
}

const PipelineIndicator: React.FC = () => {
  const [status, setStatus] = useState<PipelineStatus | null>(null);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await fetch(`${API_BASE}/pipeline/status`);
        const data = await res.json();
        setStatus(data);
        // Reset dismissed when a new run starts
        if (data.running) {
          setDismissed(false);
        }
      } catch (err) {
        // Silently fail
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleDismiss = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDismissed(true);
    // Clear server state
    try {
      await fetch(`${API_BASE}/pipeline/clear-completed`, { method: 'POST' });
    } catch {}
  };

  // Priority: running > completed (if not dismissed)
  const isRunning = status?.running;
  const hasCompleted = !dismissed && status?.last_completed?.test_id;

  if (!isRunning && !hasCompleted) return null;

  const completedStatus = status?.last_completed?.status;
  const isError = completedStatus === 'error';
  const isStopped = completedStatus === 'stopped';

  // Determine colors
  let bgColor = 'bg-emerald-600 hover:bg-emerald-700 shadow-emerald-500/30';
  let Icon = RefreshCw;
  let statusText = 'Running';

  if (!isRunning && hasCompleted) {
    if (isError) {
      bgColor = 'bg-orange-600 hover:bg-orange-700 shadow-orange-500/30';
      Icon = XCircle;
      statusText = 'Error';
    } else if (isStopped) {
      bgColor = 'bg-slate-600 hover:bg-slate-700 shadow-slate-500/30';
      Icon = XCircle;
      statusText = 'Stopped';
    } else {
      bgColor = 'bg-blue-600 hover:bg-blue-700 shadow-blue-500/30';
      Icon = CheckCircle;
      statusText = 'Completed';
    }
  }

  const displayTestId = isRunning ? status?.test_id : status?.last_completed?.test_id;
  const displayPart = isRunning ? status?.part : status?.last_completed?.part;

  return (
    <Link
      to="/pipeline"
      className={`fixed bottom-20 right-4 z-50 flex items-center gap-3 px-4 py-3 ${bgColor} text-white rounded-2xl shadow-2xl transition-all animate-in slide-in-from-right duration-300`}
    >
      <div className="relative">
        <Cpu className="w-5 h-5" />
        {isRunning ? (
          <RefreshCw className="w-3 h-3 absolute -bottom-0.5 -right-0.5 animate-spin" />
        ) : (
          <Icon className="w-3 h-3 absolute -bottom-0.5 -right-0.5" />
        )}
      </div>
      <div className="text-left">
        <div className="text-xs font-black uppercase tracking-wider opacity-80">
          Pipeline {statusText} • Part {displayPart}
        </div>
        <div className="text-sm font-bold truncate max-w-[150px]">{displayTestId}</div>
      </div>
      {!isRunning && (
        <button
          onClick={handleDismiss}
          className="ml-2 p-1 rounded-full hover:bg-white/20 transition-colors"
          title="Dismiss"
        >
          <X className="w-4 h-4" />
        </button>
      )}
    </Link>
  );
};

export default PipelineIndicator;
