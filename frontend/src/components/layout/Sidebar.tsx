/**
 * SEINENTAI4US — Sidebar
 */
import { useEffect } from 'react';
import { useRouter } from 'next/router';
import { motion, AnimatePresence } from 'framer-motion';
import {
  MessageSquare,
  Search,
  FileText,
  User,
  Settings,
  Activity,
  Plus,
  ChevronLeft,
  Shield,
  LayoutDashboard,
  MoreVertical,
  Trash2,
  Share2,
} from 'lucide-react';
import { useState } from 'react';
import { cn } from '@/lib/utils';
import { truncate, formatRelativeTime } from '@/lib/utils';
import { ROUTES } from '@/lib/constants';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { switchInterface, toggleSidebar, setSidebarOpen } from '@/store/slices/uiSlice';
import { useChat } from '@/hooks/useChat';
import { SessionSkeleton } from '@/components/ui/Skeleton';
import Popover from '@/components/ui/Popover';
import SocialShareButtons from '@/components/chat/SocialShareButtons';

interface NavItem {
  icon: typeof MessageSquare;
  label: string;
  href: string;
  adminOnly?: boolean;
  userOnly?: boolean;
}

const userNav: NavItem[] = [
  // { icon: MessageSquare, label: 'Chat RAG', href: ROUTES.CHAT },
  // { icon: Search, label: 'Recherche', href: ROUTES.SEARCH },
];

const adminNav: NavItem[] = [
  { icon: FileText, label: 'Documents', href: ROUTES.DOCUMENTS },
  { icon: Search, label: 'Recherche', href: ROUTES.SEARCH },
  { icon: Activity, label: 'Monitoring', href: ROUTES.ADMIN_MONITORING },
];

export default function Sidebar() {
  const router = useRouter();
  const dispatch = useAppDispatch();
  const { sidebarOpen, interfaceMode } = useAppSelector((s) => s.ui);
  const { 
    sessions, 
    activeSessionId, 
    sessionsLoading, 
    loadSessions, 
    loadSession, 
    newConversation,
    deleteSession 
  } = useChat();

  const [activeMenuId, setActiveMenuId] = useState<string | null>(null);

  const navItems = interfaceMode === 'admin' ? adminNav : userNav;

  useEffect(() => {
    if (interfaceMode === 'user') {
      loadSessions();
    }
  }, [loadSessions, interfaceMode]);

  // Close sidebar on mobile route change
  useEffect(() => {
    const handleRouteChange = () => {
      if (window.innerWidth < 768) {
        dispatch(setSidebarOpen(false));
      }
    };
    router.events.on('routeChangeComplete', handleRouteChange);
    return () => router.events.off('routeChangeComplete', handleRouteChange);
  }, [router.events, dispatch]);

  return (
    <>
      {/* Mobile overlay */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="md:hidden backdrop-overlay"
            onClick={() => dispatch(toggleSidebar())}
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed md:relative z-40 h-screen flex flex-col',
          'w-[280px] bg-white border-r border-slate-200/60 shadow-sm md:shadow-none',
          'transition-transform duration-300 ease-out',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 h-[65px] border-b border-slate-100/80">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center shadow-sm shadow-emerald-200">
              <span className="text-sm font-bold text-white">S</span>
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-900 leading-none tracking-tight">SEINENTAI4US</h2>
              <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-[0.1em] mt-1 block">
                {interfaceMode === 'admin' ? 'Admin Panel' : 'Assistant IA'}
              </span>
            </div>
          </div>
          <button
            onClick={() => dispatch(toggleSidebar())}
            className="p-1.5 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer md:hidden text-slate-400 hover:text-slate-600"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
        </div>

        {/* New Chat Button (user mode only) */}
        {interfaceMode === 'user' && (
          <div className="px-4 py-4">
            <button
              onClick={() => {
                newConversation();
                router.push(ROUTES.CHAT);
              }}
              className={cn(
                'w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl',
                'text-sm font-semibold text-white',
                'bg-gradient-to-r from-emerald-500 to-teal-600 shadow-sm shadow-emerald-100',
                'hover:shadow-md hover:shadow-emerald-200/50 hover:-translate-y-0.5',
                'transition-all duration-200 cursor-pointer',
                'active:scale-[0.98]'
              )}
            >
              <Plus className="w-4 h-4 stroke-[3px]" />
              Nouvelle conversation
            </button>
          </div>
        )}

        <hr className="border-slate-100/80 mx-4" />

        {/* Navigation */}
        {interfaceMode === 'admin' && (
        <nav className="px-3 pt-6">
          <p className="px-4 mb-3 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
            Menu Principal
          </p>
          <div className="space-y-1">
            {navItems.map((item) => {
              const isActive = router.pathname === item.href;
              return (
                <button
                  key={item.href}
                  onClick={() => router.push(item.href)}
                  className={cn(
                    'w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 cursor-pointer',
                    isActive
                      ? 'bg-emerald-50 text-emerald-700 shadow-sm border border-emerald-100/50'
                      : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                  )}
                >
                  <item.icon className={cn('w-[18px] h-[18px]', isActive ? 'text-emerald-500' : 'text-slate-400 group-hover:text-slate-600')} />
                  {item.label}
                </button>
              );
            })}
          </div>
        </nav>
        )}

        {/* Chat History (user mode) */}
        {interfaceMode === 'user' && (
          <div id="tour-sidebar-history" className="flex-1 flex flex-col min-h-0 mt-2">
            <p className="px-6 mb-3 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
              Historique
            </p>
            
            <div className="flex-1 overflow-y-auto modern-scrollbar px-3 pb-4 space-y-1">
              {sessionsLoading ? (
                <div className="px-3">
                  <SessionSkeleton />
                </div>
              ) : sessions.length === 0 ? (
                <div className="px-6 py-8 text-center">
                  <p className="text-xs text-slate-400 italic">Aucune conversation</p>
                </div>
              ) : (
                <div className="space-y-1">
                  {sessions.map((session) => (
                    <div
                      key={session.session_id}
                      role="button"
                      tabIndex={0}
                      onClick={() => {
                        loadSession(session.session_id);
                        router.push(ROUTES.CHAT);
                      }}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault();
                          loadSession(session.session_id);
                          router.push(ROUTES.CHAT);
                        }
                      }}
                      className={cn(
                        'w-full flex flex-col items-start gap-1 px-4 py-3 rounded-xl text-left transition-all duration-200 cursor-pointer group relative outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-inset',
                        activeSessionId === session.session_id
                          ? 'bg-emerald-50/50 text-emerald-800 border border-emerald-100/50'
                          : 'text-slate-600 hover:bg-slate-50/80 border border-transparent hover:border-slate-100'
                      )}
                    >
                      {/* Active indicator line */}
                      {activeSessionId === session.session_id && (
                        <div className="absolute left-0 top-3 bottom-3 w-1 bg-emerald-500 rounded-r-full" />
                      )}
                      
                      <div className="flex items-center gap-2 w-full pr-6">
                        <MessageSquare className={cn(
                          'w-3.5 h-3.5 flex-shrink-0 transition-colors',
                          activeSessionId === session.session_id ? 'text-emerald-500' : 'text-slate-400 group-hover:text-slate-500'
                        )} />
                        <p className="text-xs font-semibold truncate flex-1">
                          {session.title || 'Sans titre'}
                        </p>
                      </div>
                      
                      <div className="flex items-center justify-between w-full mt-1 px-5">
                        <span className="text-[10px] text-slate-400 font-medium">
                          {formatRelativeTime(session.updated_at || session.created_at)}
                        </span>
                        {session.message_count > 0 && (
                          <span className="text-[9px] text-slate-300 bg-slate-50 px-1.5 py-0.5 rounded-md border border-slate-100">
                            {session.message_count} msg
                          </span>
                        )}
                      </div>

                      {/* Session Actions Popover */}
                      <div className="absolute right-2 top-3 opacity-0 group-hover:opacity-100 transition-opacity">
                        <Popover
                          isOpen={activeMenuId === session.session_id}
                          onClose={() => setActiveMenuId(null)}
                          align="right"
                          position="bottom"
                          contentClassName="min-w-[180px]"
                          trigger={
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setActiveMenuId(activeMenuId === session.session_id ? null : session.session_id);
                              }}
                              className="p-1.5 rounded-lg hover:bg-white border border-transparent hover:border-slate-200 shadow-none hover:shadow-sm text-slate-400 hover:text-slate-600 transition-all cursor-pointer"
                            >
                              <MoreVertical className="w-3.5 h-3.5" />
                            </button>
                          }
                        >
                          <div className="p-1 min-w-[180px]">
                            {/* Share section */}
                            <div className="px-3 py-1.5 text-[10px] font-bold text-slate-400 uppercase tracking-widest border-b border-slate-50 mb-1">
                              Partager la conversation
                            </div>
                            <SocialShareButtons 
                              url={typeof window !== 'undefined' ? `${window.location.origin}${ROUTES.CHAT}?session_id=${session.session_id}` : ''} 
                              title={`Conversation: ${session.title || 'Sans titre'}`} 
                            />
                            
                            <div className="h-px bg-slate-100 my-1" />
                            
                            {/* Delete action */}
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                if (confirm('Supprimer cette conversation ?')) {
                                  deleteSession(session.session_id);
                                  setActiveMenuId(null);
                                }
                              }}
                              className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium text-red-500 hover:bg-red-50 transition-colors cursor-pointer"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                              Supprimer la session
                            </button>
                          </div>
                        </Popover>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Admin placeholder in admin mode */}
        {interfaceMode === 'admin' && (
          <div className="flex-1 flex items-center justify-center px-6">
            <div className="text-center">
              <Shield className="w-10 h-10 text-slate-200 mx-auto mb-2" />
              <p className="text-xs text-slate-400">Panel d&apos;administration</p>
            </div>
          </div>
        )}

        {/* Footer — Interface Switch */}
        <div className="p-3 border-t border-slate-100">
          <button
            onClick={() =>
              dispatch(switchInterface(interfaceMode === 'user' ? 'admin' : 'user'))
            }
            className={cn(
              'w-full flex items-center gap-3 px-3 py-2.5 rounded-xl',
              'text-sm font-medium transition-all duration-200 cursor-pointer',
              interfaceMode === 'admin'
                ? 'text-emerald-600 bg-emerald-50 hover:bg-emerald-100'
                : 'text-slate-500 hover:bg-slate-50 hover:text-slate-700'
            )}
          >
            {interfaceMode === 'admin' ? (
              <>
                <LayoutDashboard className="w-4 h-4" />
                Interface Utilisateur
              </>
            ) : (
              <>
                <Settings className="w-4 h-4" />
                Interface Admin
              </>
            )}
          </button>
        </div>
      </aside>
    </>
  );
}
