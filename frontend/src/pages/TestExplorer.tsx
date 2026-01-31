import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { TestSummary } from '../types';
import { Search, Filter, Play, Clock, CheckCircle, BarChart2, ChevronRight, MoreVertical, Trash2, BookOpen, Zap, Calendar, Target, TrendingUp } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface UserHistoryItem {
    id: string; 
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

export default function TestExplorer() {
    const [tests, setTests] = useState<TestSummary[]>([]);
    const [history, setHistory] = useState<UserHistoryItem[]>([]);
    const [enrichedTests, setEnrichedTests] = useState<EnrichedTest[]>([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'all' | 'new' | 'completed'>('all');
    const [searchTerm, setSearchTerm] = useState('');
    const [sortBy, setSortBy] = useState<'newest' | 'active'>('newest');
    
    const navigate = useNavigate();

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
                const maxScore = isCompleted ? Math.max(...attempts.map(a => a.score)) : undefined;
                const lastAttempt = isCompleted ? attempts.sort((a,b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())[0].timestamp : undefined;

                return {
                    ...test,
                    status: isCompleted ? 'completed' : 'new',
                    bestScore: maxScore,
                    lastAttemptDate: lastAttempt,
                    attempts: attempts.length,
                    recentAttempts: attempts
                        .sort((a,b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
                        .slice(0, 3)
                        .sort((a,b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
                        .slice(0, 3)
                        .map(a => ({ id: a.id, score: a.score, timestamp: a.timestamp }))
                } as EnrichedTest;
            });
            
            setTests(testsRes.data);
            setHistory(historyRes.data);
            sortAndSet(enriched);
        } catch (error) {
            console.error("Failed to load tests", error);
        } finally {
            setLoading(false);
        }
    };

    const sortAndSet = (list: EnrichedTest[]) => {
        const sorted = [...list];
        if (sortBy === 'newest') {
            sorted.sort((a, b) => {
                const dateA = a.published_at ? new Date(a.published_at).getTime() : 0;
                const dateB = b.published_at ? new Date(b.published_at).getTime() : 0;
                return dateB - dateA;
            });
        } else {
            sorted.sort((a, b) => {
                const dateA = a.lastAttemptDate ? new Date(a.lastAttemptDate).getTime() : 0;
                const dateB = b.lastAttemptDate ? new Date(b.lastAttemptDate).getTime() : 0;
                return dateB - dateA;
            });
        }
        setEnrichedTests(sorted);
    };

    useEffect(() => {
        fetchData();
    }, []);

    useEffect(() => {
        if (enrichedTests.length > 0) {
            sortAndSet(enrichedTests);
        }
    }, [sortBy]);

    const isNearNew = (dateStr?: string) => {
        if (!dateStr) return false;
        const date = new Date(dateStr);
        const now = new Date();
        const diff = now.getTime() - date.getTime();
        return diff < 72 * 60 * 60 * 1000; // 72 hours
    };

    const handleDelete = async (e: React.MouseEvent, testId: string) => {
        e.stopPropagation();
        if (!window.confirm(`Delete "${testId}"?`)) return;
        try {
            await api.delete(`/toeic/tests/${testId}`);
            setEnrichedTests(prev => prev.filter(t => t.test_id !== testId));
        } catch (err) {
            alert("Failed to delete test.");
        }
    };

    const filteredList = enrichedTests.filter(t => {
        const matchesSearch = t.title.toLowerCase().includes(searchTerm.toLowerCase()) || t.test_id.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesTab = activeTab === 'all' ? true : t.status === activeTab;
        return matchesSearch && matchesTab;
    });

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

    if (loading) return <div className="p-12 text-center text-gray-400">Loading Library...</div>;

    return (
        <div className="max-w-7xl mx-auto space-y-10 pb-20 animate-fade-in">
            {/* Header Area */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
                <div className="space-y-2">
                    <h1 className="text-5xl font-black text-slate-900 dark:text-white tracking-tight">Test Library</h1>
                    <p className="text-slate-500 dark:text-slate-400 font-medium text-lg">Browse curated professional TOEIC materials.</p>
                </div>
                
                <div className="flex bg-slate-100 dark:bg-slate-800 p-1.5 rounded-2xl h-fit border border-slate-200 dark:border-slate-700">
                    {(['all', 'new', 'completed'] as const).map(tab => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={`px-8 py-2.5 rounded-xl text-sm font-black capitalize transition-all ${
                                activeTab === tab 
                                ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm border border-slate-200 dark:border-slate-600' 
                                : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
                            }`}
                        >
                            {tab}
                        </button>
                    ))}
                </div>
            </div>

            {/* Filters & Search Row */}
            <div className="flex flex-col lg:flex-row gap-6 items-center">
                <div className="relative flex-1 group w-full">
                    <Search className="absolute left-5 top-1/2 -translate-y-1/2 text-slate-400 w-5 h-5 group-focus-within:text-blue-500 transition-colors" />
                    <input 
                        type="text" 
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        placeholder="Search by title, test ID, or topic..." 
                        className="w-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 pl-14 pr-6 py-4 rounded-[2rem] text-lg font-bold text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-4 focus:ring-blue-50 dark:focus:ring-blue-900/30 focus:border-blue-300 dark:focus:border-blue-700 transition-all shadow-sm"
                    />
                </div>

                <div className="flex items-center gap-3 bg-white dark:bg-slate-800 p-1.5 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm">
                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest pl-3">Order by</span>
                    <div className="flex bg-slate-100 dark:bg-slate-900 p-1 rounded-xl">
                        {(['newest', 'active'] as const).map(s => (
                            <button
                                key={s}
                                onClick={() => setSortBy(s)}
                                className={`px-4 py-2 rounded-lg text-[10px] font-black capitalize transition-all ${
                                    sortBy === s 
                                    ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm' 
                                    : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
                                }`}
                            >
                                {s === 'active' ? 'Last Active' : 'Newest First'}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* Grid */}
            {filteredList.length === 0 ? (
                <div className="text-center py-32 bg-slate-50 rounded-[4rem] border-2 border-dashed border-slate-200">
                    <div className="bg-white w-24 h-24 rounded-[2rem] shadow-sm border border-slate-100 flex items-center justify-center mx-auto mb-6">
                         <BookOpen className="text-slate-200" size={40} />
                    </div>
                    <h3 className="text-2xl font-black text-slate-900 mb-2">No results found</h3>
                    <p className="text-slate-400 max-w-sm mx-auto font-medium">Try adjusting your filters or search terms.</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-8">
                    {filteredList.map(test => (
                        <div key={test.test_id} className="group bg-white dark:bg-slate-800 rounded-[3rem] p-8 border border-slate-100 dark:border-slate-700 shadow-sm hover:shadow-2xl hover:-translate-y-2 transition-all duration-500 relative flex flex-col">
                            
                            {/* Badges Overlay */}
                            <div className="flex items-center justify-between mb-8">
                                <span className={`px-4 py-1.5 rounded-full text-[10px] font-black uppercase tracking-widest ${
                                    test.status === 'completed' ? 'bg-blue-100 text-blue-600' : 'bg-emerald-100 text-emerald-600'
                                }`}>
                                    {test.status === 'completed' ? 'Completed' : 'Ready'}
                                </span>
                                
                                <div className="flex items-center gap-3">
                                    {isNearNew(test.published_at) && (
                                        <span className="bg-emerald-500 text-white px-2 py-1 rounded-md text-[9px] font-black animate-pulse flex items-center gap-1">
                                            <Zap size={10} className="fill-white" /> NEW
                                        </span>
                                    )}
                                    {test.published_at && (
                                        <span className="flex items-center gap-1.5 text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
                                            <Calendar size={12} /> {new Date(test.published_at).toLocaleDateString()}
                                        </span>
                                    )}
                                </div>
                            </div>

                            {/* Center Icon/Visual */}
                            <div className={`h-48 rounded-[2rem] mb-8 flex items-center justify-center relative overflow-hidden ${
                                test.status === 'completed' ? 'bg-slate-950' : 'bg-slate-200 dark:bg-slate-700'
                            }`}>
                                <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                                <span className={`text-6xl font-black select-none ${test.status === 'completed' ? 'text-white/10' : 'text-slate-300 dark:text-slate-600'}`}>TOEIC</span>
                                
                                {test.status === 'completed' && test.bestScore !== undefined && (
                                    <div className="absolute bottom-6 right-6 bg-white/10 backdrop-blur-md px-4 py-2 rounded-2xl border border-white/20 text-white flex items-center gap-2">
                                        <Target size={18} className="text-amber-400" />
                                        <div className="flex flex-col items-start leading-none">
                                            <span className="text-[8px] font-black uppercase text-amber-400 mb-0.5">High Score</span>
                                            <span className="font-black text-xl">{test.bestScore}</span>
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* Info */}
                            <div className="flex-1 space-y-4">
                                <div className="space-y-1">
                                    <div className="flex items-center justify-between">
                                        <h3 className="text-xl font-black text-slate-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors line-clamp-2 leading-tight">{test.title}</h3>
                                        <button 
                                            onClick={(e) => handleDelete(e, test.test_id)}
                                            className="p-2 text-slate-300 hover:text-red-500 hover:bg-red-50 rounded-xl transition-all opacity-0 group-hover:opacity-100"
                                        >
                                            <Trash2 size={16} />
                                        </button>
                                    </div>
                                    <div className="flex items-center gap-2 text-[10px] font-black text-slate-400 font-mono tracking-tighter uppercase">
                                        <Clock size={12} className="text-slate-300" />
                                        <span>
                                            {test.status === 'completed' 
                                                ? `Last Active: ${formatTimeAgo(test.lastAttemptDate)}` 
                                                : `Published: ${new Date(test.published_at || Date.now()).toLocaleDateString()}`
                                            }
                                        </span>
                                        <span className="text-slate-200 mx-1">•</span>
                                        <span>System Publisher</span>
                                    </div>
                                </div>

                                {/* Recent Performance Mini-List */}
                                {test.status === 'completed' && test.recentAttempts.length > 0 && (
                                    <div className="bg-slate-50/50 dark:bg-slate-700/50 rounded-2xl p-4 border border-slate-100/50 dark:border-slate-600/50">
                                        <div className="flex items-center justify-between mb-3">
                                            <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest flex items-center gap-2">
                                                <TrendingUp size={10} className="text-blue-500" /> Recent Performance
                                            </p>
                                            <button 
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    navigate(`/history?test_id=${test.test_id}`);
                                                }}
                                                className="text-[9px] font-bold text-blue-500 hover:text-blue-700 hover:underline cursor-pointer"
                                            >
                                                View All
                                            </button>
                                        </div>
                                        <div className="space-y-2">
                                            {test.recentAttempts.map((attempt, idx) => (
                                                <div 
                                                    key={idx} 
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        navigate(`/result/${attempt.id}`);
                                                    }}
                                                    className="flex items-center justify-between group/score cursor-pointer hover:bg-slate-100/50 p-1 rounded-lg transition-colors -mx-1 px-2"
                                                >
                                                    <span className="text-[10px] font-bold text-slate-500">{new Date(attempt.timestamp).toLocaleDateString()}</span>
                                                    <div className="flex items-center gap-2">
                                                        <div className="h-1 w-8 bg-slate-100 rounded-full overflow-hidden">
                                                            <div 
                                                                className="h-full bg-blue-500 transition-all duration-500" 
                                                                style={{ width: `${(attempt.score / 990) * 100}%` }}
                                                            />
                                                        </div>
                                                        <span className="text-[10px] font-black text-slate-900 dark:text-white">{attempt.score}</span>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                <div className="flex items-center gap-6 pt-2 border-t border-slate-50 dark:border-slate-700 mt-auto">
                                    <div className="flex-1">
                                        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Attempt Stats</p>
                                        <div className="flex items-center gap-2">
                                            <div className="flex -space-x-2">
                                                {[...Array(Math.min(test.attempts, 3))].map((_, i) => (
                                                    <div key={i} className="w-6 h-6 rounded-full border-2 border-white dark:border-slate-800 bg-slate-200 dark:bg-slate-600" />
                                                ))}
                                                {test.attempts > 3 && (
                                                    <div className="w-6 h-6 rounded-full border-2 border-white dark:border-slate-800 bg-slate-100 dark:bg-slate-700 flex items-center justify-center text-[8px] font-black text-slate-400">+{test.attempts - 3}</div>
                                                )}
                                            </div>
                                            <span className="text-xs font-bold text-slate-600 dark:text-slate-400">{test.attempts} session{test.attempts !== 1 ? 's' : ''}</span>
                                        </div>
                                    </div>
                                    
                                    <button 
                                        onClick={() => navigate(`/test/${test.test_id}`)}
                                        className={`px-6 h-14 rounded-2xl flex items-center justify-center gap-3 transition-all shadow-lg font-black text-xs uppercase tracking-widest ${
                                            test.status === 'new'
                                            ? 'bg-slate-900 dark:bg-slate-950 text-white hover:bg-blue-600 shadow-slate-200 dark:shadow-none'
                                            : 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 hover:bg-blue-600 hover:text-white shadow-blue-100 dark:shadow-none'
                                        }`}
                                    >
                                        {test.status === 'completed' ? 'Retake' : 'Start Now'}
                                        <ChevronRight size={18} />
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}

                    {/* Coming Soon Card */}
                    <div className="group bg-slate-50 rounded-[3rem] p-8 border-2 border-dashed border-slate-200 flex flex-col items-center justify-center text-center opacity-70 grayscale hover:grayscale-0 transition-all duration-500">
                        <div className="w-20 h-20 bg-white rounded-3xl mb-6 flex items-center justify-center shadow-sm border border-slate-100">
                            <Clock className="text-slate-300" size={32} />
                        </div>
                        <h3 className="text-xl font-black text-slate-900">Coming Soon</h3>
                        <p className="text-slate-400 font-medium text-sm max-w-[180px] mt-2">More professional content being processed.</p>
                    </div>
                </div>
            )}
        </div>
    );
}
