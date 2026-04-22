/**
 * SEINENTAI4US — Admin Monitoring page
 */
import { useEffect, useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Activity, Server, Database, Cpu, RefreshCw, CheckCircle, XCircle } from 'lucide-react';
import AppLayout from '@/components/layout/AppLayout';
import Button from '@/components/ui/Button';
import Badge from '@/components/ui/Badge';
import { adminApi } from '@/api/admin';
import { cn, formatTime } from '@/lib/utils';

interface HealthData {
  status: string;
  uptime?: number;
  version?: string;
  components?: Record<string, { status: string; details?: string }>;
}

export default function MonitoringPage() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  const checkHealth = useCallback(async () => {
    setLoading(true);
    try {
      const res = await adminApi.getHealth();
      setHealth(res.data);
      setLastChecked(new Date());
    } catch {
      setHealth({ status: 'error' });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { checkHealth(); }, [checkHealth]);

  const isHealthy = health?.status === 'ok' || health?.status === 'healthy';

  const services = [
    { name: 'API FastAPI', icon: Server, status: isHealthy ? 'healthy' : 'error' },
    { name: 'Base de données', icon: Database, status: health?.components?.database?.status || (isHealthy ? 'healthy' : 'unknown') },
    { name: 'Qdrant Vector DB', icon: Cpu, status: health?.components?.qdrant?.status || (isHealthy ? 'healthy' : 'unknown') },
    { name: 'LLM Service', icon: Activity, status: health?.components?.llm?.status || (isHealthy ? 'healthy' : 'unknown') },
  ];

  return (
    <AppLayout title="Monitoring" pageTitle="Monitoring">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Global status */}
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="card p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className={cn('w-14 h-14 rounded-2xl flex items-center justify-center', isHealthy ? 'bg-emerald-50' : 'bg-red-50')}>
                {isHealthy ? <CheckCircle className="w-7 h-7 text-emerald-500" /> : <XCircle className="w-7 h-7 text-red-500" />}
              </div>
              <div>
                <h2 className="text-lg font-bold text-slate-900">État du système</h2>
                <p className="text-sm text-slate-500">
                  {isHealthy ? 'Tous les services sont opérationnels' : 'Problème détecté'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {lastChecked && <span className="text-[11px] text-slate-400">Vérifié à {formatTime(lastChecked)}</span>}
              <Button variant="outline" size="sm" loading={loading} icon={<RefreshCw className="w-3.5 h-3.5" />} onClick={checkHealth}>
                Rafraîchir
              </Button>
            </div>
          </div>
        </motion.div>

        {/* Services grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {services.map((svc, i) => {
            const ok = svc.status === 'healthy' || svc.status === 'ok';
            return (
              <motion.div key={svc.name} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }} className="card p-5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={cn('w-10 h-10 rounded-xl flex items-center justify-center', ok ? 'bg-emerald-50' : 'bg-red-50')}>
                      <svc.icon className={cn('w-5 h-5', ok ? 'text-emerald-500' : 'text-red-500')} />
                    </div>
                    <span className="text-sm font-semibold text-slate-900">{svc.name}</span>
                  </div>
                  <Badge variant={ok ? 'success' : 'danger'} dot>{ok ? 'En ligne' : 'Hors ligne'}</Badge>
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* System info */}
        {health?.version && (
          <div className="card p-5">
            <h3 className="text-sm font-semibold text-slate-900 mb-3">Informations système</h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div><p className="text-[11px] text-slate-400 uppercase">Version</p><p className="font-medium text-slate-700">{health.version}</p></div>
              {health.uptime && <div><p className="text-[11px] text-slate-400 uppercase">Uptime</p><p className="font-medium text-slate-700">{Math.floor(health.uptime / 3600)}h {Math.floor((health.uptime % 3600) / 60)}m</p></div>}
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
