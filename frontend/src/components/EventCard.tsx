import type { EventDto, EventStatus } from "../api";

interface EventCardProps {
  event: EventDto;
  onConfirm: (id: number) => void;
  onDismiss: (id: number) => void;
  onOpenImage?: (event: EventDto) => void;
}

function statusLabel(status: EventStatus): string {
  switch (status) {
    case "new":
      return "Новое";
    case "confirmed":
      return "Подтверждено";
    case "dismissed":
      return "Ложное";
    default:
      return status;
  }
}

function statusClass(status: EventStatus): string {
  switch (status) {
    case "new":
      return "bg-yellow-500/15 text-yellow-300 border-yellow-500/40";
    case "confirmed":
      return "bg-emerald-500/15 text-emerald-300 border-emerald-500/40";
    case "dismissed":
      return "bg-red-500/15 text-red-300 border-red-500/40";
    default:
      return "bg-slate-500/15 text-slate-200 border-slate-500/40";
  }
}

export default function EventCard({
  event,
  onConfirm,
  onDismiss,
  onOpenImage,
}: EventCardProps) {
  const ts = new Date(event.event_timestamp);
  const timeStr = ts.toLocaleString();

  const handleImageClick = () => {
    if (onOpenImage) {
      onOpenImage(event);
    }
  };

  return (
    <div className="flex gap-3 py-3 px-3 hover:bg-slate-900/60 rounded-xl transition-colors border border-slate-800/70">
      {/* превью кликабельно */}
      <button
        type="button"
        className="w-28 h-20 rounded-lg overflow-hidden bg-slate-900 shrink-0 border border-slate-800 hover:border-slate-500 transition-colors"
        onClick={handleImageClick}
      >
        {/* eslint-disable-next-line jsx-a11y/img-redundant-alt */}
        <img
          src={event.frame_snapshot_url}
          alt={`Event ${event.id} snapshot`}
          className="w-full h-full object-cover"
        />
      </button>

      <div className="flex-1 flex flex-col gap-1 min-w-0">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <span className="text-xs text-slate-400 shrink-0">
              ID #{event.id}
            </span>
            <span className="text-xs text-slate-500 truncate">
              {timeStr}
            </span>
          </div>
          <span
            className={`text-[10px] px-2 py-0.5 rounded-full border ${statusClass(
              event.status
            )}`}
          >
            {statusLabel(event.status)}
          </span>
        </div>

        <div className="flex flex-wrap gap-x-3 gap-y-1 text-[11px] text-slate-400">
          <span>Object ID: {event.object_id ?? "—"}</span>
          <span>Owner ID: {event.owner_id ?? "—"}</span>
          {event.bbox && (
            <span>
              BBox: {event.bbox.map((v) => v.toFixed(0)).join(" × ")}
            </span>
          )}
        </div>

        <div className="flex gap-2 mt-1">
          <button
            onClick={() => onConfirm(event.id)}
            className="text-xs px-2 py-1 rounded-lg bg-emerald-500/15 text-emerald-200 hover:bg-emerald-500/25 border border-emerald-500/40 transition-colors"
          >
            Подтвердить
          </button>
          <button
            onClick={() => onDismiss(event.id)}
            className="text-xs px-2 py-1 rounded-lg bg-red-500/15 text-red-200 hover:bg-red-500/25 border border-red-500/40 transition-colors"
          >
            Ложное
          </button>
        </div>
      </div>
    </div>
  );
}