import { useEffect, useRef, useState } from "react";
import Hls from "hls.js";
import { fetchStreamHlsUrl } from "../api";

export default function HlsPlayer() {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let hls: Hls | null = null;
    let cancelled = false;

    async function setup() {
      try {
        setLoading(true);
        setError(null);

        const hlsUrl = await fetchStreamHlsUrl();

        const video = videoRef.current;
        if (!video) return;

        if (video.canPlayType("application/vnd.apple.mpegurl")) {
          // Safari / iOS
          video.src = hlsUrl;
        } else if (Hls.isSupported()) {
          // остальные браузеры
          hls = new Hls({
            enableWorker: true,
            lowLatencyMode: true,
          });
          hls.loadSource(hlsUrl);
          hls.attachMedia(video);
        } else {
          setError("HLS не поддерживается браузером");
          return;
        }

        if (!cancelled) {
          setLoading(false);
        }
      } catch (e) {
        console.error(e);
        if (!cancelled) {
          setError("Не удалось подключиться к видеопотоку");
          setLoading(false);
        }
      }
    }

    setup();

    return () => {
      cancelled = true;
      if (hls) {
        hls.destroy();
      }
    };
  }, []);

  return (
    <div className="w-full h-full flex flex-col rounded-2xl bg-black overflow-hidden shadow-lg">
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/10">
        <div className="flex flex-col">
          <span className="text-sm text-white/60">Live stream</span>
          <span className="text-base font-medium text-white">
            live_stream
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-red-500 animate-pulse" />
          <span className="text-xs uppercase tracking-wide text-red-400">
            Live
          </span>
        </div>
      </div>

      <div className="relative flex-1 bg-black">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center text-sm text-white/60">
            Подключаюсь к потоку...
          </div>
        )}
        {error && (
          <div className="absolute inset-0 flex items-center justify-center text-sm text-red-400 px-4 text-center">
            {error}
          </div>
        )}
        <video
          ref={videoRef}
          className="w-full h-full object-contain"
          autoPlay
          muted
          controls
        />
      </div>
    </div>
  );
}
