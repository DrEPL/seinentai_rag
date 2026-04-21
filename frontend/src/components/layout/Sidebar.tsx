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
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { truncate, formatRelativeTime } from '@/lib/utils';
import { ROUTES } from '@/lib/constants';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { switchInterface, toggleSidebar, setSidebarOpen } from '@/store/slices/uiSlice';
import { useChat } from '@/hooks/useChat';
import { SessionSkeleton } from '@/components/ui/Skeleton';

interface NavItem {
  icon: typeof MessageSquare;
  label: string;
  href: string;
  adminOnly?: boolean;
  userOnly?: boolean;
}

const userNav: NavItem[] = [
  { icon: MessageSquare, label: 'Chat RAG', href: ROUTES.CHAT },
  { icon: Search, label: 'Recherche', href: ROUTES.SEARCH },
  { icon: User, label: 'Profil', href: ROUTES.PROFILE },
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
  const { sessions, activeSessionId, sessionsLoading, loadSessions, loadSession, newConversation } = useChat();

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
      <motion.aside
        initial={false}
        animate={{ x: sidebarOpen ? 0 : -280 }}
        transition={{ type: 'spring', stiffness: 400, damping: 35 }}
        className={cn(
          'fixed md:relative z-40 h-screen flex flex-col',
          'w-[280px] bg-white border-r border-slate-200/80',
          'shadow-sm md:shadow-none'
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 h-[60px] border-b border-slate-100">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center">
              <span className="text-sm font-bold text-white">S</span>
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-900 leading-none">SEINENTAI4US</h2>
              <span className="text-[10px] text-slate-400 uppercase tracking-wider">
                {interfaceMode === 'admin' ? 'Admin' : 'RAG Agent'}
              </span>
            </div>
          </div>
          <button
            onClick={() => dispatch(toggleSidebar())}
            className="p-1.5 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer md:hidden"
          >
            <ChevronLeft className="w-4 h-4 text-slate-400" />
          </button>
        </div>

        {/* New Chat Button (user mode only) */}
        {interfaceMode === 'user' && (
          <div className="px-3 pt-3">
            <button
              onClick={() => {
                newConversation();
                router.push(ROUTES.CHAT);
              }}
              className={cn(
                'w-full flex items-center gap-2 px-3 py-2.5 rounded-xl',
                'text-sm font-medium text-indigo-600',
                'border border-indigo-200 bg-indigo-50/50',
                'hover:bg-indigo-100/70 hover:border-indigo-300',
                'transition-all duration-200 cursor-pointer',
                'active:scale-[0.98]'
              )}
            >
              <Plus className="w-4 h-4" />
              Nouvelle conversation
            </button>
          </div>
        )}

        {/* Navigation */}
        <nav className="px-3 pt-4">
          <p className="px-3 mb-2 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
            Navigation
          </p>
          <div className="space-y-0.5">
            {navItems.map((item) => {
              const isActive = router.pathname === item.href;
              return (
                <button
                  key={item.href}
                  onClick={() => router.push(item.href)}
                  className={cn(
                    'w-full flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-medium transition-all duration-200 cursor-pointer',
                    isActive
                      ? 'bg-indigo-50 text-indigo-700 shadow-sm'
                      : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                  )}
                >
                  <item.icon className={cn('w-[18px] h-[18px]', isActive && 'text-indigo-500')} />
                  {item.label}
                </button>
              );
            })}
          </div>
        </nav>

        {/* Chat History (user mode) */}
        {interfaceMode === 'user' && (
          <div className="flex-1 overflow-y-auto mt-4 no-scrollbar">
            <p className="px-6 mb-2 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
              Historique
            </p>
            {sessionsLoading ? (
              <SessionSkeleton />
            ) : sessions.length === 0 ? (
              <p className="px-6 text-xs text-slate-400 italic">Aucune conversation</p>
            ) : (
              <div className="px-3 space-y-0.5">
                {sessions.map((session) => (
                  <button
                    key={session.session_id}
                    onClick={() => {
                      loadSession(session.session_id);
                      router.push(ROUTES.CHAT);
                    }}
                    className={cn(
                      'w-full flex items-start gap-2.5 px-3 py-2 rounded-xl text-left transition-all duration-200 cursor-pointer group',
                      activeSessionId === session.session_id
                        ? 'bg-indigo-50/80 text-indigo-700'
                        : 'text-slate-600 hover:bg-slate-50'
                    )}
                  >
                    <MessageSquare className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 opacity-50" />
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium truncate">
                        {truncate(session.title || 'Sans titre', 35)}
                      </p>
                      <p className="text-[10px] text-slate-400 mt-0.5">
                        {formatRelativeTime(session.updated_at || session.created_at)}
                      </p>
                    </div>
                  </button>
                ))}
              </div>
            )}
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
                ? 'text-indigo-600 bg-indigo-50 hover:bg-indigo-100'
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
      </motion.aside>
    </>
  );
}
