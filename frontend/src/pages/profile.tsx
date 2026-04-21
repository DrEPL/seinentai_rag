/**
 * SEINENTAI4US — Profile page
 */
import { motion } from 'framer-motion';
import { User, Mail, Calendar, Shield, LogOut, Key } from 'lucide-react';
import AppLayout from '@/components/layout/AppLayout';
import Button from '@/components/ui/Button';
import Badge from '@/components/ui/Badge';
import { useAuth } from '@/hooks/useAuth';
import { useAppSelector } from '@/store/hooks';
import { getInitials, formatDate } from '@/lib/utils';

export default function ProfilePage() {
  const { user, logout } = useAuth();
  const interfaceMode = useAppSelector((s) => s.ui.interfaceMode);

  if (!user) return null;

  return (
    <AppLayout title="Profil" pageTitle="Profil">
      <div className="max-w-2xl mx-auto space-y-6">
        {/* Profile card */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="card p-8"
        >
          <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6">
            {/* Avatar */}
            <div className="relative">
              <div className="w-24 h-24 rounded-2xl bg-gradient-to-br from-indigo-400 to-violet-600 flex items-center justify-center shadow-lg shadow-indigo-200">
                <span className="text-3xl font-bold text-white">
                  {getInitials(user.full_name)}
                </span>
              </div>
              <div className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-emerald-400 border-2 border-white" />
            </div>

            {/* Info */}
            <div className="flex-1 text-center sm:text-left">
              <h2 className="text-xl font-bold text-slate-900">{user.full_name}</h2>
              <p className="text-sm text-slate-500 mt-1">{user.email}</p>
              <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2 mt-3">
                <Badge variant="success" dot>Actif</Badge>
                <Badge variant={interfaceMode === 'admin' ? 'warning' : 'info'}>
                  {interfaceMode === 'admin' ? 'Admin' : 'Utilisateur'}
                </Badge>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Details */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="card"
        >
          <div className="px-6 py-4 border-b border-slate-100">
            <h3 className="text-sm font-semibold text-slate-900">Informations du compte</h3>
          </div>
          <div className="divide-y divide-slate-50">
            {[
              { icon: User, label: 'Nom complet', value: user.full_name },
              { icon: Mail, label: 'Email', value: user.email },
              { icon: Calendar, label: 'Inscrit le', value: formatDate(user.created_at) },
              { icon: Shield, label: 'ID', value: user.id },
            ].map((item, i) => (
              <div key={i} className="flex items-center gap-4 px-6 py-4">
                <div className="w-9 h-9 rounded-lg bg-slate-50 flex items-center justify-center">
                  <item.icon className="w-4 h-4 text-slate-400" />
                </div>
                <div>
                  <p className="text-[11px] text-slate-400 uppercase tracking-wider">{item.label}</p>
                  <p className="text-sm font-medium text-slate-700 mt-0.5">{item.value}</p>
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Actions */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="flex flex-col sm:flex-row gap-3"
        >
          <Button variant="danger" icon={<LogOut className="w-4 h-4" />} onClick={logout}>
            Se déconnecter
          </Button>
        </motion.div>
      </div>
    </AppLayout>
  );
}
