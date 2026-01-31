import React, { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Shield, Cpu, Plus, Trash2, Save, CheckCircle2, AlertCircle, RefreshCw } from 'lucide-react';

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

const API_BASE = 'http://localhost:8000/api';

const SettingsPage: React.FC = () => {
  const [settings, setSettings] = useState<LLMSettings>({
    active_provider: 'google',
    providers: []
  });
  const [newKey, setNewKey] = useState<{ [key: string]: string }>({});
  const [newModel, setNewModel] = useState<{ [key: string]: string }>({});
  const [fetchedModels, setFetchedModels] = useState<{ [key: string]: string[] }>({});
  const [loadingModels, setLoadingModels] = useState<string | null>(null);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'success' | 'error'>('idle');

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const res = await fetch(`${API_BASE}/pipeline/config`);
      const data = await res.json();
      setSettings(data.settings);
    } catch (err) {
      console.error("Failed to fetch settings", err);
    }
  };

  const fetchAvailableModels = async (providerName: string) => {
    setLoadingModels(providerName);
    try {
      // Temporarily switch backend provider to fetch valid models if needed, 
      // but simpler to just passing provider param to backend if backend supports it.
      // Current backend implementation just uses active provider. 
      // We will rely on user selecting active provider first or backend update.
      // Actually, let's just call the endpoint.
      const res = await fetch(`${API_BASE}/pipeline/models`);
      const data = await res.json();
      if (data.models) {
         setFetchedModels(prev => ({ ...prev, [providerName]: data.models }));
      }
    } catch (err) {
      console.error("Failed to fetch models", err);
    } finally {
      setLoadingModels(null);
    }
  };

  const handleSave = async () => {
    setSaveStatus('saving');
    try {
      const res = await fetch(`${API_BASE}/pipeline/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      });
      if (res.ok) {
        setSaveStatus('success');
        setTimeout(() => setSaveStatus('idle'), 3000);
      } else {
        setSaveStatus('error');
      }
    } catch (err) {
      setSaveStatus('error');
    }
  };

  const addKey = (providerName: string) => {
    const val = newKey[providerName];
    if (!val?.trim()) return;
    
    setSettings(prev => ({
      ...prev,
      providers: prev.providers.map(p => 
        p.name === providerName ? { ...p, keys: [...p.keys, val.trim()] } : p
      )
    }));
    setNewKey({ ...newKey, [providerName]: '' });
  };

  const removeKey = (providerName: string, idx: number) => {
    setSettings(prev => ({
      ...prev,
      providers: prev.providers.map(p => 
        p.name === providerName ? { ...p, keys: p.keys.filter((_, i) => i !== idx) } : p
      )
    }));
  };

  const addModel = (providerName: string) => {
    const val = newModel[providerName];
    if (!val?.trim()) return;
    
    setSettings(prev => ({
      ...prev,
      providers: prev.providers.map(p => 
        p.name === providerName ? { ...p, models: [...p.models, val.trim()] } : p
      )
    }));
    setNewModel({ ...newModel, [providerName]: '' });
  };

  const removeModel = (providerName: string, idx: number) => {
    setSettings(prev => ({
      ...prev,
      providers: prev.providers.map(p => 
        p.name === providerName ? { ...p, models: p.models.filter((_, i) => i !== idx) } : p
      )
    }));
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white flex items-center gap-3">
            <SettingsIcon className="w-8 h-8 text-blue-600" />
            System Settings
          </h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">Configure your LLM providers and rotation preferences.</p>
        </div>
        <button
          onClick={handleSave}
          disabled={saveStatus === 'saving'}
          className={`flex items-center gap-2 px-6 py-2.5 rounded-xl font-bold transition-all shadow-lg ${
            saveStatus === 'success' ? 'bg-emerald-500 text-white shadow-emerald-200' :
            saveStatus === 'error' ? 'bg-red-500 text-white shadow-red-200' :
            'bg-blue-600 text-white hover:bg-blue-700 shadow-blue-200'
          }`}
        >
          {saveStatus === 'saving' ? 'Saving...' : 
           saveStatus === 'success' ? <><CheckCircle2 className="w-5 h-5"/> Saved</> :
           saveStatus === 'error' ? <><AlertCircle className="w-5 h-5"/> Error</> :
           <><Save className="w-5 h-5"/> Save Changes</>}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <aside className="space-y-1">
          <nav className="flex flex-col gap-1">
            <button className="flex items-center gap-3 px-4 py-3 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400 rounded-xl font-semibold transition-all">
              <Cpu className="w-5 h-5" />
              LLM Configuration
            </button>
            <button className="flex items-center gap-3 px-4 py-3 text-slate-500 dark:text-slate-400 hover:bg-white dark:hover:bg-slate-800 rounded-xl transition-all opacity-50 cursor-not-allowed">
              <Shield className="w-5 h-5" />
              Security & Privacy
            </button>
          </nav>
        </aside>

        <section className="md:col-span-2 space-y-6">
          <div className="bg-white dark:bg-slate-800 p-6 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-700 space-y-6">
            <div className="flex items-center gap-2 font-bold text-slate-800 dark:text-white border-b border-slate-50 dark:border-slate-700 pb-4">
              <Cpu className="w-5 h-5 text-blue-600" />
              Active Provider
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              {settings.providers.map(p => (
                <button
                  key={p.name}
                  onClick={() => setSettings({ ...settings, active_provider: p.name })}
                  className={`p-4 rounded-xl border-2 transition-all flex flex-col items-center gap-2 ${
                    settings.active_provider === p.name ? 'border-blue-500 bg-blue-50/50 dark:bg-blue-900/20' : 'border-slate-100 dark:border-slate-700 hover:border-slate-200 dark:hover:border-slate-600'
                  }`}
                >
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-white text-[10px] uppercase ${
                    p.name === 'google' ? 'bg-blue-600' : p.name === 'openai' ? 'bg-emerald-600' : 'bg-slate-700'
                  }`}>
                    {p.name.substring(0, 3)}
                  </div>
                  <span className={`font-bold capitalize ${settings.active_provider === p.name ? 'text-blue-700 dark:text-blue-400' : 'text-slate-600 dark:text-slate-400'}`}>
                    {p.name}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {settings.providers.map((p) => (
            <div key={p.name} className={`bg-white dark:bg-slate-800 p-6 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-700 space-y-6 transition-all ${settings.active_provider !== p.name ? 'opacity-50 grayscale scale-[0.98]' : ''}`}>
              <div className="flex items-center justify-between">
                <div className="font-bold text-slate-800 dark:text-white capitalize border-l-4 border-blue-500 pl-3">{p.name} Engine Configuration</div>
                <span className="text-[10px] uppercase font-bold px-2 py-0.5 bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-300 rounded">Dynamic Rotation</span>
              </div>

              <div className="space-y-6">
                <div>
                  <label className="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest block mb-3">Authorized API Keys</label>
                  <div className="space-y-2">
                    {p.keys.map((key, i) => (
                      <div key={i} className="flex gap-2 animate-in slide-in-from-right-2 duration-300">
                        <input 
                          type="password" 
                          value={key}
                          readOnly
                          className="flex-1 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg px-3 py-2 text-sm font-mono text-slate-600 dark:text-white"
                        />
                        <button onClick={() => removeKey(p.name, i)} className="p-2 text-slate-300 hover:text-red-500 transition-colors">
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                    <div className="flex gap-2 mt-2">
                       <input 
                         type="text" 
                         placeholder={`Add ${p.name} key...`}
                         value={newKey[p.name] || ''}
                         onChange={(e) => setNewKey({ ...newKey, [p.name]: e.target.value })}
                         className="flex-1 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 focus:border-blue-500 focus:ring-1 focus:ring-blue-100 rounded-lg px-3 py-2 text-sm transition-all dark:text-white"
                       />
                       <button onClick={() => addKey(p.name)} className="px-4 py-2 bg-slate-900 text-white rounded-lg font-bold text-sm hover:bg-slate-800 transition-colors">
                         <Plus className="w-4 h-4" />
                       </button>
                    </div>
                  </div>
                </div>

                <div>
                   <label className="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest block mb-3">Model Pool</label>
                   <div className="flex flex-wrap gap-2 mb-3">
                      {p.models.map((model, i) => (
                        <div key={i} className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-full text-xs font-semibold text-slate-700 dark:text-slate-300">
                          {model}
                          <button onClick={() => removeModel(p.name, i)} className="text-slate-400 hover:text-red-500 transition-colors">
                            <Trash2 className="w-3 h-3" />
                          </button>
                        </div>
                      ))}
                   </div>
                   
                   <div className="flex gap-2 items-center">
                       {/* Datalist for suggestions */}
                       <input 
                         type="text" 
                         list={`models-${p.name}`}
                         placeholder="Add model..."
                         value={newModel[p.name] || ''}
                         onChange={(e) => setNewModel({ ...newModel, [p.name]: e.target.value })}
                         className="bg-white dark:bg-slate-900 border border-dashed border-slate-300 dark:border-slate-600 rounded-full px-4 py-1.5 text-xs focus:border-blue-500 outline-none w-48 dark:text-white"
                       />
                       <datalist id={`models-${p.name}`}>
                          {fetchedModels[p.name]?.map(m => <option key={m} value={m} />)}
                       </datalist>

                       <button 
                         onClick={() => fetchAvailableModels(p.name)} 
                         disabled={loadingModels === p.name}
                         className="p-1.5 bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-400 rounded-full hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
                         title="Fetch available models from provider"
                       >
                         <RefreshCw className={`w-3 h-3 ${loadingModels === p.name ? 'animate-spin' : ''}`} />
                       </button>

                       <button onClick={() => addModel(p.name)} className="p-1.5 bg-blue-600 text-white rounded-full hover:bg-blue-700 transition-colors shadow-sm">
                         <Plus className="w-3 h-3" />
                       </button>
                    </div>
                </div>
              </div>
            </div>
          ))}
        </section>
      </div>
    </div>
  );
};

export default SettingsPage;
