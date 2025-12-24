'use client';

import { useEffect } from 'react';

export default function PWAClient() {
  useEffect(() => {
    if (typeof window === 'undefined') return;
    if (!('serviceWorker' in navigator)) return;

    const register = async () => {
      try {
        await navigator.serviceWorker.register('/service-worker.js');
      } catch (err) {
        console.error('Service worker registration failed', err);
      }
    };

    // Delay registration slightly so it doesn't compete with critical rendering
    const id = window.setTimeout(register, 2000);
    return () => window.clearTimeout(id);
  }, []);

  return null;
}


