import React, { useState, useEffect, useRef } from 'react';
import { Play, Terminal, RefreshCw, CheckCircle2, Cpu, FolderOpen, FileText, Layout, Shield } from 'lucide-react';

interface KeyConfig {
  key: string;
  label: string;
  is_enabled: boolean;
}

interface ProviderConfig {
  name: string;
  keys: KeyConfig[];
  models: string[];
  current_key_index: number;
  current_model_index: number;
}

interface LLMSettings {
  active_provider: string;
  providers: ProviderConfig[];
}

interface PipelineConfig {
  settings: LLMSettings;
  active_resource: string;
}

const API_BASE = 'http://localhost:8000/api';
const WS_BASE = 'ws://localhost:8000/api';

const Pipeline: React.FC = () => {
  const [config, setConfig] = useState<PipelineConfig | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [runningPart, setRunningPart] = useState<number | null>(null);
  const [activePromptPart, setActivePromptPart] = useState<number | null>(null);
  const [testId, setTestId] = useState(() => {
    const now = new Date();
    const yyyy = now.getFullYear();
    const mm = String(now.getMonth() + 1).padStart(2, '0');
    const dd = String(now.getDate()).padStart(2, '0');
    const hh = String(now.getHours()).padStart(2, '0');
    const min = String(now.getMinutes()).padStart(2, '0');
    return `ETS_${yyyy}${mm}${dd}_${hh}${min}`;
  });
  const [runConfig, setRunConfig] = useState<any>({
    pdf_path: 'tools/data/PART1/part1.pdf',
    audio_dir: 'tools/data/PART1',
    is_cloud: false
  });

  // Browser state
  const [isBrowsing, setIsBrowsing] = useState<{ active: boolean; field: string | null }>({ active: false, field: null });
  const [browserPath, setBrowserPath] = useState('.');
  const [browserItems, setBrowserItems] = useState<any[]>([]);

  const logEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // Main effect moved to bottom with connectWS

  useEffect(() => {
    if (isBrowsing.active) {
      fetchBrowserItems(browserPath);
    }
  }, [isBrowsing.active, browserPath]);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  const fetchConfig = async () => {
    try {
      const res = await fetch(`${API_BASE}/pipeline/config`);
      const data = await res.json();
      setConfig(data);
    } catch (err) {
      console.error("Failed to fetch config", err);
    }
  };

  const fetchStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/pipeline/status`);
      const data = await res.json();
      if (data.running) {
        setIsRunning(true);
        setTestId(data.test_id);
        setRunningPart(data.part);
      } else {
        setIsRunning(false);
        setRunningPart(null);
      }
      // Restore logs if available and we have none
      if (data.logs && data.logs.length > 0 && logs.length === 0) {
        setLogs(data.logs);
      }
    } catch (err) {
      console.error("Failed to fetch status", err);
    }
  };

  const fetchBrowserItems = async (path: string) => {
    try {
      const res = await fetch(`${API_BASE}/pipeline/browse?path=${encodeURIComponent(path)}`);
      const data = await res.json();
      if (data.items) {
        setBrowserItems(data.items);
        setBrowserPath(data.current_path);
      }
    } catch (err) {
      console.error("Browse error", err);
    }
  };

  const connectWS = () => {
    // Avoid double connections
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(`${WS_BASE}/pipeline/logs`);
    ws.onmessage = (event) => {
      const msg = event.data;
      setLogs(prev => [...prev, msg]);
      
      // Real-time config update on rotation
      if (msg.startsWith("[ROTATION]")) {
        fetchConfig();
      }
      
      // Handle state message from server
      if (msg.startsWith("[STATE]")) {
        // Already running, restore state handled by fetchStatus
      }
      
      // Auto-detect completion
      if (msg.includes("Batch process ended") || msg.includes("Critical Error")) {
        setIsRunning(false);
        setRunningPart(null);
        // Optional: Simple browser notification
        if (Notification.permission === "granted") {
           new Notification("Pipeline Complete", { body: msg });
        }
      }
    };
    
    ws.onclose = () => {
        // Only reconnect if we didn't intentionally close (managed by ref)
        // actually, simpler: just clear ref on close, and let the interval or effect handle checks?
        // or just strict retry.
        // Let's use a flag or just rely on the effect to mount/unmount.
        // For auto-reconnect on server restart:
        setTimeout(() => {
             if (wsRef.current === null) return; // Component unmounted
             connectWS(); 
        }, 3000);
    };
    wsRef.current = ws;
  };

  useEffect(() => {
    // Request notification permission
    if (Notification.permission === "default") {
        Notification.requestPermission();
    }

    fetchConfig();
    fetchStatus(); // Check if pipeline is already running
    const interval = setInterval(fetchConfig, 5000);
    connectWS();
    
    return () => {
      // Cleanup: clear ref so onclose knows not to reconnect
      const ws = wsRef.current;
      wsRef.current = null; 
      if (ws) {
          ws.onclose = null; // Disable reconnect trigger
          ws.close();
      }
      clearInterval(interval);
    };
  }, []);

  const openRunDialog = (part: number) => {
    setActivePromptPart(part);
    if (part === 1) {
      setRunConfig({ pdf_path: 'tools/data/PART1/part1.pdf', audio_dir: 'tools/data/PART1', is_cloud: false });
    } else {
      setRunConfig({ audio_dir: 'tools/data/PART2', is_cloud: false });
    }
  }

  const runPart = async () => {
    const part = activePromptPart;
    if (part === null) return;
    
    setIsRunning(true);
    setActivePromptPart(null);
    setLogs([]);
    try {
      await fetch(`${API_BASE}/pipeline/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ part, test_id: testId, config: runConfig })
      });
    } catch (err) {
      setLogs(prev => [...prev, `[!] Error starting Part ${part}: ${err}`]);
      setIsRunning(false);
    }
  };

  const selectPath = (item: any) => {
    if (item.type === 'dir') {
      setBrowserPath(item.path);
    } else {
      if (isBrowsing.field === 'pdf_path') {
        setRunConfig({ ...runConfig, pdf_path: item.path });
        setIsBrowsing({ active: false, field: null });
      }
    }
  };

  const confirmDirSelect = () => {
    if (isBrowsing.field) {
      setRunConfig({ ...runConfig, [isBrowsing.field]: browserPath });
      setIsBrowsing({ active: false, field: null });
    }
  };

  const goUp = () => {
    // Basic parent resolution
    const parent = browserPath.split('/').slice(0, -1).join('/') || '/';
    setBrowserPath(parent);
  };

  if (!config) return <div className="p-8 text-slate-500 italic">Initializing Pipeline Interface...</div>;

  const activeProviderName = config.settings.active_provider;
  const activeProvider = config.settings.providers.find(p => p.name === activeProviderName);
  const isGoogle = activeProviderName === 'google';

  const PathPicker = () => (
    <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-[100] flex items-center justify-center p-4">
      <div className="bg-white dark:bg-slate-800 w-full max-w-2xl rounded-3xl shadow-2xl border border-slate-200 dark:border-slate-700 overflow-hidden flex flex-col max-h-[80vh]">
        <div className="p-6 bg-slate-50 dark:bg-slate-900 border-b border-slate-100 dark:border-slate-700 flex justify-between items-center gap-4">
          <div className="flex-1 min-w-0">
            <h4 className="font-bold text-slate-900 dark:text-white">System Path Browser</h4>
            <div className="text-[10px] text-slate-500 font-mono mt-1 truncate">{browserPath}</div>
          </div>
          <button 
            onClick={goUp} 
            className="p-2 bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-lg text-xs font-bold text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-600 hover:text-slate-900 dark:hover:text-white flex items-center gap-1"
            title="Go to Parent Directory"
          >
            <FolderOpen className="w-3 h-3" /> Up
          </button>
          <button onClick={() => setIsBrowsing({ active: false, field: null })} className="text-2xl text-slate-400 hover:text-slate-900">&times;</button>
        </div>
        <div className="flex-1 overflow-y-auto p-2">
          <div className="grid grid-cols-1 gap-1">
            {browserItems.map((item, idx) => (
              <button 
                key={idx}
                onClick={() => selectPath(item)}
                className="flex items-center gap-3 p-3 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-xl transition-all text-left group"
              >
                {item.type === 'dir' ? <FolderOpen className="w-5 h-5 text-blue-500" /> : <div className="w-5 h-5 flex items-center justify-center text-slate-400 text-[8px] border rounded">FILE</div>}
                <span className="text-sm font-medium text-slate-700 dark:text-slate-200 truncate">{item.name}</span>
                <span className="ml-auto text-[10px] font-bold text-slate-300 group-hover:text-blue-400 uppercase">{item.type}</span>
              </button>
            ))}
          </div>
        </div>
        <div className="p-4 bg-slate-50 dark:bg-slate-900 border-t border-slate-100 dark:border-slate-700 flex gap-3">
          <button onClick={() => setIsBrowsing({ active: false, field: null })} className="px-6 py-2 bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 text-slate-600 dark:text-white rounded-xl font-bold">Cancel</button>
          <button onClick={confirmDirSelect} className="flex-1 px-6 py-2 bg-blue-600 text-white rounded-xl font-bold shadow-lg shadow-blue-200">Select "{browserPath.split('/').pop() || 'Root'}"</button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className={`p-3 rounded-2xl ${isGoogle ? 'bg-blue-600' : 'bg-emerald-600'} text-white shadow-lg`}>
            <Cpu className="w-8 h-8" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Content Pipeline</h1>
            <p className="text-slate-500 dark:text-slate-400">Monitoring & Execution Hub • <span className="text-blue-600 dark:text-blue-400 font-semibold uppercase">{activeProviderName} Engine</span></p>
          </div>
        </div>
        <div className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-bold border transition-all ${
          isRunning ? 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400 border-emerald-100 dark:border-emerald-800 animate-pulse' : 'bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border-slate-100 dark:border-slate-700'
        }`}>
          <RefreshCw className={`w-4 h-4 ${isRunning ? 'animate-spin' : ''}`} />
          {isRunning ? 'Processing Batch...' : 'System Idle'}
        </div>
        
        {isRunning && (
            <button 
                onClick={async () => {
                    try {
                        const res = await fetch(`${API_BASE}/pipeline/stop`, { method: 'POST' });
                        const data = await res.json();
                        setLogs(prev => [...prev, `[!] ${data.message}`]);
                        setIsRunning(false);
                    } catch (e) {
                         alert("Failed to stop pipeline");
                    }
                }}
                className="ml-2 px-4 py-2 bg-red-100 text-red-600 rounded-full text-sm font-bold hover:bg-red-200 transition-colors flex items-center gap-2"
            >
                <div className="w-2 h-2 bg-red-600 rounded-sm" /> STOP
            </button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-6">
          {/* Target Test Configuration */}
          <section className={`bg-white dark:bg-slate-800 p-6 rounded-3xl shadow-sm border ${isRunning ? 'border-emerald-400/50 ring-2 ring-emerald-400/20' : 'border-slate-100 dark:border-slate-700'}`}>
             <div className="text-slate-900 dark:text-white font-bold flex items-center gap-2 mb-4">
                <Layout className="w-5 h-5 text-blue-600" />
                Target Test
                {isRunning && (
                  <span className="ml-auto text-[10px] font-black bg-emerald-100 dark:bg-emerald-900/50 text-emerald-600 dark:text-emerald-400 px-2 py-0.5 rounded-full animate-pulse">
                    Part {runningPart} Running
                  </span>
                )}
             </div>
             <div className="space-y-2">
                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Test Identifier (Merging Key)</label>
                <div className="relative">
                   <FileText className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                   <input 
                     type="text" 
                     value={testId}
                     onChange={(e) => setTestId(e.target.value)}
                     disabled={isRunning}
                     className={`w-full bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-700 rounded-2xl pl-12 pr-4 py-3 text-sm font-bold focus:bg-white dark:focus:bg-slate-800 focus:border-blue-500 transition-all outline-none dark:text-white ${isRunning ? 'opacity-70 cursor-not-allowed' : ''}`}
                     placeholder="e.g. ETS_Test_2024"
                   />
                </div>
                <p className="text-[10px] text-slate-400 px-1 mt-1">{isRunning ? 'Pipeline is running with this Test ID.' : 'Parts run with the same ID will be merged into a single test.'}</p>
             </div>
          </section>

          <section className="bg-white dark:bg-slate-800 p-6 rounded-3xl shadow-sm border border-slate-100 dark:border-slate-700">
            <div className="flex items-center justify-between mb-6">
              <div className="text-slate-900 dark:text-white font-bold flex items-center gap-2">
                <Cpu className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                Operational Status
              </div>
              <span className="text-[10px] font-bold bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-300 px-2 py-0.5 rounded">Live</span>
            </div>
            
            <div className="space-y-3">
              <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block pl-1">Active Model</label>
              {activeProvider?.models.map((model, idx) => {
                 const isActive = idx === activeProvider.current_model_index;
                 return (
                  <div key={model} className={`relative flex items-center gap-3 p-4 rounded-2xl border-2 transition-all ${
                    isActive ? 'border-emerald-500 bg-emerald-50/50 dark:bg-emerald-900/20 shadow-md' : 'border-slate-50 dark:border-slate-700 text-slate-400 opacity-60'
                  }`}>
                    <div className={`p-2 rounded-lg ${isActive ? 'bg-emerald-600 text-white' : 'bg-slate-100 dark:bg-slate-700'}`}>
                      {isActive ? <CheckCircle2 className="w-4 h-4" /> : <div className="w-4 h-4" />}
                    </div>
                    <div className={`text-sm font-bold ${isActive ? 'text-emerald-900 dark:text-emerald-400' : 'dark:text-white'}`}>{model}</div>
                  </div>
                 )
              })}
            </div>

            <div className="mt-6 space-y-3">
              <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block pl-1">Active Resource (Key)</label>
              {activeProvider?.keys.map((k, idx) => {
                 const isActive = idx === activeProvider.current_key_index;
                 return (
                  <div key={idx} className={`relative flex items-center gap-3 p-4 rounded-2xl border-2 transition-all ${
                    isActive ? 'border-blue-500 bg-blue-50/50 dark:bg-blue-900/20 shadow-md' : 'border-slate-50 dark:border-slate-700 text-slate-400 opacity-60'
                  }`}>
                    <div className={`p-2 rounded-lg ${isActive ? 'bg-blue-600 text-white' : 'bg-slate-100 dark:bg-slate-700'}`}>
                      <Shield className="w-4 h-4" />
                    </div>
                    <div>
                      <div className={`text-sm font-bold ${isActive ? 'text-blue-900 dark:text-blue-400' : 'dark:text-white'}`}>{k.label}</div>
                      {isActive && <div className="text-[10px] text-blue-600 dark:text-blue-400 font-bold uppercase tracking-widest mt-0.5">Currently Using</div>}
                    </div>
                  </div>
                 )
              })}
            </div>

            <div className="mt-6 p-4 bg-slate-50 dark:bg-slate-900 rounded-2xl space-y-2">
               <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Resource Provider</div>
               <div className="text-sm font-medium text-slate-700 dark:text-slate-300">{config.active_resource}</div>
            </div>
          </section>

          <section className="bg-white dark:bg-slate-800 p-6 rounded-3xl shadow-sm border border-slate-100 dark:border-slate-700">
             <div className="text-slate-900 dark:text-white font-bold flex items-center gap-2 mb-6">
                <Play className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                Initialize Parts
             </div>
             <div className="grid grid-cols-2 gap-4">
                <button onClick={() => openRunDialog(1)} className="group p-4 bg-slate-50 dark:bg-slate-900 rounded-2xl border border-slate-100 dark:border-slate-700 hover:border-emerald-400 dark:hover:border-emerald-400/50 hover:bg-emerald-50 dark:hover:bg-emerald-900/10 transition-all text-center space-y-1">
                   <div className="text-2xl font-black text-slate-800 dark:text-white group-hover:scale-110 transition-transform">01</div>
                   <div className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase">Part 1</div>
                </button>
                <button onClick={() => openRunDialog(2)} className="group p-4 bg-slate-50 dark:bg-slate-900 rounded-2xl border border-slate-100 dark:border-slate-700 hover:border-emerald-400 dark:hover:border-emerald-400/50 hover:bg-emerald-50 dark:hover:bg-emerald-900/10 transition-all text-center space-y-1">
                   <div className="text-2xl font-black text-slate-800 dark:text-white group-hover:scale-110 transition-transform">02</div>
                   <div className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase">Part 2</div>
                </button>
             </div>
          </section>
        </div>

        <div className="lg:col-span-2 flex flex-col min-h-[600px] bg-slate-900 rounded-[2.5rem] shadow-2xl overflow-hidden border border-slate-800">
           <div className="px-6 py-4 bg-slate-800/80 backdrop-blur-md flex items-center justify-between border-b border-slate-700/50">
              <div className="flex items-center gap-2 text-blue-400 font-bold">
                 <Terminal className="w-5 h-5" />
                 STREAM CONSOLE
              </div>
           </div>
           <div className="flex-1 p-6 font-mono text-sm overflow-y-auto bg-[radial-gradient(circle_at_top_right,rgba(30,41,59,1),rgba(15,23,42,1))]">
              {logs.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-slate-600 opacity-40">
                   <div className="text-lg font-bold uppercase tracking-widest">Awaiting Command</div>
                </div>
              ) : (
                <div className="space-y-1.5">
                   {logs.map((log, i) => (
                     <div key={i} className="flex gap-3">
                        <span className="text-slate-700 select-none">#{i}</span>
                        <div className={`
                          ${log.includes('[!]') ? 'text-red-400' : 
                            log.includes('[+]') ? 'text-emerald-400' : 
                            log.includes('[*]') ? 'text-blue-400' : 'text-slate-300'}
                        `}>
                          {log}
                        </div>
                     </div>
                   ))}
                   <div ref={logEndRef} />
                </div>
              )}
           </div>
        </div>
      </div>

      {activePromptPart && (
        <div className="fixed inset-0 bg-slate-900/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-800 w-full max-w-xl rounded-[2rem] shadow-2xl border border-slate-200 dark:border-slate-700 overflow-hidden animate-in zoom-in-95">
             <div className="p-8 bg-slate-50 dark:bg-slate-900 border-b border-slate-100 dark:border-slate-700 relative">
                <h3 className="text-2xl font-black text-slate-900 dark:text-white">PART {activePromptPart} CONFIG</h3>
                <button onClick={() => setActivePromptPart(null)} className="absolute top-8 right-8 text-2xl text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors">&times;</button>
             </div>
             <div className="p-8 space-y-6">
                <div className="flex items-center gap-4 p-4 bg-blue-50 dark:bg-slate-700/50 rounded-2xl border border-blue-100 dark:border-slate-600">
                   <div className="flex-1">
                      <div className="text-sm font-bold text-slate-900 dark:text-white">File Access Mode</div>
                      <div className="text-xs text-slate-500 dark:text-slate-400">{runConfig.is_cloud ? 'Cloud Retrieval' : 'Local Storage'}</div>
                   </div>
                   <button onClick={() => setRunConfig({...runConfig, is_cloud: !runConfig.is_cloud})} className="px-4 py-2 bg-white dark:bg-slate-600 rounded-xl text-xs font-bold border border-blue-100 dark:border-slate-500 shadow-sm text-blue-900 dark:text-white hover:bg-blue-50 dark:hover:bg-slate-500 transition-colors">SWITCH</button>
                </div>

                <div className="space-y-4">
                   {activePromptPart === 1 && (
                     <div className="space-y-2">
                        <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">PDF File</label>
                        <div className="flex gap-2">
                           <input 
                             type="text" 
                             value={runConfig.pdf_path} 
                             onChange={(e) => setRunConfig({ ...runConfig, pdf_path: e.target.value })}
                             className="flex-1 bg-slate-50 dark:bg-slate-900 border rounded-xl px-4 py-3 text-sm font-medium focus:bg-white dark:focus:bg-slate-800 focus:border-blue-500 transition-all outline-none dark:text-white dark:border-slate-600" 
                           />
                           <button onClick={() => setIsBrowsing({ active: true, field: 'pdf_path' })} className="px-4 bg-slate-900 text-white rounded-xl hover:bg-slate-800 transition-colors"><FolderOpen className="w-4 h-4"/></button>
                        </div>
                     </div>
                   )}
                   <div className="space-y-2">
                      <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Audio Directory</label>
                      <div className="flex gap-2">
                         <input 
                           type="text" 
                           value={runConfig.audio_dir} 
                           onChange={(e) => setRunConfig({ ...runConfig, audio_dir: e.target.value })}
                           className="flex-1 bg-slate-50 dark:bg-slate-900 border rounded-xl px-4 py-3 text-sm font-medium focus:bg-white dark:focus:bg-slate-800 focus:border-blue-500 transition-all outline-none dark:text-white dark:border-slate-600" 
                         />
                         <button onClick={() => setIsBrowsing({ active: true, field: 'audio_dir' })} className="px-4 bg-slate-900 text-white rounded-xl hover:bg-slate-800 transition-colors"><FolderOpen className="w-4 h-4"/></button>
                      </div>
                   </div>
                </div>
             </div>
             <div className="p-8 bg-slate-50 dark:bg-slate-900 flex gap-4 border-t dark:border-slate-700">
                <button onClick={() => setActivePromptPart(null)} className="flex-1 py-4 bg-white dark:bg-slate-800 border dark:border-slate-600 text-slate-600 dark:text-white rounded-2xl font-bold">CANCEL</button>
                <button onClick={runPart} className="flex-[2] py-4 bg-blue-600 text-white rounded-2xl font-black shadow-lg">START PROCESSING</button>
             </div>
          </div>
        </div>
      )}

      {isBrowsing.active && <PathPicker />}
    </div>
  );
};

export default Pipeline;
