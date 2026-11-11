'use client';

import { useEffect } from 'react';

export default function DevReloader() {
  useEffect(() => {
    if (process.env.NODE_ENV !== 'development') return;

    const es = new EventSource('/api/dev-reload');

    es.addEventListener('reload', () => {
      window.location.reload();
    });

    return () => {
      es.close();
    };
  }, []);

  return null;
}
