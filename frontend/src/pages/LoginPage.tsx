import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { Lock, User, ArrowRight, ShieldCheck } from 'lucide-react';

const LoginPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('username', username);
      formData.append('password', password);

      const response = await api.post('/auth/token', formData, {
        headers: { 'Content-Type': 'multipart/form-data' } // OAuth2 standard
      });

      const { access_token, role } = response.data;
      localStorage.setItem('token', access_token);
      localStorage.setItem('role', role);
      localStorage.setItem('username', username);

      // Redirect based on role or default
      navigate('/'); 
    } catch (err: any) {
      console.error("Login failed", err);
      setError('Invalid credentials. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6">
      <div className="bg-white w-full max-w-md rounded-[2.5rem] shadow-xl border border-slate-100 overflow-hidden">
        <div className="bg-slate-900 p-8 text-center relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-full bg-[radial-gradient(circle_at_top_right,rgba(59,130,246,0.3),transparent)]" />
          <div className="relative z-10 flex flex-col items-center">
             <div className="w-16 h-16 bg-white/10 backdrop-blur-md rounded-2xl flex items-center justify-center mb-4 text-emerald-400">
                <ShieldCheck size={32} />
             </div>
             <h1 className="text-2xl font-bold text-white tracking-tight">System Access</h1>
             <p className="text-slate-400 text-sm mt-1">Please authenticate to continue</p>
          </div>
        </div>

        <div className="p-8">
          <form onSubmit={handleLogin} className="space-y-6">
             {error && (
               <div className="p-4 bg-red-50 text-red-600 text-sm font-bold rounded-xl flex items-center gap-2 animate-pulse">
                  <Lock size={16} /> {error}
               </div>
             )}

             <div className="space-y-2">
                <label className="text-xs font-bold text-slate-400 uppercase tracking-widest ml-1">Username</label>
                <div className="relative">
                   <User className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                   <input 
                     type="text" 
                     value={username}
                     onChange={e => setUsername(e.target.value)}
                     className="w-full pl-12 pr-4 py-4 bg-slate-50 border border-slate-200 rounded-2xl font-bold text-slate-700 outline-none focus:bg-white focus:border-blue-500 transition-all"
                     placeholder="Enter your username"
                     required
                   />
                </div>
             </div>

             <div className="space-y-2">
                <label className="text-xs font-bold text-slate-400 uppercase tracking-widest ml-1">Password</label>
                <div className="relative">
                   <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                   <input 
                     type="password" 
                     value={password}
                     onChange={e => setPassword(e.target.value)}
                     className="w-full pl-12 pr-4 py-4 bg-slate-50 border border-slate-200 rounded-2xl font-bold text-slate-700 outline-none focus:bg-white focus:border-blue-500 transition-all"
                     placeholder="••••••••"
                     required
                   />
                </div>
             </div>

             <button 
               type="submit" 
               disabled={loading}
               className="w-full py-4 bg-blue-600 hover:bg-blue-700 active:scale-[0.98] transition-all text-white font-black rounded-2xl shadow-lg shadow-blue-200 flex items-center justify-center gap-2"
             >
               {loading ? 'Authenticating...' : (
                 <>
                   Sign In <ArrowRight size={20} />
                 </>
               )}
             </button>
          </form>
          
          <div className="mt-8 text-center">
             <p className="text-xs text-slate-400 font-medium">Restricted Area • TOEIC Platform v1.0</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
