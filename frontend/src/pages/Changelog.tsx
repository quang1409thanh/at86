import { GitCommit } from 'lucide-react';

export default function Changelog() {
  const versions = [
    {
      version: "1.2.0",
      date: "Jan 31, 2026",
      title: "Navigation & Experience Refinement",
      color: "blue",
      changes: [
        "Implemented dedicated User Profile page with password management.",
        "Refactored Navigation: Removed Profile from sidebar for cleaner UI.",
        "Added System Documentation: API Resources and Changelog pages.",
        "Refactored Backend: Moved TOEIC endpoints to dedicated `/api/toeic` router."
      ]
    },
    {
        version: "1.1.0",
        date: "Jan 30, 2026",
        title: "Security & Clean Architecture",
        color: "emerald",
        changes: [
          "Implemented Clean Architecture (core, db, schemas, api, services).",
          "Added Role-Based Access Control (RBAC) with Admin/User roles.",
          "Secured Endpoints with JWT Authentication.",
          "Migrated to MySQL with Alembic migrations support."
        ]
    },
    {
        version: "1.0.0",
        date: "Jan 28, 2026",
        title: "Initial Release & Pipeline Core",
        color: "indigo",
        changes: [
          "Launched Core Pipeline for automated TOEIC test generation.",
          "Integrated Google Gemini 1.5/2.0 Models.",
          "Established basic Test Runner and Result Analytics.",
          "Implemented PDF-to-Test parsing capability."
        ]
    }
  ];

  return (
    <div className="max-w-3xl mx-auto space-y-8 pb-20">
      <header className="space-y-4 text-center mb-12">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 font-bold text-xs uppercase tracking-widest mb-2">
            <GitCommit size={14} /> System Updates
        </div>
        <h1 className="text-4xl font-black text-gray-900 dark:text-white tracking-tight">Changelog</h1>
        <p className="text-xl text-gray-500 dark:text-gray-400 font-medium">
            Tracking the evolution of the TOEIC Master platform.
        </p>
      </header>
      
      <div className="relative border-l-2 border-gray-100 dark:border-slate-800 ml-6 space-y-12">
        {versions.map((ver, idx) => (
            <div key={idx} className="relative pl-12">
                {/* Timeline Dot */}
                <div className={`absolute -left-[9px] top-0 w-5 h-5 rounded-full border-4 border-white dark:border-slate-900 shadow-sm flex items-center justify-center bg-${ver.color}-500`} />
                
                <div className="space-y-6">
                    <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4">
                         <span className={`px-3 py-1 rounded-lg bg-${ver.color}-50 dark:bg-${ver.color}-900/20 text-${ver.color}-700 dark:text-${ver.color}-400 font-black text-sm w-fit`}>
                            v{ver.version}
                         </span>
                         <span className="text-sm font-bold text-gray-400 dark:text-gray-500">{ver.date}</span>
                    </div>

                    <div className="p-8 bg-white dark:bg-slate-800 rounded-3xl border border-gray-100 dark:border-slate-700 shadow-sm hover:shadow-md transition-shadow">
                        <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-6 flex items-center gap-2">
                           {ver.title}
                        </h3>
                        <ul className="space-y-3">
                            {ver.changes.map((change, cIdx) => (
                                <li key={cIdx} className="flex items-start gap-3 text-gray-600 dark:text-gray-300 font-medium text-sm leading-relaxed">
                                    <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-gray-300 dark:bg-gray-600 flex-shrink-0" />
                                    {change}
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>
            </div>
        ))}
      </div>
    </div>
  );
}
