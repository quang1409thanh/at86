import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import type { UserResult } from '../types';
import { format } from 'date-fns';
import { Calendar, Target } from 'lucide-react';

export default function HistoryPage() {
    const [history, setHistory] = useState<UserResult[]>([]);

    useEffect(() => {
        api.get<UserResult[]>('/history').then(res => setHistory(res.data));
    }, []);

    return (
        <div className="space-y-6">
            <h2 className="text-2xl font-bold text-gray-900">Learning History</h2>
            
            {history.length === 0 ? (
                <div className="text-center p-12 bg-white rounded-2xl shadow-sm border border-gray-100">
                    <p className="text-gray-400">No test history available correctly.</p>
                </div>
            ) : (
                <div className="grid gap-4">
                    {history.map((item) => (
                        <Link to={`/result/${item.id}`} key={item.id} className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex items-center justify-between hover:shadow-md transition">
                            <div className="flex items-center gap-6">
                                <div className="w-16 h-16 rounded-full bg-yellow-50 text-yellow-600 flex flex-col items-center justify-center border-4 border-white shadow-sm">
                                    <span className="text-xs font-bold text-yellow-400">SCORE</span>
                                    <span className="text-xl font-black leading-none">{item.score}</span>
                                </div>
                                
                                <div>
                                    <h3 className="font-bold text-lg text-gray-900">{item.test_id}</h3>
                                    <div className="flex gap-4 text-sm text-gray-500 mt-1">
                                        <span className="flex items-center gap-1"><Calendar size={14}/> {format(new Date(item.timestamp), 'PP p')}</span>
                                        <span className="flex items-center gap-1"><Target size={14}/> {item.correct_count}/{item.total_questions} Correct</span>
                                    </div>
                                </div>
                            </div>
                        </Link>
                    ))}
                </div>
            )}
        </div>
    )
}
