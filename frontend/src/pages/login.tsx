/**
 * SEINENTAI4US — Login page
 */
import { useState, type FormEvent } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Mail, Lock, ArrowRight, Eye, EyeOff, RefreshCw } from 'lucide-react';
import AuthLayout from '@/components/layout/AuthLayout';
import Input from '@/components/ui/Input';
import Button from '@/components/ui/Button';
import { useAuth } from '@/hooks/useAuth';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const { login, loading, error } = useAuth();

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (email && password) {
      login(email, password);
    }
  };

  return (
    <AuthLayout title="Connexion" subtitle="Accédez à votre espace SEINENTAI4US">
      <form onSubmit={handleSubmit} className="space-y-5">
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm"
          >
            {error}
          </motion.div>
        )}

        <Input
          label="Email"
          type="email"
          placeholder="votre@email.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          icon={<Mail className="w-4 h-4" />}
          required
          autoFocus
        />

        <Input
          label="Mot de passe"
          type={showPassword ? 'text' : 'password'}
          placeholder="••••••••"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          icon={<Lock className="w-4 h-4" />}
          rightIcon={
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="cursor-pointer hover:text-slate-600 transition-colors"
              tabIndex={-1}
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          }
          required
          minLength={8}
        />

        <Button
          type="submit"
          loading={loading}
          size="lg"
          className="w-full"
          icon={loading ? <RefreshCw className="w-4 h-4" /> : <ArrowRight className="w-4 h-4" />}
        >
          Se connecter {loading ? 'Connexion en cours...' : loading}
        </Button>

        <div className="text-center">
          <span className="text-sm text-slate-500">Pas encore de compte ? </span>
          <Link
            href="/register"
            className="text-sm font-semibold text-emerald-600 hover:text-emerald-700 transition-colors"
          >
            Créer un compte
          </Link>
        </div>
      </form>
    </AuthLayout>
  );
}
