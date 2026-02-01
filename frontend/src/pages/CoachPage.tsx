import { useState, useEffect, useRef } from 'react';
import { Brain, AlertCircle, CheckCircle2, Lightbulb, MessageSquare, Send, Loader2, BarChart3, Target, BookOpen, Headphones, ChevronRight, Sparkles, Bot, User, RefreshCw } from 'lucide-react';
import { api } from '../api/client';
import MarkdownRenderer from '../components/MarkdownRenderer';

interface MistakeAnalysis {
  total_mistakes: number;
  error_types: Record<string, { count: number; description: string }>;
  weak_parts: { part: number; error_count: number }[];
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export default function CoachPage() {
  const [analysis, setAnalysis] = useState<MistakeAnalysis | null>(null);
  const [coachAdvice, setCoachAdvice] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [selectedPart, setSelectedPart] = useState<number | null>(null);
  
  // Chat state
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadAnalysis();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadAnalysis = async () => {
    setIsLoading(true);
    try {
      const response = await api.get('/rag/analyze/default');
      setAnalysis(response.data.metadata?.error_summary || null);
      setCoachAdvice(response.data.answer || '');
    } catch (error) {
      console.error('Error loading analysis:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const regenerateAdvice = async () => {
    setIsGenerating(true);
    try {
      const response = await api.get('/rag/analyze/default');
      setCoachAdvice(response.data.answer || '');
    } catch (error) {
      console.error('Error regenerating:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSendMessage = async () => {
    if (!input.trim() || isChatLoading) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsChatLoading(true);

    try {
      const response = await api.post('/rag/chat', {
        query: input,
        user_id: 'default',
        collections: ['toeic', 'user']
      });

      const assistantMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.data.answer,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (error: any) {
      const errorMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Xin lỗi, có lỗi xảy ra: ${error.message}`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsChatLoading(false);
    }
  };

  const getPartIcon = (part: number) => {
    if (part <= 4) return <Headphones size={16} />;
    return <BookOpen size={16} />;
  };

  const getErrorTypeColor = (errorType: string) => {
    if (errorType.includes('listening')) return 'from-purple-500 to-indigo-600';
    if (errorType.includes('grammar')) return 'from-orange-500 to-red-500';
    if (errorType.includes('reading')) return 'from-blue-500 to-cyan-500';
    return 'from-gray-500 to-gray-600';
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-blue-500 mx-auto mb-4" />
          <p className="text-gray-500 dark:text-slate-400">Đang phân tích dữ liệu học tập...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
            <Brain className="w-7 h-7 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">TOEIC Coach</h1>
            <p className="text-gray-500 dark:text-slate-400">Phân tích lỗi sai & lộ trình cải thiện cá nhân hóa</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={async () => {
              if (window.confirm('Bạn có chắc chắn muốn xóa hết dữ liệu Coach? Hành động này không thể hoàn tác.')) {
                try {
                  await api.delete('/rag/reset/user');
                  alert('Đã xóa dữ liệu Coach thành công!');
                  loadAnalysis();
                } catch (error) {
                  alert('Lỗi khi xóa dữ liệu');
                }
              }
            }}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/50 transition-colors"
          >
            <AlertCircle size={18} />
            Xóa dữ liệu
          </button>
          
          <button
            onClick={regenerateAdvice}
            disabled={isGenerating}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-900/50 transition-colors disabled:opacity-50"
          >
            <RefreshCw size={18} className={isGenerating ? 'animate-spin' : ''} />
            Phân tích lại
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Stats */}
        <div className="lg:col-span-1 space-y-4">
          {/* Overview Card */}
          <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700 shadow-sm">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-orange-100 dark:bg-orange-900/30 flex items-center justify-center">
                <AlertCircle className="w-5 h-5 text-orange-600 dark:text-orange-400" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-white">Tổng lỗi sai</h3>
                <p className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                  {analysis?.total_mistakes || 0}
                </p>
              </div>
            </div>
          </div>

          {/* Weak Parts */}
          <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700 shadow-sm">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
              <Target size={18} className="text-red-500" />
              Parts cần cải thiện
            </h3>
            <div className="space-y-3">
              {analysis?.weak_parts?.map((item, idx) => (
                <button
                  key={idx}
                  onClick={() => setSelectedPart(item.part)}
                  className={`w-full flex items-center justify-between p-3 rounded-xl transition-colors ${
                    selectedPart === item.part
                      ? 'bg-red-50 dark:bg-red-900/30 border-2 border-red-200 dark:border-red-800'
                      : 'bg-gray-50 dark:bg-slate-700/50 hover:bg-gray-100 dark:hover:bg-slate-700'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                      item.part <= 4 ? 'bg-purple-100 dark:bg-purple-900/50 text-purple-600 dark:text-purple-400' : 'bg-blue-100 dark:bg-blue-900/50 text-blue-600 dark:text-blue-400'
                    }`}>
                      {getPartIcon(item.part)}
                    </div>
                    <span className="font-medium text-gray-800 dark:text-gray-200">Part {item.part}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-red-600 dark:text-red-400 font-semibold">{item.error_count} lỗi</span>
                    <ChevronRight size={16} className="text-gray-400" />
                  </div>
                </button>
              ))}
              {(!analysis?.weak_parts || analysis.weak_parts.length === 0) && (
                <div className="text-center py-4 text-gray-400">
                  <CheckCircle2 className="w-8 h-8 mx-auto mb-2 text-green-500" />
                  <p>Chưa có dữ liệu lỗi sai</p>
                </div>
              )}
            </div>
          </div>

          {/* Error Types */}
          <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700 shadow-sm">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
              <BarChart3 size={18} className="text-blue-500" />
              Phân loại lỗi
            </h3>
            <div className="space-y-3">
              {analysis?.error_types && Object.entries(analysis.error_types).map(([type, data], idx) => (
                <div key={idx} className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600 dark:text-slate-400 truncate">{data.description || type}</span>
                    <span className="font-semibold text-gray-900 dark:text-white">{data.count}</span>
                  </div>
                  <div className="h-2 bg-gray-100 dark:bg-slate-700 rounded-full overflow-hidden">
                    <div 
                      className={`h-full bg-gradient-to-r ${getErrorTypeColor(type)} rounded-full transition-all`}
                      style={{ width: `${Math.min((data.count / (analysis?.total_mistakes || 1)) * 100, 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column - Coach Advice & Chat */}
        <div className="lg:col-span-2 space-y-4">
          {/* Coach Advice */}
          <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700 shadow-sm">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center">
                <Lightbulb className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-white">Lời khuyên từ Coach</h3>
                <p className="text-sm text-gray-500 dark:text-slate-400">Dựa trên phân tích lỗi sai của bạn</p>
              </div>
            </div>
            
            <div className="prose prose-sm dark:prose-invert max-w-none">
              {isGenerating ? (
                <div className="flex items-center gap-2 text-gray-400">
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Đang tạo lời khuyên...
                </div>
              ) : (
                <MarkdownRenderer 
                  content={coachAdvice || 'Hãy làm thêm bài test để Coach có thể phân tích và đưa ra lời khuyên phù hợp!'} 
                  isAssistant
                />
              )}
            </div>
          </div>

          {/* Interactive Chat with Coach */}
          <div className="bg-white dark:bg-slate-800 rounded-2xl border border-gray-100 dark:border-slate-700 shadow-sm overflow-hidden">
            <div className="p-4 border-b border-gray-100 dark:border-slate-700 bg-gradient-to-r from-indigo-500/10 to-purple-500/10">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                  <MessageSquare className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-white">Hỏi Coach</h3>
                  <p className="text-sm text-gray-500 dark:text-slate-400">Hỏi chi tiết về lỗi sai, từ vựng, ngữ pháp...</p>
                </div>
              </div>
            </div>

            {/* Messages */}
            <div className="h-80 overflow-y-auto p-4 space-y-4 bg-gray-50 dark:bg-slate-900/50">
              {messages.length === 0 && (
                <div className="text-center py-8">
                  <Sparkles className="w-12 h-12 text-indigo-300 dark:text-indigo-700 mx-auto mb-3" />
                  <p className="text-gray-500 dark:text-slate-400">Hỏi Coach về bất kỳ điều gì!</p>
                  <div className="mt-4 flex flex-wrap justify-center gap-2">
                    {[
                      "Tại sao tôi hay sai Part 2?",
                      "Từ vựng nào tôi cần học?",
                      "Lộ trình học 1 tuần"
                    ].map((q, idx) => (
                      <button
                        key={idx}
                        onClick={() => setInput(q)}
                        className="text-xs bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 px-3 py-1.5 rounded-full hover:bg-indigo-100 dark:hover:bg-indigo-900/50 transition-colors"
                      >
                        {q}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {messages.map((msg) => (
                <div key={msg.id} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                    msg.role === 'user'
                      ? 'bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-300'
                      : 'bg-indigo-100 dark:bg-indigo-900 text-indigo-600 dark:text-indigo-300'
                  }`}>
                    {msg.role === 'user' ? <User size={16} /> : <Bot size={16} />}
                  </div>
                  <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                    msg.role === 'user'
                      ? 'bg-blue-500 text-white rounded-tr-sm shadow-md shadow-blue-500/20'
                      : 'bg-white dark:bg-slate-800 text-gray-800 dark:text-gray-200 rounded-tl-sm shadow-sm border border-gray-100 dark:border-slate-700'
                  }`}>
                    {msg.role === 'user' ? (
                      <p className="text-sm whitespace-pre-wrap font-medium">{msg.content}</p>
                    ) : (
                      <MarkdownRenderer content={msg.content} isAssistant />
                    )}
                  </div>
                </div>
              ))}

              {isChatLoading && (
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-full bg-indigo-100 dark:bg-indigo-900 flex items-center justify-center">
                    <Loader2 size={16} className="text-indigo-600 dark:text-indigo-300 animate-spin" />
                  </div>
                  <div className="bg-white dark:bg-slate-800 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm border border-gray-100 dark:border-slate-700">
                    <p className="text-sm text-gray-400">Đang suy nghĩ...</p>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="p-4 border-t border-gray-100 dark:border-slate-700">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                  placeholder="Hỏi Coach về lỗi sai, cách cải thiện..."
                  className="flex-1 px-4 py-3 rounded-xl bg-gray-100 dark:bg-slate-700 text-gray-800 dark:text-gray-200 placeholder-gray-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                  disabled={isChatLoading}
                />
                <button
                  onClick={handleSendMessage}
                  disabled={!input.trim() || isChatLoading}
                  className="px-4 py-3 rounded-xl bg-indigo-500 hover:bg-indigo-600 disabled:bg-gray-300 dark:disabled:bg-slate-600 text-white transition-colors"
                >
                  {isChatLoading ? <Loader2 size={20} className="animate-spin" /> : <Send size={20} />}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
