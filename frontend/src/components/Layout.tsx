import React from 'react';
import { Link, Outlet } from 'react-router-dom';
import { BookOpen, Home, BarChart2, Settings, Terminal } from 'lucide-react';

export default function Layout() {
  return (
    <div className="flex h-screen bg-gray-50 text-gray-900 font-sans">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-6 border-b border-gray-100">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
            TOEIC Master
          </h1>
        </div>
        
        <nav className="flex-1 p-4 space-y-2">
          <NavItem to="/" icon={<Home size={20} />} label="Dashboard" />
          <NavItem to="/tests" icon={<BookOpen size={20} />} label="Tests" />
          <NavItem to="/history" icon={<BarChart2 size={20} />} label="History" />
          <NavItem to="/pipeline" icon={<Terminal size={20} />} label="Pipeline" />
          <NavItem to="/settings" icon={<Settings size={20} />} label="Settings" />
        </nav>
        
        <div className="p-4 border-t border-gray-100 text-xs text-gray-400">
          v1.0.0
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <header className="h-16 bg-white/80 backdrop-blur-md sticky top-0 z-10 border-b border-gray-200 px-8 flex items-center justify-between">
           <div className="font-medium text-gray-500">Welcome back</div>
           <div className="flex items-center gap-4">
              <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-bold">
                U
              </div>
           </div>
        </header>
        <div className="p-8 max-w-7xl mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
  );
}

function NavItem({ to, icon, label }: { to: string; icon: React.ReactNode; label: string }) {
  return (
    <Link to={to} className="flex items-center gap-3 px-4 py-3 text-gray-600 hover:bg-blue-50 hover:text-blue-600 rounded-lg transition-colors font-medium">
      {icon}
      <span>{label}</span>
    </Link>
  );
}
