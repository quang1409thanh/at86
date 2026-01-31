import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { useAuth } from '../contexts/AuthContext';
import { User, Lock, Save, ShieldCheck, LogOut, Activity, Award, Calendar, LayoutDashboard } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

// Types for stats
interface UserStats {
    totalTests: number;
    averageScore: number;
    highestScore: number;
    lastActive: string;
}

export default function UserProfile() {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    
    const [activeTab, setActiveTab] = useState<'overview' | 'security'>('overview');
    const [stats, setStats] = useState<UserStats>({ totalTests: 0, averageScore: 0, highestScore: 0, lastActive: 'New Member' });
    const [loadingStats, setLoadingStats] = useState(true);

    // Password Form State
    const [currentPassword, setCurrentPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        // Fetch History to calculate stats
        api.get('/toeic/history')
            .then(res => {
                const history = res.data || [];
                if (history.length === 0) {
                     setStats({ totalTests: 0, averageScore: 0, highestScore: 0, lastActive: 'No activity' });
                } else {
                    const total = history.length;
                    // Assuming score is available or calculable. For now, we might just count.
                    // If the API returns full objects with scores, we use them. 
                    // Based on previous files, result contains 'score'.
                    const scores = history.map((h: any) => h.score || 0);
                    const avg = Math.round(scores.reduce((a: number, b: number) => a + b, 0) / total);
                    const max = Math.max(...scores);
                    const lastDate = history[0].timestamp ? new Date(history[0].timestamp).toLocaleString([], { dateStyle: 'short', timeStyle: 'medium' }) : 'Unknown';

                    setStats({
                        totalTests: total,
                        averageScore: avg,
                        highestScore: max,
                        lastActive: lastDate
                    });
                }
            })
            .catch(err => console.error("Failed to load stats", err))
            .finally(() => setLoadingStats(false));
    }, []);

    const handlePasswordChange = async (e: React.FormEvent) => {
        e.preventDefault();
        setMessage(null);
        
        if (newPassword !== confirmPassword) {
            setMessage({ type: 'error', text: "New passwords do not match." });
            return;
        }
        if (newPassword.length < 6) {
             setMessage({ type: 'error', text: "Password must be at least 6 characters." });
             return;
        }

        setSaving(true);
        try {
            await api.put('/auth/change-password', {
                current_password: currentPassword,
                new_password: newPassword
            });
            setMessage({ type: 'success', text: "Password updated successfully." });
            setCurrentPassword('');
            setNewPassword('');
            setConfirmPassword('');
        } catch (err: any) {
            setMessage({ 
                type: 'error', 
                text: err.response?.data?.detail || "Failed to update password." 
            });
        } finally {
            setSaving(false);
        }
    };

    const handleLogout = () => {
        if (window.confirm("Are you sure you want to log out?")) {
            logout();
        }
    };

    if (!user) return null;

    return (
        <div className="max-w-5xl mx-auto space-y-8 pb-12">
            {/* Header Section */}
            <header className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
                <div>
                   <h1 className="text-4xl font-black text-gray-900 dark:text-white tracking-tight mb-2">My Profile</h1>
                   <p className="text-gray-500 dark:text-gray-400 font-medium">Manage your account settings and view your progress.</p>
                </div>
                <button 
                    onClick={handleLogout}
                    className="flex items-center gap-2 px-6 py-2.5 bg-red-50 text-red-600 font-bold rounded-xl hover:bg-red-100 transition-colors"
                >
                    <LogOut size={18} /> Log Out
                </button>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                {/* Sidebar Navigation */}
                <div className="lg:col-span-3 space-y-2">
                    <TabButton 
                        active={activeTab === 'overview'} 
                        icon={<LayoutDashboard size={20} />} 
                        label="Overview" 
                        onClick={() => setActiveTab('overview')} 
                    />
                    <TabButton 
                        active={activeTab === 'security'} 
                        icon={<ShieldCheck size={20} />} 
                        label="Security" 
                        onClick={() => setActiveTab('security')} 
                    />
                </div>

                {/* Main Content Area */}
                <div className="lg:col-span-9 space-y-6">
                    {activeTab === 'overview' && (
                        <div className="space-y-6 animate-fade-in">
                            {/* User User Card */}
                            <div className="bg-white dark:bg-slate-800 p-8 rounded-3xl shadow-sm border border-gray-100 dark:border-slate-700 flex items-center gap-6">
                                <div className="w-24 h-24 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center text-white shadow-lg shadow-blue-200 dark:shadow-none">
                                    <span className="text-3xl font-bold">{user.username.charAt(0).toUpperCase()}</span>
                                </div>
                                <div className="space-y-1">
                                    <h2 className="text-2xl font-bold text-gray-900 dark:text-white">{user.username}</h2>
                                    <div className="flex items-center gap-2">
                                        <span className="px-3 py-1 rounded-full bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 text-xs font-bold uppercase tracking-wider flex items-center gap-1.5 w-fit">
                                            <ShieldCheck size={12} /> {user.role} Account
                                        </span>
                                    </div>
                                </div>
                            </div>

                            {/* Stats Grid */}
                            <h3 className="text-lg font-bold text-gray-900 dark:text-white px-1">Performance Statistics</h3>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                <StatCard 
                                    icon={<Activity size={24} />} 
                                    label="Tests Completed" 
                                    value={stats.totalTests} 
                                    color="blue"
                                    loading={loadingStats}
                                />
                                <StatCard 
                                    icon={<Award size={24} />} 
                                    label="Average Score" 
                                    value={stats.averageScore} 
                                    color="amber"
                                    loading={loadingStats}
                                />
                                <StatCard 
                                    icon={<Calendar size={24} />} 
                                    label="Last Active" 
                                    value={stats.lastActive} 
                                    color="purple"
                                    loading={loadingStats}
                                />
                            </div>
                        </div>
                    )}

                    {activeTab === 'security' && (
                        <div className="bg-white dark:bg-slate-800 p-8 rounded-3xl shadow-sm border border-gray-100 dark:border-slate-700 animate-fade-in relative overflow-hidden">
                             {/* Decorative Background */}
                             <div className="absolute top-0 right-0 p-12 opacity-[0.03] dark:opacity-[0.05] dark:text-white">
                                <Lock size={200} />
                             </div>

                             <div className="relative">
                                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-1">Password Management</h3>
                                <p className="text-gray-500 dark:text-gray-400 text-sm mb-8">Update your password to keep your account secure.</p>

                                {message && (
                                    <div className={`p-4 rounded-xl text-sm font-bold flex items-center gap-2 mb-6 ${
                                        message.type === 'success' ? 'bg-green-50 text-green-600' : 'bg-red-50 text-red-600'
                                    }`}>
                                        {message.text}
                                    </div>
                                )}

                                <form onSubmit={handlePasswordChange} className="space-y-6 max-w-lg">
                                    <div className="space-y-2">
                                        <label className="text-sm font-bold text-gray-700 dark:text-gray-300">Current Password</label>
                                        <div className="relative">
                                            <input 
                                                type="password" 
                                                required
                                                value={currentPassword}
                                                onChange={(e) => setCurrentPassword(e.target.value)}
                                                className="w-full pl-12 pr-4 py-3.5 bg-gray-50 dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-xl font-medium outline-none focus:border-blue-500 dark:focus:border-blue-500 focus:bg-white dark:focus:bg-slate-800 transition-all text-gray-900 dark:text-white"
                                                placeholder="••••••••"
                                            />
                                            <Lock size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-1 gap-6 pt-2">
                                        <div className="space-y-2">
                                            <label className="text-sm font-bold text-gray-700 dark:text-gray-300">New Password</label>
                                            <input 
                                                type="password" 
                                                required
                                                value={newPassword}
                                                onChange={(e) => setNewPassword(e.target.value)}
                                                className="w-full px-4 py-3.5 bg-gray-50 dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-xl font-medium outline-none focus:border-blue-500 dark:focus:border-blue-500 focus:bg-white dark:focus:bg-slate-800 transition-all text-gray-900 dark:text-white"
                                                placeholder="New password (min 6 chars)"
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <label className="text-sm font-bold text-gray-700 dark:text-gray-300">Confirm Password</label>
                                            <input 
                                                type="password" 
                                                required
                                                value={confirmPassword}
                                                onChange={(e) => setConfirmPassword(e.target.value)}
                                                className="w-full px-4 py-3.5 bg-gray-50 dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-xl font-medium outline-none focus:border-blue-500 dark:focus:border-blue-500 focus:bg-white dark:focus:bg-slate-800 transition-all text-gray-900 dark:text-white"
                                                placeholder="Re-enter new password"
                                            />
                                        </div>
                                    </div>

                                    <div className="pt-4">
                                        <button 
                                            type="submit" 
                                            disabled={saving}
                                            className="px-8 py-3.5 bg-gray-900 dark:bg-blue-600 text-white font-bold rounded-xl hover:bg-gray-800 dark:hover:bg-blue-500 transition shadow-lg flex items-center gap-2 disabled:opacity-50 w-full justify-center sm:w-auto"
                                        >
                                            {saving ? 'Updating...' : (
                                                <>
                                                    <Save size={18} /> Update Password
                                                </>
                                            )}
                                        </button>
                                    </div>
                                </form>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

function TabButton({ active, icon, label, onClick }: { active: boolean, icon: React.ReactNode, label: string, onClick: () => void }) {
    return (
        <button 
            onClick={onClick}
            className={`w-full flex items-center gap-3 px-5 py-4 rounded-xl font-bold transition-all ${
                active 
                ? 'bg-white dark:bg-slate-800 text-blue-600 dark:text-blue-400 shadow-md shadow-gray-100 dark:shadow-none' 
                : 'text-gray-500 dark:text-gray-400 hover:bg-white/50 dark:hover:bg-slate-800/50 hover:text-gray-700 dark:hover:text-gray-200'
            }`}
        >
            {icon}
            {label}
        </button>
    )
}

function StatCard({ icon, label, value, color, loading }: any) {
    const colorClasses: any = {
        blue: 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400',
        amber: 'bg-amber-50 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400',
        purple: 'bg-purple-50 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400',
    };

    return (
        <div className="p-6 bg-white dark:bg-slate-800 rounded-3xl border border-gray-100 dark:border-slate-700 shadow-sm flex items-center gap-5">
            <div className={`p-4 rounded-2xl ${colorClasses[color] || 'bg-gray-50 dark:bg-slate-700 text-gray-600 dark:text-gray-400'}`}>
                {icon}
            </div>
            <div>
                <p className="text-sm font-bold text-gray-400 dark:text-gray-500 uppercase tracking-wide">{label}</p>
                {loading ? (
                    <div className="h-8 w-24 bg-gray-100 dark:bg-slate-700 rounded-lg animate-pulse mt-1" />
                ) : (
                    <p className={`font-black text-gray-900 dark:text-white mt-0.5 break-words ${typeof value === 'string' && value.length > 10 ? 'text-lg' : 'text-3xl'}`}>
                        {value}
                    </p>
                )}
            </div>
        </div>
    )
}
