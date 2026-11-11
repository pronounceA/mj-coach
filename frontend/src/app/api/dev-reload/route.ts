import fs from 'fs';

const SIGNAL = '/tmp/reload_signal';

export async function GET() {
  if (process.env.NODE_ENV !== 'development') {
    return new Response('Not found', { status: 404 });
  }

  const enc = new TextEncoder();
  let active = true;
  let watcher: fs.FSWatcher | null = null;

  const stream = new ReadableStream({
    start(controller) {
      const send = (event: string, data: string) => {
        if (!active) return;
        try {
          controller.enqueue(enc.encode(`event: ${event}\ndata: ${data}\n\n`));
        } catch {
          active = false;
        }
      };

      send('connected', 'ok');

      try {
        watcher = fs.watch(SIGNAL, () => {
          send('reload', String(Date.now()));
          // 1回送ったら閉じる。ブラウザ側EventSourceが自動再接続する
          active = false;
          watcher?.close();
          watcher = null;
        });
      } catch {
        // /tmp/reload_signal がまだ存在しない場合は無視
      }
    },
    cancel() {
      active = false;
      watcher?.close();
      watcher = null;
    },
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
    },
  });
}
