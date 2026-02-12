import { useEffect, useRef, useState } from 'react';

interface EventStreamOptions {
  url: string;
  enabled?: boolean;
  onMessage?: (event: MessageEvent) => void;
  onOpen?: () => void;
  onError?: (event: Event) => void;
  retryBaseMs?: number;
  retryMaxMs?: number;
}

export function useEventStream({
  url,
  enabled = true,
  onMessage,
  onOpen,
  onError,
  retryBaseMs = 1000,
  retryMaxMs = 30000,
}: EventStreamOptions) {
  const eventSourceRef = useRef<EventSource | null>(null);
  const retryTimeoutRef = useRef<number | null>(null);
  const [connected, setConnected] = useState(false);
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    if (!enabled) return;

    const connect = () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }

      const es = new EventSource(url);
      eventSourceRef.current = es;

      es.onopen = () => {
        setConnected(true);
        setRetryCount(0);
        onOpen?.();
      };

      es.onmessage = (event) => {
        onMessage?.(event);
      };

      es.onerror = (event) => {
        setConnected(false);
        onError?.(event);
        es.close();

        const nextRetry = Math.min(retryBaseMs * 2 ** retryCount, retryMaxMs);
        retryTimeoutRef.current = window.setTimeout(() => {
          setRetryCount((c) => c + 1);
          connect();
        }, nextRetry);
      };
    };

    connect();

    return () => {
      if (retryTimeoutRef.current) window.clearTimeout(retryTimeoutRef.current);
      if (eventSourceRef.current) eventSourceRef.current.close();
    };
  }, [enabled, url, onMessage, onOpen, onError, retryBaseMs, retryMaxMs, retryCount]);

  return { connected, retryCount };
}
