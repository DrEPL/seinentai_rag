/**
 * SEINENTAI4US — Auth Layout
 */
import { type ReactNode } from 'react';
import { motion } from 'framer-motion';
import Head from 'next/head';

interface AuthLayoutProps {
  children: ReactNode;
  title: string;
  subtitle?: string;
}

export default function AuthLayout({ children, title, subtitle }: AuthLayoutProps) {
  return (
    <>
      <Head>
        <title>{title} — SEINENTAI4US</title>
        <meta name="description" content="SEINENTAI4US - Plateforme RAG intelligente" />
      </Head>
      <div className="min-h-screen gradient-bg-animated flex items-center justify-center p-4">
        {/* Decorative elements */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-emerald-200/30 rounded-full blur-3xl animate-float" />
          <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-teal-200/20 rounded-full blur-3xl animate-float" style={{ animationDelay: '1.5s' }} />
          <div className="absolute top-1/3 left-1/4 w-64 h-64 bg-green-200/20 rounded-full blur-3xl animate-float" style={{ animationDelay: '3s' }} />
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20, scale: 0.98 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.5, ease: [0.4, 0, 0.2, 1] }}
          className="relative w-full max-w-md"
        >
          {/* Logo / Branding */}
          <div className="text-center mb-8">
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: 0.1, duration: 0.4 }}
              className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 shadow-lg shadow-emerald-200 mb-4"
            >
              <span className="text-2xl font-bold text-white font-[var(--font-heading)]">S</span>
            </motion.div>
            <h1 className="text-2xl font-bold gradient-text">{title}</h1>
            {subtitle && (
              <p className="mt-2 text-sm text-slate-500">{subtitle}</p>
            )}
          </div>

          {/* Card */}
          <div className="glass-strong rounded-2xl shadow-xl p-8">
            {children}
          </div>

          {/* Footer */}
          <p className="text-center text-xs text-slate-400 mt-6">
            SEINENTAI4US © {new Date().getFullYear()} — Plateforme RAG intelligente
          </p>
        </motion.div>
      </div>
    </>
  );
}
