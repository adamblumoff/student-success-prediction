import { EventEmitter } from 'events';

export type RealtimeEvent = {
  type: 'data:mutation' | 'ping' | 'connected';
  paths?: string[];
  districtId?: number | null;
  institutionId?: number | null;
};

const globalForRealtime = globalThis as typeof globalThis & {
  __realtimeEmitter?: EventEmitter;
};

export const realtimeEmitter =
  globalForRealtime.__realtimeEmitter ?? new EventEmitter();

if (process.env.NODE_ENV !== 'production') {
  globalForRealtime.__realtimeEmitter = realtimeEmitter;
}

export function emitRealtimeEvent(event: RealtimeEvent) {
  realtimeEmitter.emit('event', event);
}
