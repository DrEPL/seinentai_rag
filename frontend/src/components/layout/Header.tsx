/**
 * SEINENTAI4US — Header
 */
import { useState } from 'react';
import { Menu, Bell, LogOut, Calendar, Shield, BookOpen } from 'lucide-react';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { toggleSidebar } from '@/store/slices/uiSlice';
import { openTutorial, setStep } from '@/store/slices/tutorialSlice';
import { getInitials, formatDate } from '@/lib/utils';
import { useAuth } from '@/hooks/useAuth';
import Badge from '@/components/ui/Badge';
import Popover from '@/components/ui/Popover';

interface HeaderProps {
  title?: string;
}

export default function Header({ title }: HeaderProps) {
  const dispatch = useAppDispatch();
  const { user, logout } = useAuth();
  const interfaceMode = useAppSelector((s) => s.ui.interfaceMode);
  const [isProfileOpen, setIsProfileOpen] = useState(false);

  return (
    <header id="tour-app-header" className="h-[60px] bg-white/80 backdrop-blur-md border-b border-slate-100 flex items-center justify-between px-4 md:px-6 sticky top-0 z-30">
      <div className="flex items-center gap-3">
        <button
          id="tour-sidebar-toggle"
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

      <div className="flex items-center gap-2">
        <button className="p-2 rounded-xl hover:bg-slate-100 transition-colors relative cursor-pointer">
          <Bell className="w-[18px] h-[18px] text-slate-500" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-emerald-500 rounded-full" />
        </button>

        {user && (
          <Popover
            isOpen={isProfileOpen}
            onClose={() => setIsProfileOpen(false)}
            align="right"
            position="bottom"
            trigger={
              <div
                className="flex items-center gap-2.5 pl-2 ml-1 border-l border-slate-100 cursor-pointer hover:opacity-80 transition-opacity"
                onClick={() => setIsProfileOpen(!isProfileOpen)}
              >
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center shadow-sm">
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
            }
          >
            <div className="w-80">
              {/* Header */}
              <div className="p-5 border-b border-slate-50 bg-gradient-to-b from-slate-50/50 to-white">
                <div className="flex items-center gap-4">
                  <div className="relative">
                    <div className="w-14 h-14 rounded-full bg-gradient-to-br from-emerald-400 to-teal-600 flex items-center justify-center shadow-md shadow-emerald-100">
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

                {/* ─── Bouton Tutoriel ──────────────────────────────────── */}
                <button
                  onClick={() => {
                    setIsProfileOpen(false);
                    dispatch(setStep(0));
                    dispatch(openTutorial({ manual: true }));
                    window.dispatchEvent(new Event('seinentai:tutorial-open-manual'));
                  }}
                  className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-emerald-700 text-sm font-medium hover:bg-emerald-50 transition-colors cursor-pointer mb-1"
                >
                  <BookOpen className="w-4 h-4 text-emerald-500" />
                  Revoir le tutoriel
                </button>

                <div className="h-px bg-slate-100 mx-3 mb-1" />

                <button
                  onClick={() => {
                    setIsProfileOpen(false);
                    logout();
                  }}
                  className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-slate-600 text-sm font-medium hover:text-slate-900 hover:bg-slate-50 transition-colors cursor-pointer"
                >
                  <LogOut className="w-4 h-4" />
                  Se déconnecter
                </button>
              </div>
            </div>
          </Popover>
        )}
      </div>
    </header>
  );
}
