import { useEffect, useState } from 'react';
import { useLocation, Link, useParams } from 'react-router-dom';
import type { UserResult, TestDetail, Question } from '../types';
import { api } from '../api/client';
import { cn } from '../lib/utils';
import { CheckCircle, XCircle, Home, FileText, Loader2 } from 'lucide-react';
import DiffViewer from '../components/DiffViewer';
import AudioPlayer from '../components/AudioPlayer';

export default function ResultPage() {
    const { resultId } = useParams<{ resultId: string }>();
    const location = useLocation();
    
    const [result, setResult] = useState<UserResult | null>(location.state?.result || null);
    const [test, setTest] = useState<TestDetail | null>(location.state?.test || null);
    const [loading, setLoading] = useState(!result || !test);

    useEffect(() => {
        if (!resultId) return;
        if (result && test) return;

        const fetchData = async () => {
            try {
                setLoading(true);
                const resResponse = await api.get<UserResult>(`/toeic/results/${resultId}`);
                const resData = resResponse.data;
                setResult(resData);
                
                const testResponse = await api.get<TestDetail>(`/toeic/tests/${resData.test_id}`);
                setTest(testResponse.data);
            } catch (err) {
                console.error("Failed to load result data", err);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [resultId]);

    if (loading) return (
        <div className="p-24 flex flex-col items-center justify-center space-y-4">
            <Loader2 className="animate-spin text-blue-600" size={48} />
            <p className="text-gray-500 font-medium">Loading your results...</p>
        </div>
    );

    if (!result || !test) return (
        <div className="max-w-xl mx-auto mt-20 p-8 bg-white dark:bg-slate-800 rounded-3xl shadow-sm border border-gray-100 dark:border-slate-700 text-center space-y-6">
            <XCircle className="mx-auto text-red-500" size={64} />
            <h2 className="text-2xl font-bold dark:text-white">Error Loading Results</h2>
            <p className="text-gray-500 dark:text-gray-400">We couldn't find the result you were looking for.</p>
            <Link to="/history" className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white font-bold rounded-xl hover:bg-blue-700 transition">
                <FileText size={18} /> View History
            </Link>
        </div>
    );

    function renderResultQuestion(q: Question, partNumber: number) {
        if (!result || !test) return null;
        const userAnswer = result.answers[q.id];
        const isCorrect = userAnswer === q.correct_answer;

        return (
            <div key={q.id} className="p-6 rounded-3xl border border-transparent hover:border-gray-100 dark:hover:border-slate-700 hover:bg-white dark:hover:bg-slate-800 transition-all">
                <div className="flex gap-6">
                    <div className="flex flex-col items-center gap-2">
                        <span className={cn(
                            "font-black w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 border-2 text-sm",
                            isCorrect ? "bg-green-50 text-green-600 border-green-200 shadow-sm" : "bg-red-50 text-red-600 border-red-200 shadow-sm"
                        )}>
                            {q.id.replace(/^.*q/, '')}
                        </span>
                        {isCorrect ? <CheckCircle className="text-green-500" size={16} /> : <XCircle className="text-red-500" size={16} />}
                    </div>
                    
                    <div className="flex-1 space-y-6">
                        {/* Audio/Image Context at Question Level */}
                        {partNumber <= 2 && q.audio && <AudioPlayer src={`${test.test_id}/${q.audio}`} />}
                        {q.image && (
                            <div className="border border-gray-100 dark:border-slate-700 rounded-2xl overflow-hidden max-w-sm shadow-sm bg-white dark:bg-black">
                                <img src={`http://localhost:8000/static/${test.test_id}/${q.image}`} alt={`Question ${q.id}`} className="w-full h-auto" />
                            </div>
                        )}

                        {q.text && <p className="text-xl font-black text-gray-900 dark:text-white leading-tight">{q.text}</p>}

                        {/* Part 2: Transcription of the Question itself (Top level) */}
                        {partNumber === 2 && q.transcripts?.['question'] && (
                            <div className="p-5 bg-blue-50/30 rounded-2xl border border-blue-100 shadow-sm space-y-3">
                                <div className="flex items-center gap-2 text-blue-800 font-black uppercase text-[10px] tracking-widest pl-1">
                                    <FileText size={14} /> Question Transcript Review
                                </div>
                                <DiffViewer 
                                    userText={result.user_transcripts?.[q.id]?.['question'] || ""}
                                    correctText={q.transcripts['question']}
                                />
                            </div>
                        )}
                        
                        {/* All Options with Selection State */}
                        <div className="grid grid-cols-1 gap-3">
                            {(q.options || ['A', 'B', 'C', partNumber === 1 ? 'D' : null].filter(Boolean)).map((opt, idx) => {
                                const optKey = q.options ? ['A','B','C','D'][idx] : opt as string;
                                const isUserChoice = userAnswer === optKey;
                                const isCorrectOpt = q.correct_answer === optKey;

                                return (
                                    <div key={idx} className="space-y-3">
                                        <div className={cn(
                                            "flex items-center gap-4 p-4 rounded-2xl border-2 transition-all",
                                            isCorrectOpt ? "border-green-500 bg-green-50/30 dark:bg-green-900/20" : 
                                            isUserChoice ? "border-red-500 bg-red-50/30 dark:bg-red-900/20" : "border-gray-50 dark:border-slate-700 bg-white dark:bg-slate-800"
                                        )}>
                                            <div className={cn(
                                                "w-8 h-8 rounded-full border-2 flex items-center justify-center text-xs font-black",
                                                isCorrectOpt ? "border-green-600 bg-green-600 text-white" :
                                                isUserChoice ? "border-red-600 bg-red-600 text-white" : "border-gray-200 text-gray-400"
                                            )}>
                                                {optKey}
                                            </div>
                                            <span className={cn(
                                                "font-bold text-base",
                                                isCorrectOpt ? "text-green-900 dark:text-green-400" :
                                                isUserChoice ? "text-red-900 dark:text-red-400" : "text-gray-700 dark:text-gray-300"
                                            )}>
                                                {q.options ? opt : `Option ${opt}`}
                                            </span>
                                            <div className="ml-auto">
                                                {isCorrectOpt && <CheckCircle className="text-green-600" size={18} />}
                                                {isUserChoice && !isCorrectOpt && <XCircle className="text-red-600" size={18} />}
                                            </div>
                                        </div>

                                        {/* Transcript Review per Option (Parts 1 & 2) */}
                                        {partNumber <= 2 && q.transcripts?.[optKey!] && (
                                            <div className="ml-12 p-4 bg-white/50 dark:bg-slate-800/50 rounded-xl border border-gray-100 dark:border-slate-700 shadow-inner">
                                                <div className="flex items-center justify-between mb-2">
                                                    <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Transcript Comparison</span>
                                                </div>
                                                <DiffViewer 
                                                    userText={result.user_transcripts?.[q.id]?.[optKey!] || ""} 
                                                    correctText={q.transcripts[optKey!]} 
                                                />
                                            </div>
                                        )}
                                    </div>
                                )
                            })}
                        </div>


                        {/* Reading Rationale and Explanation */}
                        {partNumber >= 5 && (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
                                {result.user_notes?.[q.id] && (
                                    <div className="p-5 bg-blue-50/40 rounded-2xl border border-blue-100 space-y-2">
                                        <div className="flex items-center gap-2 text-blue-800 font-black uppercase text-[10px] tracking-widest">
                                            <FileText size={14} /> My Rationale
                                        </div>
                                        <p className="text-gray-700 text-sm font-medium leading-relaxed italic">"{result.user_notes[q.id]}"</p>
                                    </div>
                                )}
                                {q.explanation && (
                                    <div className="p-5 bg-yellow-50/40 rounded-2xl border border-yellow-100 space-y-2">
                                        <div className="flex items-center gap-2 text-yellow-800 font-black uppercase text-[10px] tracking-widest">
                                            Expert Explanation
                                        </div>
                                        <p className="text-gray-700 text-sm font-medium leading-relaxed italic">{q.explanation}</p>
                                    </div>
                                )}
                            </div>
                        )}
                        {! (partNumber >= 5) && q.explanation && (
                             <div className="p-5 bg-yellow-50/40 rounded-2xl border border-yellow-100 space-y-2">
                                <div className="flex items-center gap-2 text-yellow-800 font-black uppercase text-[10px] tracking-widest">
                                    Expert Explanation
                                </div>
                                <p className="text-gray-700 text-sm font-medium leading-relaxed italic">{q.explanation}</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        );
    };

    return (
        <div className="max-w-4xl mx-auto space-y-8 pb-32">
            <header className="flex items-center justify-between bg-white dark:bg-slate-800 p-8 rounded-3xl shadow-sm border border-gray-100 dark:border-slate-700">
                <div className="space-y-1">
                    <h1 className="text-3xl font-black text-gray-900 dark:text-white tracking-tight">{test.title}</h1>
                    <p className="text-gray-500 dark:text-gray-400 font-medium">Completed on {new Date(result.timestamp).toLocaleDateString()}</p>
                </div>
                <Link to="/" className="p-3 rounded-2xl bg-gray-50 dark:bg-slate-700 text-gray-400 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/30 transition shadow-inner">
                    <Home size={28} />
                </Link>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-blue-600 rounded-3xl p-8 text-white shadow-xl shadow-blue-100 flex flex-col items-center justify-center text-center">
                    <div className="text-5xl font-black mb-2">{result.score}</div>
                    <div className="text-blue-100 font-bold uppercase tracking-widest text-xs">Estimated Score</div>
                </div>
                <div className="bg-white dark:bg-slate-800 rounded-3xl p-8 border border-gray-100 dark:border-slate-700 shadow-sm flex flex-col items-center justify-center text-center">
                    <div className="text-4xl font-black text-green-600 dark:text-green-400 mb-2">{result.correct_count} / {result.total_questions}</div>
                    <div className="text-gray-400 font-bold uppercase tracking-widest text-xs">Accuracy</div>
                </div>
                <div className="bg-white dark:bg-slate-800 rounded-3xl p-8 border border-gray-100 dark:border-slate-700 shadow-sm flex flex-col items-center justify-center text-center">
                    <div className="text-4xl font-black text-blue-600 dark:text-blue-400 mb-2 text-center flex items-center justify-center">
                        {Math.round((result.correct_count / result.total_questions) * 100)}%
                    </div>
                    <div className="text-gray-400 font-bold uppercase tracking-widest text-xs">Performance Percentage</div>
                </div>
            </div>

            <div className="space-y-12">
                {test.parts.map(part => (
                    <div key={part.part_number} className="bg-white dark:bg-slate-800 rounded-3xl p-8 shadow-sm border border-gray-100 dark:border-slate-700">
                        <div className="flex items-center justify-between mb-8">
                            <h2 className="text-2xl font-black text-gray-800 dark:text-white tracking-tight">Part {part.part_number}</h2>
                        </div>

                        <div className="space-y-12">
                            {part.questions?.map(q => renderResultQuestion(q, part.part_number))}

                            {part.groups?.map(group => (
                                <div key={group.id} className="p-8 bg-gray-50/50 dark:bg-slate-700/30 rounded-3xl border border-gray-100 dark:border-slate-700 space-y-8">
                                    <div className="space-y-6">
                                        <div className="px-4 py-2 bg-blue-600 text-white text-[10px] font-black uppercase rounded-full w-fit tracking-widest">Shared Context</div>
                                        {group.audio && <AudioPlayer src={`${test.test_id}/${group.audio}`} />}
                                        {group.passage_images?.map((img, idx) => (
                                            <img key={idx} src={`http://localhost:8000/static/${test.test_id}/${img}`} alt="Passage" className="w-full h-auto rounded-xl shadow-sm border border-gray-200" />
                                        ))}
                                        {group.passage_text && (
                                            <div className="prose prose-blue max-w-none whitespace-pre-wrap font-medium text-gray-800 dark:text-gray-200 leading-relaxed italic border-l-4 border-blue-400 pl-6 bg-white dark:bg-slate-900 p-6 rounded-2xl shadow-sm">
                                                {group.passage_text}
                                            </div>
                                        )}
                                        {(part.part_number === 3 || part.part_number === 4) && group.transcripts?.['main'] && (
                                            <div className="space-y-4">
                                                <div className="flex items-center gap-2 text-blue-800 font-black uppercase text-xs tracking-widest border-l-4 border-blue-600 pl-2">
                                                    <FileText size={14} /> Full Transcript Review
                                                </div>
                                                <DiffViewer userText={result.user_transcripts?.[group.id]?.['main'] || ""} correctText={group.transcripts['main']} />
                                            </div>
                                        )}
                                    </div>
                                    <div className="space-y-12 pl-4 border-l-2 border-dashed border-gray-200 ml-2">
                                        {group.questions.map(q => renderResultQuestion(q, part.part_number))}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
