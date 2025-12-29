import type { EventDto } from "../api";

interface ImageModalProps {
  event: EventDto;
  onClose: () => void;
}

export default function ImageModal({ event, onClose }: ImageModalProps) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative max-w-5xl w-full max-h-[90vh] mx-4 bg-slate-950/95 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
          <div className="flex flex-col">
            <span className="text-sm text-slate-200">
              Событие #{event.id}
            </span>
            <span className="text-xs text-slate-500">
              {new Date(event.event_timestamp).toLocaleString()}
            </span>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-100 text-sm px-2 py-1 rounded-lg hover:bg-slate-800 transition-colors"
          >
            ✕ Закрыть
          </button>
        </div>

        <div className="flex-1 bg-black flex items-center justify-center">
          {/* eslint-disable-next-line jsx-a11y/img-redundant-alt */}
          <img
            src={event.frame_snapshot_url}
            alt={`Event ${event.id} full image`}
            className="max-h-[80vh] w-auto object-contain"
          />
        </div>

        <div className="px-4 py-2 border-t border-slate-800 text-xs text-slate-400 flex flex-wrap gap-x-4 gap-y-1">
          <span>Object ID: {event.object_id ?? "—"}</span>
          <span>Owner ID: {event.owner_id ?? "—"}</span>
          {event.bbox && (
            <span>
              BBox: {event.bbox.map((v) => v.toFixed(0)).join(" × ")}
            </span>
          )}
          <span>Статус: {event.status}</span>
        </div>
      </div>
    </div>
  );
}
