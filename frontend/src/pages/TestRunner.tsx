import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import type { TestDetail, Question } from '../types';
import AudioPlayer from '../components/AudioPlayer';
import DictationInput from '../components/DictationInput';
import { cn } from '../lib/utils';

export default function TestRunner() {
  const { testId } = useParams<{ testId: string }>();
  const [test, setTest] = useState<TestDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [transcripts, setTranscripts] = useState<Record<string, Record<string, string>>>({}); // dictation state
  const [notes, setNotes] = useState<Record<string, string>>({}); // reading rationale
  const navigate = useNavigate();

  useEffect(() => {
    if (!testId) return;
    api.get<TestDetail>(`/tests/${testId}`)
      .then(res => setTest(res.data))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, [testId]);

  const handleSelect = (questionId: string, option: string) => {
      setAnswers(prev => ({ ...prev, [questionId]: option }));
  };
  
  const handleDictation = (id: string, key: string, text: string) => {
      setTranscripts(prev => ({
          ...prev,
          [id]: {
              ...(prev[id] || {}),
              [key]: text
          }
      }));
  }

  const handleNote = (questionId: string, text: string) => {
      setNotes(prev => ({ ...prev, [questionId]: text }));
  }

  const handleSubmit = async () => {
    if (!test) return;
    
    // Calculate Score
    let correct = 0;
    let total = 0;
    
    test.parts.forEach(part => {
        if (part.questions) {
            part.questions.forEach(q => {
                total++;
                if (q.correct_answer === answers[q.id]) correct++;
            });
        }
        if (part.groups) {
            part.groups.forEach(group => {
                group.questions.forEach(q => {
                    total++;
                    if (q.correct_answer === answers[q.id]) correct++;
                });
            });
        }
    });

    const score = Math.round((correct / total) * 990) || 0;
    
    const resultId = `${test.test_id}_${Date.now()}`;
    const result = {
        id: resultId,
        test_id: test.test_id,
        timestamp: new Date().toISOString(),
        score,
        total_questions: total,
        correct_count: correct,
        answers,
        user_transcripts: transcripts,
        user_notes: notes
    };

    try {
        await api.post('/results', result);
        navigate(`/result/${resultId}`, { state: { result, test } }); 
    } catch (error) {
        console.error("Failed to submit", error);
        alert("Failed to submit result. Please try again.");
    }
  };

  const renderQuestion = (q: Question, partNumber: number) => {
    return (
      <div key={q.id} className="space-y-6">
          <div className="flex gap-6">
              <span className={cn(
                  "font-black w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 border-2 transition-all text-sm",
                  answers[q.id] ? "bg-blue-600 text-white border-blue-600 shadow-md shadow-blue-100" : "bg-white text-gray-400 border-gray-100"
              )}>
                  {q.id.replace(/^.*q/, '')}
              </span>
              <div className="flex-1 space-y-6">
                  {/* Standalone Audio only for Part 1-2 */}
                  {partNumber <= 2 && q.audio && <AudioPlayer src={`${test?.test_id}/${q.audio}`} />}
                  
                  {q.image && (
                      <div className="border border-gray-100 rounded-2xl overflow-hidden max-w-lg shadow-sm">
                          <img 
                              src={`http://localhost:8000/static/${test?.test_id}/${q.image}`} 
                              alt={`Question ${q.id}`}
                              className="w-full h-auto"
                          />
                      </div>
                  )}

                  {q.text && <p className="font-bold text-xl text-gray-900">{q.text}</p>}

                  {/* Part 2: Transcription of the Question itself is key */}
                  {partNumber === 2 && (
                      <div className="space-y-3 bg-blue-50/20 p-6 rounded-3xl border border-blue-50/50">
                          <label className="text-[10px] font-black text-blue-400 uppercase tracking-widest pl-1">Question Transcription</label>
                          <DictationInput 
                              value={transcripts[q.id]?.['question'] || ""}
                              onChange={(val) => handleDictation(q.id, 'question', val)}
                              placeholder="What was the question exactly? (e.g. Where is the...)"
                              className="bg-white border-blue-100"
                          />
                      </div>
                  )}

                  {partNumber >= 5 && (
                      <div className="space-y-2">
                          <DictationInput 
                              value={notes[q.id] || ""}
                              onChange={(val) => handleNote(q.id, val)}
                              placeholder="Why did you choose this answer? (Rationale)"
                              className="bg-blue-50/30 border-blue-100"
                          />
                      </div>
                  )}

                  <div className="grid grid-cols-1 gap-4">
                      {(q.options || ['A', 'B', 'C', partNumber === 1 ? 'D' : null].filter(Boolean)).map((opt, idx) => {
                          const optionKey = q.options ? ['A','B','C','D'][idx] : opt as string; 
                          const isSelected = answers[q.id] === optionKey;

                          return (
                              <div key={idx} className="space-y-2">
                                  <label 
                                      className={cn(
                                          "flex items-center gap-4 p-5 rounded-2xl border-2 cursor-pointer transition-all",
                                          isSelected ? "border-blue-500 bg-blue-50/50" : "border-gray-100 hover:border-blue-200 hover:bg-gray-50"
                                      )}
                                  >
                                      <input 
                                          type="radio" 
                                          name={q.id} 
                                          value={optionKey}
                                          checked={isSelected}
                                          onChange={() => handleSelect(q.id, optionKey)}
                                          className="hidden"
                                      />
                                      <div className={cn(
                                          "w-8 h-8 rounded-full border-2 flex items-center justify-center text-sm font-black transition-all",
                                          isSelected ? "border-blue-600 bg-blue-600 text-white shadow-sm" : "border-gray-200 text-gray-400"
                                      )}>
                                          {optionKey}
                                      </div> 
                                      <span className={cn("font-bold text-lg", isSelected ? "text-blue-900" : "text-gray-700")}>
                                          {q.options ? opt : `Option ${opt}`}
                                      </span>
                                  </label>
                                  
                                  {partNumber <= 2 && (
                                      <div className="pl-12">
                                          <DictationInput 
                                              value={transcripts[q.id]?.[optionKey] || ""}
                                              onChange={(val) => handleDictation(q.id, optionKey, val)}
                                              placeholder={partNumber === 1 ? `Transcribe statement ${optionKey}...` : `Transcribe response ${optionKey}...`}
                                              className="bg-white/50 border-gray-100 text-sm"
                                          />
                                      </div>
                                  )}
                              </div>
                          )
                      })}
                  </div>
              </div>
          </div>
      </div>
    );
  };

  if (loading) return <div className="p-8 text-center text-gray-500">Loading test content...</div>;
  if (!test) return <div className="p-8 text-center text-red-500">Test not found.</div>;

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-32">
        <header className="mb-6 flex justify-between items-center bg-white p-6 rounded-2xl shadow-sm border border-gray-100 sticky top-20 z-10">
            <div>
                <h1 className="text-xl font-bold text-gray-900">{test.title}</h1>
                <p className="text-sm text-gray-500 font-medium">{Object.keys(answers).length} questions answered</p>
            </div>
            <button onClick={handleSubmit} className="px-8 py-3 bg-blue-600 text-white font-bold rounded-xl hover:bg-blue-700 transition shadow-lg">
                Submit Test
            </button>
        </header>

        {test.parts.map(part => (
            <div key={part.part_number} className="bg-white rounded-3xl p-8 shadow-sm border border-gray-100 mb-12">
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-black text-gray-800 tracking-tight">Part {part.part_number}</h2>
                </div>
                
                <p className="text-gray-500 font-medium mb-8 leading-relaxed border-l-4 border-blue-500 pl-4">{part.instructions}</p>

                <div className="space-y-12">
                    {part.questions?.map(q => renderQuestion(q, part.part_number))}

                    {part.groups?.map(group => (
                        <div key={group.id} className="p-8 bg-gray-50 rounded-3xl border border-gray-100 space-y-8">
                            <div className="space-y-6">
                                {group.audio && <AudioPlayer src={`${test.test_id}/${group.audio}`} />}
                                {group.passage_images?.map((img, idx) => (
                                    <img key={idx} src={`http://localhost:8000/static/${test.test_id}/${img}`} alt="Passage" className="w-full h-auto rounded-xl shadow-sm border border-gray-200" />
                                ))}
                                {group.passage_text && (
                                    <div className="prose prose-blue max-w-none whitespace-pre-wrap font-medium text-gray-800 leading-relaxed italic border-l-4 border-blue-200 pl-6 bg-white p-6 rounded-2xl shadow-sm">
                                        {group.passage_text}
                                    </div>
                                )}
                                {(part.part_number === 3 || part.part_number === 4) && (
                                    <DictationInput 
                                        value={transcripts[group.id]?.['main'] || ""}
                                        onChange={(val) => handleDictation(group.id, 'main', val)}
                                        placeholder="Transcribe the talk/conversation..."
                                        className="bg-white p-4 rounded-2xl border-dashed border-2 border-blue-100"
                                    />
                                )}
                            </div>
                            <div className="space-y-12 pl-4 border-l-2 border-gray-100 ml-2">
                                {group.questions.map(q => renderQuestion(q, part.part_number))}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        ))}
    </div>
  );
}
