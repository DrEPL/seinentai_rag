/**
 * SEINENTAI4US — App Layout (Sidebar + Header + Content)
 */
import { useEffect, type ReactNode } from 'react';
import Head from 'next/head';
import Sidebar from './Sidebar';
import Header from './Header';
import { useAppSelector, useAppDispatch } from '@/store/hooks';
import { setSidebarOpen } from '@/store/slices/uiSlice';
import { cn } from '@/lib/utils';

interface AppLayoutProps {
  children: ReactNode;
  title?: string;
  pageTitle?: string;
  fullHeight?: boolean;
}

export default function AppLayout({ children, title, pageTitle, fullHeight = false }: AppLayoutProps) {
  const dispatch = useAppDispatch();
  const sidebarOpen = useAppSelector((s) => s.ui.sidebarOpen);

  return (
    <>
      <Head>
        <title>{pageTitle ? `${pageTitle} — SEINENTAI4US` : 'SEINENTAI4US'}</title>
        <meta name="description" content="SEINENTAI4US - Plateforme RAG intelligente" />
      </Head>
      <div className="flex h-[100dvh] overflow-hidden bg-[var(--background)]">
        <Sidebar />
        <div
          className={cn(
            'flex-1 flex flex-col min-w-0 transition-all duration-300',
            !sidebarOpen && 'md:ml-0'
          )}
        >
          <Header title={title} />
          <main
            className={cn(
              'flex-1',
              fullHeight ? 'flex flex-col overflow-hidden relative' : 'p-4 md:p-6 overflow-y-auto'
            )}
          >
            {children}
          </main>
        </div>
      </div>
    </>
  );
}
