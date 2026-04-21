/**
 * SEINENTAI4US — Header
 */
import { useState, useRef, useEffect } from 'react';
import { Menu, Bell, LogOut, User as UserIcon, Mail, Calendar, Shield } from 'lucide-react';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { toggleSidebar } from '@/store/slices/uiSlice';
import { getInitials, formatDate } from '@/lib/utils';
import { useAuth } from '@/hooks/useAuth';
import Badge from '@/components/ui/Badge';
import { AnimatePresence, motion } from 'framer-motion';

interface HeaderProps {
  title?: string;
}

export default function Header({ title }: HeaderProps) {
  const dispatch = useAppDispatch();
  const { user, logout } = useAuth();
  const interfaceMode = useAppSelector((s) => s.ui.interfaceMode);
  
  const [isPopoverOpen, setIsPopoverOpen] = useState(false);
  const popoverRef = useRef<HTMLDivElement>(null);

  // Close popover when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (popoverRef.current && !popoverRef.current.contains(event.target as Node)) {
        setIsPopoverOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <header className="h-[60px] bg-white/80 backdrop-blur-md border-b border-slate-100 flex items-center justify-between px-4 md:px-6 sticky top-0 z-30">
      <div className="flex items-center gap-3">
        <button
          onClick={() => dispatch(toggleSidebar())}
          className="p-2 rounded-xl hover:bg-slate-100 transition-colors cursor-pointer md:hidden"
        >
          <Menu className="w-5 h-5 text-slate-600" />
        </button>
        {title && (
          <h1 className="text-lg font-semibold text-slate-900 hidden sm:block">{title}</h1>
        )}
        {interfaceMode === 'admin' && (
          <span className="text-[10px] font-semibold text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full uppercase tracking-wider">
            Admin
          </span>
        )}
      </div>

      <div className="flex items-center gap-2 relative" ref={popoverRef}>
        <button className="p-2 rounded-xl hover:bg-slate-100 transition-colors relative cursor-pointer">
          <Bell className="w-[18px] h-[18px] text-slate-500" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-indigo-500 rounded-full" />
        </button>

        {user && (
          <div 
            className="flex items-center gap-2.5 pl-2 ml-1 border-l border-slate-100 cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setIsPopoverOpen(!isPopoverOpen)}
          >
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-400 to-violet-500 flex items-center justify-center shadow-sm">
              <span className="text-xs font-bold text-white">
                {getInitials(user.full_name)}
              </span>
            </div>
            <div className="hidden sm:block">
              <p className="text-sm font-medium text-slate-700 leading-tight">
                {user.full_name}
              </p>
              <p className="text-[10px] text-slate-400 leading-tight">{user.email}</p>
            </div>
          </div>
        )}

        {/* Profile Popover */}
        <AnimatePresence>
          {isPopoverOpen && user && (
            <motion.div
              initial={{ opacity: 0, y: 10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 10, scale: 0.95 }}
              transition={{ duration: 0.15, ease: "easeOut" }}
              className="absolute right-0 top-[48px] w-80 bg-white rounded-2xl shadow-xl shadow-slate-200/50 border border-slate-100 overflow-hidden z-50 origin-top-right"
            >
              {/* Header */}
              <div className="p-5 border-b border-slate-50 bg-gradient-to-b from-slate-50/50 to-white">
                <div className="flex items-center gap-4">
                  <div className="relative">
                    <div className="w-14 h-14 rounded-full bg-gradient-to-br from-indigo-400 to-violet-600 flex items-center justify-center shadow-md shadow-indigo-100">
                      <span className="text-xl font-bold text-white">
                        {getInitials(user.full_name)}
                      </span>
                    </div>
                    <div className="absolute -bottom-0.5 -right-0.5 w-4 h-4 rounded-full bg-emerald-400 border-2 border-white" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-slate-900 leading-tight">{user.full_name}</h3>
                    <p className="text-xs text-slate-500 mt-0.5">{user.email}</p>
                    <div className="flex gap-2 mt-2">
                      <Badge variant="success" dot className="!text-[9px] !py-0">Actif</Badge>
                      <Badge variant={interfaceMode === 'admin' ? 'warning' : 'info'} className="!text-[9px] !py-0">
                        {interfaceMode === 'admin' ? 'Admin' : 'Utilisateur'}
                      </Badge>
                    </div>
                  </div>
                </div>
              </div>

              {/* Body */}
              <div className="p-3">
                <div className="space-y-1 mb-3">
                  <div className="flex items-center gap-3 px-3 py-2 rounded-xl text-slate-600 text-sm">
                    <Calendar className="w-4 h-4 text-slate-400" />
                    <span>Inscrit le {formatDate(user.created_at)}</span>
                  </div>
                  <div className="flex items-center gap-3 px-3 py-2 rounded-xl text-slate-600 text-sm">
                    <Shield className="w-4 h-4 text-slate-400" />
                    <span className="truncate" title={user.id}>ID: {user.id}</span>
                  </div>
                </div>

                <div className="h-px bg-slate-100 mx-3 mb-3" />

                <button
                  onClick={() => {
                    setIsPopoverOpen(false);
                    logout();
                  }}
                  className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-red-600 text-sm font-medium hover:bg-red-50 transition-colors cursor-pointer"
                >
                  <LogOut className="w-4 h-4" />
                  Se déconnecter
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </header>
  );
}
