import { Code, ExternalLink, Shield, Server, Zap } from 'lucide-react';

export default function ApiDocs() {
  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-20">
      <header className="space-y-4">
        <h1 className="text-4xl font-black text-gray-900 dark:text-white tracking-tight">API Resources</h1>
        <p className="text-xl text-gray-500 dark:text-gray-400 font-medium">
          Comprehensive documentation for developers and integrators.
        </p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Main Swagger Link */}
        <div className="col-span-1 md:col-span-2 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-3xl p-8 text-white shadow-xl shadow-blue-200">
          <div className="flex items-start justify-between">
            <div className="space-y-4">
              <div className="p-3 bg-white/10 rounded-xl w-fit backdrop-blur-sm">
                <Server size={32} />
              </div>
              <div>
                <h2 className="text-2xl font-bold mb-2">Interactive API Reference</h2>
                <p className="text-blue-100 max-w-lg leading-relaxed">
                  Explore our REST endpoints using the standard OpenAPI (Swagger) interface. 
                  Test requests, inspect schemas, and view authentication requirements in real-time.
                </p>
              </div>
              <a 
                href="http://localhost:8000/docs" 
                target="_blank" 
                rel="noreferrer"
                className="inline-flex items-center gap-2 px-6 py-3 bg-white text-blue-700 font-bold rounded-xl hover:bg-blue-50 transition shadow-sm mt-4"
              >
                Open Swagger UI <ExternalLink size={18} />
              </a>
            </div>
            <div className="hidden md:block opacity-20 transform rotate-12">
               <Code size={180} />
            </div>
          </div>
        </div>

        {/* Authentication Info */}
        <div className="p-8 bg-white dark:bg-slate-800 rounded-3xl border border-gray-100 dark:border-slate-700 shadow-sm space-y-4">
            <div className="p-3 bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400 rounded-xl w-fit">
                <Shield size={24} />
            </div>
            <h3 className="text-xl font-bold text-gray-900 dark:text-white">Authentication</h3>
            <p className="text-gray-500 dark:text-gray-400 text-sm leading-relaxed">
                All API requests detailed in this documentation require a valid <code className="bg-gray-100 dark:bg-slate-700 px-1 py-0.5 rounded text-gray-800 dark:text-gray-200 font-mono text-xs">Bearer Token</code>. 
                Obtain one via the <code className="bg-gray-100 dark:bg-slate-700 px-1 py-0.5 rounded text-gray-800 dark:text-gray-200 font-mono text-xs">/api/auth/token</code> endpoint.
            </p>
        </div>

        {/* Quick Start */}
        <div className="p-8 bg-white dark:bg-slate-800 rounded-3xl border border-gray-100 dark:border-slate-700 shadow-sm space-y-4">
            <div className="p-3 bg-amber-50 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400 rounded-xl w-fit">
                <Zap size={24} />
            </div>
            <h3 className="text-xl font-bold text-gray-900 dark:text-white">Quick Start</h3>
            <div className="bg-slate-900 rounded-xl p-4 overflow-x-auto">
                <pre className="text-xs text-slate-300 font-mono">
                    curl -X POST "http://localhost:8000/api/auth/token" \<br/>
                    -H "Content-Type: multipart/form-data" \<br/>
                    -F "username=admin" \<br/>
                    -F "password=secret"
                </pre>
            </div>
        </div>
      </div>
    </div>
  );
}
