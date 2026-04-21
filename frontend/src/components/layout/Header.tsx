/**
 * SEINENTAI4US — Header
 */
import { Menu, Bell } from 'lucide-react';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { toggleSidebar } from '@/store/slices/uiSlice';
import { getInitials } from '@/lib/utils';

interface HeaderProps {
  title?: string;
}

export default function Header({ title }: HeaderProps) {
  const dispatch = useAppDispatch();
  const user = useAppSelector((s) => s.auth.user);
  const interfaceMode = useAppSelector((s) => s.ui.interfaceMode);

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

      <div className="flex items-center gap-2">
        <button className="p-2 rounded-xl hover:bg-slate-100 transition-colors relative cursor-pointer">
          <Bell className="w-[18px] h-[18px] text-slate-500" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-indigo-500 rounded-full" />
        </button>

        {user && (
          <div className="flex items-center gap-2.5 pl-2 ml-1 border-l border-slate-100">
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
      </div>
    </header>
  );
}
