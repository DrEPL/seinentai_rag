/**
 * SEINENTAI4US — Index page (redirect)
 */
import { useEffect } from 'react';
import { useRouter } from 'next/router';
import { AUTH_TOKEN_KEY, ROUTES } from '@/lib/constants';

export default function IndexPage() {
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem(AUTH_TOKEN_KEY);
    router.replace(token ? ROUTES.CHAT : ROUTES.LOGIN);
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center gradient-bg-animated">
      <div className="typing-dots">
        <span /><span /><span />
      </div>
    </div>
  );
}
