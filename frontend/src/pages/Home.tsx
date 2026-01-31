import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { TestSummary } from '../types';
import { Play, Award, Clock, BookOpen, ChevronRight, TrendingUp, Zap } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface UserHistoryItem {
    id: string; // Result ID
    test_id: string;
    score: number;
    timestamp: string;
}

interface EnrichedTest extends TestSummary {
    status: 'new' | 'completed';
    bestScore?: number;
    lastAttemptDate?: string;
    attempts: number;
    published_at?: string;
    recentAttempts: { id: string, score: number, timestamp: string }[];
}

export default function Home() {
    const [history, setHistory] = useState<UserHistoryItem[]>([]);
    const [enrichedTests, setEnrichedTests] = useState<EnrichedTest[]>([]);
    const [loading, setLoading] = useState(true);
    
    const navigate = useNavigate();

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [testsRes, historyRes] = await Promise.all([
                    api.get<TestSummary[]>('/toeic/tests'),
                    api.get<UserHistoryItem[]>('/toeic/history')
                ]);
                
                const historyMap = new Map<string, UserHistoryItem[]>();
                historyRes.data.forEach(h => {
                    if (!historyMap.has(h.test_id)) historyMap.set(h.test_id, []);
                    historyMap.get(h.test_id)?.push(h);
                });

                const enriched = testsRes.data.map(test => {
                    const attempts = historyMap.get(test.test_id) || [];
                    const isCompleted = attempts.length > 0;
                    const maxScore = attempts.length > 0 ? Math.max(...attempts.map(a => a.score)) : undefined;
                    const lastAttempt = attempts.length > 0 ? attempts.sort((a,b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())[0].timestamp : undefined;

                    return {
                        ...test,
                        status: isCompleted ? 'completed' : 'new',
                        bestScore: maxScore,
                        lastAttemptDate: lastAttempt,
                        attempts: attempts.length,
                        recentAttempts: attempts
                            .sort((a,b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
                            .slice(0, 3)
                            .map(a => ({ id: a.id, score: a.score, timestamp: a.timestamp }))
                    } as EnrichedTest;
                });
                
                // Sort by last active / published for "Continue" or "Latest"
                setEnrichedTests(enriched);
                setHistory(historyRes.data);

            } catch (error) {
                console.error("Failed to load dashboard data", error);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    const stats = {
        totalTests: enrichedTests.length,
        completed: enrichedTests.filter(t => t.status === 'completed').length,
        avgScore: history.length > 0 ? Math.round(history.reduce((a,b) => a + b.score, 0) / history.length) : 0,
        bestScore: history.length > 0 ? Math.max(...history.map(h => h.score)) : 0
    };

    const recentTests = [...enrichedTests]
        .filter(t => t.attempts > 0)
        .sort((a, b) => {
            const dateA = a.lastAttemptDate ? new Date(a.lastAttemptDate).getTime() : 0;
            const dateB = b.lastAttemptDate ? new Date(b.lastAttemptDate).getTime() : 0;
            return dateB - dateA;
        })
        .slice(0, 3);

    const latestTests = [...enrichedTests]
        .filter(t => t.status === 'new')
        .sort((a, b) => {
            const dateA = a.published_at ? new Date(a.published_at).getTime() : 0;
            const dateB = b.published_at ? new Date(b.published_at).getTime() : 0;
            return dateB - dateA;
        })
        .slice(0, 3);

    const isNearNew = (dateStr?: string) => {
        if (!dateStr) return false;
        const date = new Date(dateStr);
        const now = new Date();
        const diff = now.getTime() - date.getTime();
        return diff < 72 * 60 * 60 * 1000; // 72 hours
    };

    const formatTimeAgo = (dateStr?: string) => {
        if (!dateStr) return 'N/A';
        const date = new Date(dateStr);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);

        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        return `${diffDays}d ago`;
    };

    if (loading) return <div className="p-12 text-center text-gray-400">Loading Dashboard...</div>;

    return (
        <div className="max-w-7xl mx-auto space-y-12 pb-20 animate-fade-in">
            {/* Header / Hero */}
            <div className="relative overflow-hidden bg-slate-900 rounded-[3rem] p-12 text-white shadow-2xl">
                <div className="absolute top-0 right-0 w-1/3 h-full bg-gradient-to-l from-blue-600/20 to-transparent pointer-events-none" />
                <div className="relative z-10 space-y-6 max-w-2xl">
                    <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-md px-4 py-2 rounded-full border border-white/10">
                        <Zap size={16} className="text-yellow-400 fill-yellow-400" />
                        <span className="text-xs font-black uppercase tracking-widest">Active Learning Session</span>
                    </div>
                    <h1 className="text-6xl font-black tracking-tighter leading-none">
                        Welcome back,<br />
                        <span className="bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">Ready to excel?</span>
                    </h1>
                    <p className="text-slate-400 font-medium text-lg leading-relaxed">
                        Your performance is up 12% this week. Keep going to reach your target score.
                    </p>
                    <div className="flex items-center gap-4 pt-4">
                        <button 
                            onClick={() => navigate('/tests')}
                            className="bg-blue-600 hover:bg-blue-500 text-white px-8 py-4 rounded-2xl font-black flex items-center gap-2 transition-all shadow-lg shadow-blue-900/40"
                        >
                            <Play size={20} fill="currentColor" /> Browse Library
                        </button>
                    </div>
                </div>
            </div>

            {/* Top Level Stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {[
                    { label: 'Overall Progress', value: `${Math.round((stats.completed / stats.totalTests) * 100) || 0}%`, icon: TrendingUp, color: 'blue' },
                    { label: 'Average Score', value: stats.avgScore, icon: Award, color: 'amber' },
                    { label: 'Personal Best', value: stats.bestScore, icon: Zap, color: 'emerald' },
                    { label: 'Available Tests', value: stats.totalTests, icon: BookOpen, color: 'indigo' }
                ].map((stat, i) => (
                    <div key={i} className="bg-white dark:bg-slate-800 rounded-[2rem] p-8 border border-slate-100 dark:border-slate-700 shadow-sm hover:shadow-md transition-shadow">
                        <div className={`w-12 h-12 rounded-2xl bg-${stat.color}-50 dark:bg-${stat.color}-900/30 flex items-center justify-center text-${stat.color}-600 dark:text-${stat.color}-400 mb-6`}>
                            <stat.icon size={24} />
                        </div>
                        <p className="text-slate-400 font-black text-[10px] uppercase tracking-widest mb-1">{stat.label}</p>
                        <p className="text-4xl font-black text-slate-900 dark:text-white">{stat.value}</p>
                    </div>
                ))}
            </div>

            {/* Activity & Suggestions Split */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
                
                {/* Recent Activity */}
                <div className="lg:col-span-8 space-y-8">
                    <div className="flex items-center justify-between">
                        <h2 className="text-3xl font-black text-slate-900 dark:text-white tracking-tight">Recent Activity</h2>
                        <button onClick={() => navigate('/history')} className="text-blue-600 dark:text-blue-400 font-black text-xs uppercase tracking-widest hover:underline">View All History</button>
                    </div>

                    <div className="grid grid-cols-1 gap-4">
                        {recentTests.length > 0 ? recentTests.map(test => (
                            <div key={test.test_id} className="group bg-white dark:bg-slate-800 rounded-[2.5rem] p-6 border border-slate-100 dark:border-slate-700 shadow-sm hover:shadow-xl transition-all duration-300 flex items-center justify-between">
                                <div className="flex items-center gap-6">
                                    <div className="w-16 h-16 rounded-2xl bg-slate-900 dark:bg-black flex items-center justify-center text-white font-black text-xs italic">
                                        TOEIC
                                    </div>
                                    <div>
                                        <h3 className="text-lg font-black text-slate-900 dark:text-white mb-1 line-clamp-2">{test.title}</h3>
                                        <div className="flex items-center gap-4 text-xs font-bold text-slate-400 uppercase tracking-widest">
                                            <span className="flex items-center gap-1.5"><Clock size={12} /> {formatTimeAgo(test.lastAttemptDate)}</span>
                                            <span className="flex items-center gap-1.5"><Award size={12} className="text-amber-500" /> Best: {test.bestScore || 0}</span>
                                        </div>
                                    </div>
                                    {/* Mini Trend Line */}
                                    <div className="hidden sm:flex items-center gap-1 ml-6">
                                        {test.recentAttempts.map((a, i) => (
                                            <div 
                                                key={i}
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    navigate(`/result/${a.id}`);
                                                }}
                                                className="w-1.5 bg-blue-100 dark:bg-blue-900/30 rounded-full overflow-hidden flex flex-col justify-end h-8 cursor-pointer hover:bg-blue-200 dark:hover:bg-blue-800 transition-colors group/bar"
                                                title={`Score: ${a.score} - Click to view result`}
                                            >
                                                <div 
                                                    className="bg-blue-500 dark:bg-blue-400 w-full group-hover/bar:bg-blue-600 dark:group-hover/bar:bg-blue-300 transition-colors" 
                                                    style={{ height: `${(a.score / 990) * 100}%` }}
                                                />
                                            </div>
                                        )).reverse()}
                                    </div>
                                    </div>

                                <button 
                                    onClick={() => navigate(`/test/${test.test_id}`)}
                                    className="w-12 h-12 rounded-xl bg-slate-50 dark:bg-slate-700 text-slate-900 dark:text-white hover:bg-slate-900 dark:hover:bg-slate-600 hover:text-white flex items-center justify-center transition-all"
                                >
                                    <ChevronRight size={24} />
                                </button>
                            </div>
                        )) : (
                            <div className="text-center py-20 bg-slate-50 rounded-[3rem] border border-dashed border-slate-200">
                                <p className="text-slate-400 font-bold uppercase tracking-widest text-xs">No recent activity yet.</p>
                                <button onClick={() => navigate('/tests')} className="text-blue-600 font-black text-sm mt-2">Start your first test</button>
                            </div>
                        )}
                    </div>
                </div>

                {/* Latest / Recommended Side */}
                <div className="lg:col-span-4 space-y-8">
                    <div className="flex items-center justify-between">
                        <h2 className="text-3xl font-black text-slate-900 dark:text-white tracking-tight">New Materials</h2>
                    </div>

                    <div className="space-y-4">
                        {latestTests.length > 0 ? latestTests.map(test => (
                            <div key={test.test_id} className="bg-gradient-to-br from-white to-slate-50 dark:from-slate-800 dark:to-slate-900 border border-slate-100 dark:border-slate-700 rounded-[2rem] p-6 flex flex-col gap-4 shadow-sm">
                                <div>
                                    <div className="bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest w-fit mb-3 flex items-center gap-1">
                                        {isNearNew(test.published_at) && <Zap size={10} className="fill-emerald-700 dark:fill-emerald-400" />}
                                        {isNearNew(test.published_at) ? 'New Arrival' : 'Recently Released'}
                                    </div>
                                    <h4 className="text-base font-black text-slate-900 dark:text-white leading-tight line-clamp-2">{test.title}</h4>
                                    <div className="flex items-center gap-2 mt-2">
                                        <Clock size={10} className="text-slate-300 dark:text-slate-500" />
                                        <p className="text-slate-400 dark:text-slate-500 text-[9px] font-black uppercase tracking-tight">Published {new Date(test.published_at || Date.now()).toLocaleDateString()}</p>
                                    </div>
                                </div>
                                <button 
                                    onClick={() => navigate(`/test/${test.test_id}`)}
                                    className="w-full bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 py-3 rounded-xl font-black text-sm text-slate-900 dark:text-white hover:border-blue-500 dark:hover:border-blue-400 hover:text-blue-600 dark:hover:text-blue-400 transition-all flex items-center justify-center gap-2"
                                >
                                    Start Test <ChevronRight size={16} />
                                </button>
                            </div>
                        )) : (
                            <div className="p-8 bg-blue-50 rounded-[3rem] text-center space-y-4 border border-blue-100">
                                <Clock className="text-blue-200 mx-auto" size={40} />
                                <h4 className="text-blue-900 font-black">All Caught Up!</h4>
                                <p className="text-blue-600/60 text-xs font-medium">You've seen all the latest content. Retake tests to master them!</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
