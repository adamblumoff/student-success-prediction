'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useEffect, useRef, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';

export default function Providers({
  children
}: {
  children: React.ReactNode;
}) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            refetchOnWindowFocus: false,
            retry: 1
          }
        }
      })
  );
  const router = useRouter();
  const pathname = usePathname();
  const sourceRef = useRef<EventSource | null>(null);
  const pathnameRef = useRef(pathname);

  useEffect(() => {
    pathnameRef.current = pathname;
  }, [pathname]);

  useEffect(() => {
    if (sourceRef.current) return;
    const source = new EventSource('/api/events');
    sourceRef.current = source;

    source.onmessage = (event) => {
      if (!event.data) return;
      try {
        const payload = JSON.parse(event.data) as {
          type: string;
          paths?: string[];
          districtId?: number | null;
          institutionId?: number | null;
        };
        window.dispatchEvent(new CustomEvent('data:mutation', { detail: payload }));
        if (!payload.paths || payload.paths.length === 0) {
          router.refresh();
          return;
        }
        if (payload.paths.includes(pathnameRef.current)) {
          router.refresh();
        }
      } catch {
        // Ignore malformed events.
      }
    };

    return () => {
      source.close();
      sourceRef.current = null;
    };
  }, [router, pathname]);

  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
