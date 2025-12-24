'use client';

import { WifiOff, Home } from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function OfflinePage() {
  const router = useRouter();

  return (
    <main className="min-h-screen bg-gradient-soft flex items-center justify-center px-4">
      <div className="bg-white rounded-3xl shadow-soft-lg p-8 max-w-md w-full text-center">
        <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-2xl flex items-center justify-center">
          <WifiOff className="w-8 h-8 text-gray-500" />
        </div>
        <h1 className="text-xl font-bold text-gray-800 mb-2">You&apos;re offline</h1>
        <p className="text-gray-600 mb-6">
          Smart Approval AI needs a connection to run document analysis and dashboards.
          You can still reopen the app later when you&apos;re back online.
        </p>
        <button
          onClick={() => router.push('/')}
          className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-primary text-white font-medium hover:bg-primary-light transition"
        >
          <Home className="w-4 h-4" />
          Back to Home
        </button>
      </div>
    </main>
  );
}


