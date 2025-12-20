import './globals.css';
import type { Metadata } from 'next';
import { ClerkProvider } from '@clerk/nextjs';
import { Fraunces, Sora } from 'next/font/google';
import Providers from './providers';

export const dynamic = 'force-dynamic';

const sora = Sora({
  subsets: ['latin'],
  variable: '--font-body',
  display: 'swap'
});

const fraunces = Fraunces({
  subsets: ['latin'],
  variable: '--font-display',
  display: 'swap'
});

export const metadata: Metadata = {
  title: 'Student Success Platform',
  description: 'AI-powered early warning and intervention planning for K-12 success.'
};

export default function RootLayout({
  children
}: {
  children: React.ReactNode;
}) {
  return (
    <ClerkProvider>
      <html lang="en" className={`${sora.variable} ${fraunces.variable}`}>
        <body>
          <Providers>{children}</Providers>
        </body>
      </html>
    </ClerkProvider>
  );
}
