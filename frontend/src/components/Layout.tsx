import React from 'react';
import { Link, Outlet } from 'react-router-dom';
import { BookOpen, Home, BarChart2, Settings, Terminal, Code, Zap, Menu, Moon, Sun, ChevronLeft, ChevronRight } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

export default function Layout() {
  const { sidebarOpen, toggleSidebar, darkMode, toggleTheme } = useAuth();

  return (
    <div className={`flex h-screen font-sans transition-colors duration-300 ${darkMode ? 'bg-slate-900 text-slate-100' : 'bg-gray-50 text-gray-900'}`}>
      {/* Sidebar */}
      <aside 
        className={`${sidebarOpen ? 'w-64' : 'w-20'} 
        bg-white dark:bg-slate-800 border-r border-gray-200 dark:border-slate-700 
        flex flex-col transition-all duration-300 relative z-20`}
      >
        {/* Toggle Button (Absolute) */}
        <button 
            onClick={toggleSidebar}
            className="absolute -right-3 top-9 bg-white dark:bg-slate-700 border border-gray-200 dark:border-slate-600 rounded-full p-1 shadow-md hover:bg-gray-100 dark:hover:bg-slate-600 transition-colors z-50"
        >
            {sidebarOpen ? <ChevronLeft size={14} className="text-slate-600 dark:text-slate-300" /> : <ChevronRight size={14} className="text-slate-600 dark:text-slate-300" />}
        </button>

        <div className={`p-6 border-b border-gray-100 dark:border-slate-700 flex items-center ${sidebarOpen ? 'justify-between' : 'justify-center'}`}>
          {sidebarOpen ? (
            <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent truncate">
              TOEIC Master
            </h1>
          ) : (
             <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center font-black text-white text-xs">TM</div>
          )}
        </div>
        
        <nav className="flex-1 p-3 space-y-2 overflow-y-auto overflow-x-hidden custom-scrollbar">
          <NavItem to="/" icon={<Home size={20} />} label="Dashboard" collapsed={!sidebarOpen} />
          <NavItem to="/tests" icon={<BookOpen size={20} />} label="Tests" collapsed={!sidebarOpen} />
          <NavItem to="/history" icon={<BarChart2 size={20} />} label="History" collapsed={!sidebarOpen} />
          <NavItem to="/coach" icon={<Zap size={20} />} label="AI Coach" collapsed={!sidebarOpen} />
          <NavItem to="/pipeline" icon={<Terminal size={20} />} label="Pipeline" collapsed={!sidebarOpen} />
          
          <div className={`pt-4 mt-4 border-t border-gray-100 dark:border-slate-700 transition-all ${!sidebarOpen && 'hidden'}`}>
             <p className="px-4 text-[10px] font-black text-gray-400 uppercase tracking-widest mb-2 truncate">System</p>
             <NavItem to="/api-docs" icon={<Code size={20} />} label="API Resources" collapsed={!sidebarOpen} />
             <NavItem to="/changelog" icon={<Zap size={20} />} label="Changelog" collapsed={!sidebarOpen} />
             <NavItem to="/settings" icon={<Settings size={20} />} label="Settings" collapsed={!sidebarOpen} />
          </div>
          {/* Icons only for system when collapsed */}
           {!sidebarOpen && (
              <>
                <div className="h-px bg-gray-100 dark:bg-slate-700 my-2" />
                <NavItem to="/api-docs" icon={<Code size={20} />} label="API" collapsed={true} />
                <NavItem to="/settings" icon={<Settings size={20} />} label="Settings" collapsed={true} />
              </>
           )}
        </nav>
        
        <div className="p-4 border-t border-gray-100 dark:border-slate-700">
             <button 
                onClick={toggleTheme}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-xl transition-colors ${
                    sidebarOpen 
                    ? 'bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-slate-300 hover:bg-gray-200 dark:hover:bg-slate-600' 
                    : 'justify-center text-gray-500 hover:text-blue-500'
                }`}
             >
                {darkMode ? <Sun size={20} /> : <Moon size={20} />}
                {sidebarOpen && <span className="font-medium text-sm">{darkMode ? 'Light Mode' : 'Dark Mode'}</span>}
             </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto bg-gray-50 dark:bg-slate-900 transition-colors duration-300 relative">
        <header className="h-16 bg-white/80 dark:bg-slate-800/80 backdrop-blur-md sticky top-0 z-10 border-b border-gray-200 dark:border-slate-700 px-8 flex items-center justify-between transition-colors duration-300">
           {/* Mobile Menu Button - Visible mainly on check for smaller screens if we added responsive later */}
           <div className="flex items-center gap-4">
               {!sidebarOpen && (
                   <button onClick={toggleSidebar} className="md:hidden p-2 -ml-2 text-gray-500">
                       <Menu size={20} />
                   </button>
               )}
               <div className="font-medium text-gray-500 dark:text-slate-400">Welcome back</div>
           </div>
           
           <div className="flex items-center gap-4">
              <Link to="/profile" className="w-9 h-9 rounded-full bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-300 flex items-center justify-center font-bold hover:bg-blue-200 dark:hover:bg-blue-800 transition-colors ring-2 ring-white dark:ring-slate-700 shadow-sm">
                U
              </Link>
           </div>
        </header>

        <div className="p-8 max-w-7xl mx-auto min-h-[calc(100vh-4rem)]">
          <Outlet />
        </div>
      </main>
    </div>
  );
}

function NavItem({ to, icon, label, collapsed }: { to: string; icon: React.ReactNode; label: string, collapsed: boolean }) {
  return (
    <Link 
        to={to} 
        className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 group relative
        ${collapsed ? 'justify-center' : ''}
        text-gray-600 dark:text-slate-400 
        hover:bg-blue-50 dark:hover:bg-slate-700/50 hover:text-blue-600 dark:hover:text-blue-400
        active:scale-95`}
        title={collapsed ? label : undefined}
    >
      <div className="transition-transform group-hover:scale-110 duration-200">
          {icon}
      </div>
      
      {!collapsed && (
          <span className="font-medium text-sm whitespace-nowrap overflow-hidden transition-all duration-300">
              {label}
          </span>
      )}

      {/* Active Indicator if needed, or just rely on hover/active class */}
    </Link>
  );
}
