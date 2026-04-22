/**
 * SEINENTAI4US — Register page
 */
import { useState, type FormEvent } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Mail, Lock, User, ArrowRight, Eye, EyeOff } from 'lucide-react';
import AuthLayout from '@/components/layout/AuthLayout';
import Input from '@/components/ui/Input';
import Button from '@/components/ui/Button';
import { useAuth } from '@/hooks/useAuth';

export default function RegisterPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const { register, loading, error } = useAuth();

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (email && password && fullName) {
      register(email, password, fullName);
    }
  };

  return (
    <AuthLayout title="Créer un compte" subtitle="Rejoignez la plateforme SEINENTAI4US">
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
          label="Nom complet"
          type="text"
          placeholder="Votre nom complet"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          icon={<User className="w-4 h-4" />}
          required
          autoFocus
          minLength={2}
          maxLength={100}
        />

        <Input
          label="Email"
          type="email"
          placeholder="votre@email.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          icon={<Mail className="w-4 h-4" />}
          required
        />

        <Input
          label="Mot de passe"
          type={showPassword ? 'text' : 'password'}
          placeholder="Minimum 8 caractères"
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
          icon={<ArrowRight className="w-4 h-4" />}
        >
          {loading ? "Création en cours..." : "Créer mon compte"}
        </Button>

        <div className="text-center">
          <span className="text-sm text-slate-500">Déjà inscrit ? </span>
          <Link
            href="/login"
            className="text-sm font-semibold text-emerald-600 hover:text-emerald-700 transition-colors"
          >
            Se connecter
          </Link>
        </div>
      </form>
    </AuthLayout>
  );
}
