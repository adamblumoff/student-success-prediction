import { realtimeEmitter, type RealtimeEvent } from '@/lib/realtime';

export const revalidate = 0;

export async function GET(request: Request) {
  const stream = new ReadableStream({
    start(controller) {
      const encoder = new TextEncoder();

      const send = (event: RealtimeEvent) => {
        controller.enqueue(encoder.encode(`data: ${JSON.stringify(event)}\n\n`));
      };

      send({ type: 'connected' });

      const listener = (event: RealtimeEvent) => {
        send(event);
      };

      realtimeEmitter.on('event', listener);

      const ping = setInterval(() => {
        controller.enqueue(encoder.encode(': ping\n\n'));
      }, 25_000);

      const cleanup = () => {
        clearInterval(ping);
        realtimeEmitter.off('event', listener);
        controller.close();
      };

      request.signal.addEventListener('abort', cleanup, { once: true });
    }
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache, no-transform',
      Connection: 'keep-alive',
      'X-Accel-Buffering': 'no',
      'X-Endpoint-Type': 'sse'
    }
  });
}
