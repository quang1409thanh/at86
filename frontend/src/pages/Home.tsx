import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { TestSummary } from '../types';
import { Play } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function Home() {
  const [tests, setTests] = useState<TestSummary[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    api.get<TestSummary[]>('/tests').then(res => setTests(res.data));
  }, []);

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-3xl font-bold text-gray-900">Available Tests</h2>
        <p className="text-gray-500 mt-2">Select a test to begin your practice session.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {tests.map(test => (
          <div key={test.test_id} className="group bg-white rounded-2xl p-6 shadow-sm border border-gray-100 hover:shadow-xl hover:-translate-y-1 transition-all duration-300">
            <div className="h-40 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl mb-6 flex items-center justify-center text-white relative overflow-hidden">
               <div className="absolute inset-0 bg-white/10 opacity-0 group-hover:opacity-20 transition-opacity" />
               <span className="text-4xl font-bold opacity-30">TOEIC</span>
            </div>
            
            <h3 className="text-xl font-bold text-gray-900 mb-2 group-hover:text-blue-600 transition-colors">
              {test.title}
            </h3>
            <p className="text-gray-400 text-sm mb-6">Test ID: {test.test_id}</p>
            
            <button 
              onClick={() => navigate(`/test/${test.test_id}`)}
              className="w-full py-3 bg-gray-50 text-gray-900 font-semibold rounded-xl hover:bg-blue-600 hover:text-white transition-all flex items-center justify-center gap-2"
            >
              <Play size={18} fill="currentColor" />
              Start Test
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
