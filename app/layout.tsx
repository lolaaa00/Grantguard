import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = { title: 'GrantGuard', description: 'Consensus-powered grant evaluation on GenLayer' };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
