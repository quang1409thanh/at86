import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import type { UserResult } from '../types';
import { format } from 'date-fns';
import { Calendar, Target, Clock, Filter, X, ChevronDown } from 'lucide-react';
import { useSearchParams } from 'react-router-dom';

export default function HistoryPage() {
    const [history, setHistory] = useState<UserResult[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchParams, setSearchParams] = useSearchParams();
    const filterTestId = searchParams.get('test_id');

    useEffect(() => {
        api.get<UserResult[]>('/toeic/history')
            .then(res => setHistory(res.data))
            .finally(() => setLoading(false));
    }, []);

    // Filter history if test_id is present
    const filteredHistory = filterTestId 
        ? history.filter(h => h.test_id === filterTestId)
        : history;

    // Extract unique test IDs
    const uniqueTestIds = Array.from(new Set(history.map(h => h.test_id))).sort();

    // Grouping logic
    const grouped = filteredHistory.reduce((acc, item) => {
        const dateKey = format(new Date(item.timestamp), 'yyyy-MM-dd');
        if (!acc[dateKey]) acc[dateKey] = [];
        acc[dateKey].push(item);
        return acc;
    }, {} as Record<string, UserResult[]>);

    const sortedDates = Object.keys(grouped).sort((a, b) => b.localeCompare(a));

    const formatDateHeader = (dateStr: string) => {
        const date = new Date(dateStr);
        const today = new Date();
        const yesterday = new Date();
        yesterday.setDate(today.getDate() - 1);

        if (format(date, 'yyyy-MM-dd') === format(today, 'yyyy-MM-dd')) return 'Today';
        if (format(date, 'yyyy-MM-dd') === format(yesterday, 'yyyy-MM-dd')) return 'Yesterday';
        return format(date, 'PPPP');
    };

    if (loading) return <div className="p-12 text-center text-gray-400">Loading History...</div>;

    return (
        <div className="max-w-4xl mx-auto space-y-12 pb-20">
            <div className="flex flex-col gap-2">
                <h2 className="text-4xl font-black text-slate-900 dark:text-white tracking-tight">Learning Log</h2>
                <p className="text-slate-500 dark:text-slate-400 font-medium">Your progress journey, recorded day by day.</p>
                
                
                {/* Manual Filter UI */}
                <div className="flex flex-wrap gap-4 mt-6">
                    <div className="relative group">
                        <select
                            value={filterTestId || ''}
                            onChange={(e) => setSearchParams(e.target.value ? { test_id: e.target.value } : {})}
                            className="appearance-none bg-white dark:bg-slate-800 font-bold text-slate-700 dark:text-slate-200 pl-4 pr-10 py-3 rounded-xl border border-slate-200 dark:border-slate-700 focus:outline-none focus:ring-4 focus:ring-blue-100 dark:focus:ring-blue-900/30 focus:border-blue-300 transition-all cursor-pointer shadow-sm hover:border-blue-300 min-w-[200px]"
                        >
                            <option value="">All Tests</option>
                            {uniqueTestIds.map(id => (
                                <option key={id} value={id}>{id}</option>
                            ))}
                        </select>
                        <ChevronDown size={16} className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none group-hover:text-blue-500 transition-colors" />
                    </div>

                    {filterTestId && (
                        <div className="flex items-center gap-3 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 px-4 py-3 rounded-xl border border-blue-100 dark:border-blue-800 animate-fade-in shadow-sm">
                            <div className="bg-blue-200 dark:bg-blue-800 p-1 rounded-lg">
                                <Filter size={14} className="text-blue-700 dark:text-blue-300" />
                            </div>
                            <span className="font-bold text-sm">Active: <span className="font-black">{filterTestId}</span></span>
                            <button 
                                onClick={() => setSearchParams({})}
                                className="ml-2 hover:bg-blue-200/50 p-1 rounded-full transition-colors"
                            >
                                <X size={14} />
                            </button>
                        </div>
                    )}
                </div>
            </div>
            
            {filteredHistory.length === 0 ? (
                <div className="text-center py-24 bg-slate-50 rounded-[3rem] border border-dashed border-slate-200">
                    <div className="bg-white w-20 h-20 rounded-3xl shadow-sm border border-slate-100 flex items-center justify-center mx-auto mb-6">
                         <Calendar className="text-slate-300" size={32} />
                    </div>
                    <h3 className="text-lg font-bold text-slate-900 mb-2">No history yet</h3>
                    <p className="text-slate-400 max-w-xs mx-auto">Start your first test to see your learning progress recorded here.</p>
                </div>
            ) : (
                <div className="space-y-12 relative">
                    {/* Vertical Timeline Line */}
                    <div className="absolute left-6 top-4 bottom-0 w-px bg-slate-200 hidden md:block" />

                    {sortedDates.map((date) => (
                        <div key={date} className="space-y-6 relative">
                            {/* Date Header */}
                            <div className="flex items-center gap-4">
                                <div className="hidden md:flex w-12 h-12 rounded-2xl bg-white dark:bg-slate-800 border-2 border-slate-100 dark:border-slate-700 items-center justify-center z-10 shadow-sm text-slate-400">
                                    <Clock size={20} />
                                </div>
                                <h3 className="text-xl font-black text-slate-800 dark:text-white bg-white dark:bg-slate-950 pr-4">{formatDateHeader(date)}</h3>
                            </div>

                            {/* Daily Items */}
                            <div className="grid gap-4 md:ml-16">
                                {grouped[date].map((item) => (
                                    <Link 
                                        to={`/result/${item.id}`} 
                                        key={item.id} 
                                        className="group bg-white dark:bg-slate-800 p-6 rounded-3xl shadow-sm border border-slate-100 dark:border-slate-700 flex items-center justify-between hover:shadow-xl hover:border-blue-100 dark:hover:border-blue-700 transition-all duration-300"
                                    >
                                        <div className="flex items-center gap-6">
                                            <div className="w-16 h-16 rounded-2xl bg-slate-50 dark:bg-slate-700 text-slate-900 dark:text-white flex flex-col items-center justify-center border border-slate-100 dark:border-slate-600 group-hover:bg-blue-600 group-hover:text-white group-hover:border-blue-600 transition-all">
                                                <span className="text-[10px] font-black uppercase tracking-tighter opacity-50 mb-0.5">SCORE</span>
                                                <span className="text-2xl font-black leading-none">{item.score}</span>
                                            </div>
                                            
                                            <div className="space-y-1">
                                                <h4 className="font-bold text-lg text-slate-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors uppercase tracking-tight">{item.test_id}</h4>
                                                <div className="flex items-center gap-4 text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest">
                                                    <span className="flex items-center gap-1.5"><Clock size={12}/> {format(new Date(item.timestamp), 'HH:mm:ss')}</span>
                                                    <span className="flex items-center gap-1.5"><Target size={12}/> {item.correct_count}/{item.total_questions} PTS</span>
                                                </div>
                                            </div>
                                        </div>

                                        <div className="hidden sm:flex items-center justify-center w-10 h-10 rounded-full bg-slate-50 dark:bg-slate-700 text-slate-300 dark:text-slate-500 group-hover:bg-blue-50 dark:group-hover:bg-blue-900/30 group-hover:text-blue-500 dark:group-hover:text-blue-400 transition-all">
                                            <Target size={18} />
                                        </div>
                                    </Link>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}
