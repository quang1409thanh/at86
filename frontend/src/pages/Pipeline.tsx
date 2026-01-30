import React, { useState, useEffect, useRef } from 'react';
import { Play, Terminal, RefreshCw, CheckCircle2, Cpu, FolderOpen, Globe, FileText, Layout } from 'lucide-react';

interface ProviderConfig {
  name: string;
  keys: string[];
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
  const [activePromptPart, setActivePromptPart] = useState<number | null>(null);
  const [testId, setTestId] = useState('ETS_Test_01');
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
      
      // Auto-detect completion
      if (msg.includes("Batch process ended") || msg.includes("Critical Error")) {
        setIsRunning(false);
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

  if (!config) return <div className="p-8 text-slate-500 italic">Initializing Pipeline Interface...</div>;

  const activeProviderName = config.settings.active_provider;
  const activeProvider = config.settings.providers.find(p => p.name === activeProviderName);
  const isGoogle = activeProviderName === 'google';

  const PathPicker = () => (
    <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-[100] flex items-center justify-center p-4">
      <div className="bg-white w-full max-w-2xl rounded-3xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col max-h-[80vh]">
        <div className="p-6 bg-slate-50 border-b border-slate-100 flex justify-between items-center">
          <div>
            <h4 className="font-bold text-slate-900">System Path Browser</h4>
            <div className="text-[10px] text-slate-500 font-mono mt-1 truncate max-w-md">{browserPath}</div>
          </div>
          <button onClick={() => setIsBrowsing({ active: false, field: null })} className="text-2xl text-slate-400 hover:text-slate-900">&times;</button>
        </div>
        <div className="flex-1 overflow-y-auto p-2">
          <div className="grid grid-cols-1 gap-1">
            {browserItems.map((item, idx) => (
              <button 
                key={idx}
                onClick={() => selectPath(item)}
                className="flex items-center gap-3 p-3 hover:bg-blue-50 rounded-xl transition-all text-left group"
              >
                {item.type === 'dir' ? <FolderOpen className="w-5 h-5 text-blue-500" /> : <div className="w-5 h-5 flex items-center justify-center text-slate-400 text-[8px] border rounded">FILE</div>}
                <span className="text-sm font-medium text-slate-700 truncate">{item.name}</span>
                <span className="ml-auto text-[10px] font-bold text-slate-300 group-hover:text-blue-400 uppercase">{item.type}</span>
              </button>
            ))}
          </div>
        </div>
        <div className="p-4 bg-slate-50 border-t border-slate-100 flex gap-3">
          <button onClick={() => setIsBrowsing({ active: false, field: null })} className="px-6 py-2 bg-white border border-slate-200 text-slate-600 rounded-xl font-bold">Cancel</button>
          <button onClick={confirmDirSelect} className="flex-1 px-6 py-2 bg-blue-600 text-white rounded-xl font-bold shadow-lg shadow-blue-200">Select Current Directory</button>
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
            <h1 className="text-3xl font-bold text-slate-900">Content Pipeline</h1>
            <p className="text-slate-500">Monitoring & Execution Hub • <span className="text-blue-600 font-semibold uppercase">{activeProviderName} Engine</span></p>
          </div>
        </div>
        <div className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-bold border transition-all ${
          isRunning ? 'bg-emerald-50 text-emerald-700 border-emerald-100 animate-pulse' : 'bg-slate-50 text-slate-600 border-slate-100'
        }`}>
          <RefreshCw className={`w-4 h-4 ${isRunning ? 'animate-spin' : ''}`} />
          {isRunning ? 'Processing Batch...' : 'System Idle'}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-6">
          {/* Target Test Configuration */}
          <section className="bg-white p-6 rounded-3xl shadow-sm border border-slate-100">
             <div className="text-slate-900 font-bold flex items-center gap-2 mb-4">
                <Layout className="w-5 h-5 text-blue-600" />
                Target Test
             </div>
             <div className="space-y-2">
                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Test Identifier (Merging Key)</label>
                <div className="relative">
                   <FileText className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                   <input 
                     type="text" 
                     value={testId}
                     onChange={(e) => setTestId(e.target.value)}
                     className="w-full bg-slate-50 border border-slate-100 rounded-2xl pl-12 pr-4 py-3 text-sm font-bold focus:bg-white focus:border-blue-500 transition-all outline-none"
                     placeholder="e.g. ETS_Test_2024"
                   />
                </div>
                <p className="text-[10px] text-slate-400 px-1 mt-1">Parts run with the same ID will be merged into a single test.</p>
             </div>
          </section>

          <section className="bg-white p-6 rounded-3xl shadow-sm border border-slate-100">
            <div className="flex items-center justify-between mb-6">
              <div className="text-slate-900 font-bold flex items-center gap-2">
                <Cpu className="w-5 h-5 text-blue-600" />
                Operational Status
              </div>
              <span className="text-[10px] font-bold bg-slate-100 text-slate-500 px-2 py-0.5 rounded">Live</span>
            </div>
            
            <div className="space-y-3">
              {activeProvider?.models.map((model, idx) => {
                 const isActive = idx === activeProvider.current_model_index;
                 return (
                  <div key={model} className={`relative flex items-center gap-3 p-4 rounded-2xl border-2 transition-all ${
                    isActive ? 'border-blue-500 bg-blue-50/50 shadow-md scale-[1.02]' : 'border-slate-50 text-slate-400 opacity-60'
                  }`}>
                    {isActive && <div className="absolute -left-1 top-1/2 -translate-y-1/2 w-2 h-8 bg-blue-500 rounded-full" />}
                    <div className={`p-2 rounded-lg ${isActive ? 'bg-blue-600 text-white' : 'bg-slate-100'}`}>
                      {isActive ? <CheckCircle2 className="w-4 h-4" /> : <div className="w-4 h-4" />}
                    </div>
                    <div>
                      <div className={`text-sm font-bold ${isActive ? 'text-blue-900' : ''}`}>{model}</div>
                      {isActive && <div className="text-[10px] text-blue-600 font-bold uppercase tracking-widest mt-0.5">Active</div>}
                    </div>
                  </div>
                 )
              })}
            </div>

            <div className="mt-6 p-4 bg-slate-50 rounded-2xl space-y-2">
               <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Resource Provider</div>
               <div className="text-sm font-medium text-slate-700">{config.active_resource}</div>
            </div>
          </section>

          <section className="bg-white p-6 rounded-3xl shadow-sm border border-slate-100">
             <div className="text-slate-900 font-bold flex items-center gap-2 mb-6">
                <Play className="w-5 h-5 text-emerald-600" />
                Initialize Parts
             </div>
             <div className="grid grid-cols-2 gap-4">
                <button onClick={() => openRunDialog(1)} className="group p-4 bg-slate-50 rounded-2xl border border-slate-100 hover:border-emerald-400 hover:bg-emerald-50 transition-all text-center space-y-1">
                   <div className="text-2xl font-black text-slate-800 group-hover:scale-110 transition-transform">01</div>
                   <div className="text-xs font-bold text-slate-500 uppercase">Part 1</div>
                </button>
                <button onClick={() => openRunDialog(2)} className="group p-4 bg-slate-50 rounded-2xl border border-slate-100 hover:border-emerald-400 hover:bg-emerald-50 transition-all text-center space-y-1">
                   <div className="text-2xl font-black text-slate-800 group-hover:scale-110 transition-transform">02</div>
                   <div className="text-xs font-bold text-slate-500 uppercase">Part 2</div>
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
          <div className="bg-white w-full max-w-xl rounded-[2rem] shadow-2xl border border-slate-200 overflow-hidden animate-in zoom-in-95">
             <div className="p-8 bg-slate-50 border-b">
                <h3 className="text-2xl font-black text-slate-900">PART {activePromptPart} CONFIG</h3>
                <button onClick={() => setActivePromptPart(null)} className="absolute top-8 right-8 text-2xl text-slate-400 hover:text-slate-900">&times;</button>
             </div>
             <div className="p-8 space-y-6">
                <div className="flex items-center gap-4 p-4 bg-blue-50 rounded-2xl">
                   <div className="flex-1">
                      <div className="text-sm font-bold">File Access Mode</div>
                      <div className="text-xs text-slate-500">{runConfig.is_cloud ? 'Cloud Retrieval' : 'Local Storage'}</div>
                   </div>
                   <button onClick={() => setRunConfig({...runConfig, is_cloud: !runConfig.is_cloud})} className="px-4 py-2 bg-white rounded-xl text-xs font-bold border shadow-sm">SWITCH</button>
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
                             className="flex-1 bg-slate-50 border rounded-xl px-4 py-3 text-sm font-medium focus:bg-white focus:border-blue-500 transition-all outline-none" 
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
                           className="flex-1 bg-slate-50 border rounded-xl px-4 py-3 text-sm font-medium focus:bg-white focus:border-blue-500 transition-all outline-none" 
                         />
                         <button onClick={() => setIsBrowsing({ active: true, field: 'audio_dir' })} className="px-4 bg-slate-900 text-white rounded-xl hover:bg-slate-800 transition-colors"><FolderOpen className="w-4 h-4"/></button>
                      </div>
                   </div>
                </div>
             </div>
             <div className="p-8 bg-slate-50 flex gap-4 border-t">
                <button onClick={() => setActivePromptPart(null)} className="flex-1 py-4 bg-white border text-slate-600 rounded-2xl font-bold">CANCEL</button>
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
