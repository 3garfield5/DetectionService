import { useEffect, useState, useCallback } from "react";
import type { EventDto, EventStatus } from "../api";
import {
  fetchEvents,
  updateEventStatus,
} from "../api";
import EventCard from "./EventCard";
import ImageModal from "./ImageModal";

const STATUS_TABS: { label: string; value?: EventStatus }[] = [
  { label: "Все", value: undefined },
  { label: "Новые", value: "new" },
  { label: "Подтвержденные", value: "confirmed" },
  { label: "Ложные", value: "dismissed" },
];

export default function EventsPanel() {
  const [events, setEvents] = useState<EventDto[]>([]);
  const [statusFilter, setStatusFilter] = useState<EventStatus | undefined>(
    "new"
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [selectedEvent, setSelectedEvent] = useState<EventDto | null>(
    null
  );

  const loadEvents = useCallback(
    async (currentStatus?: EventStatus) => {
      try {
        setLoading(true);
        setError(null);
        const data = await fetchEvents(currentStatus);
        setEvents(data);
      } catch (e) {
        console.error(e);
        setError("Не удалось загрузить события");
      } finally {
        setLoading(false);
      }
    },
    []
  );

  useEffect(() => {
    loadEvents(statusFilter);
    const timer = setInterval(() => {
      loadEvents(statusFilter);
    }, 5000);

    return () => clearInterval(timer);
  }, [statusFilter, loadEvents]);

  const handleConfirm = async (id: number) => {
    try {
      await updateEventStatus(id, "confirmed");
      await loadEvents(statusFilter);
    } catch (e) {
      console.error(e);
    }
  };

  const handleDismiss = async (id: number) => {
    try {
      await updateEventStatus(id, "dismissed");
      await loadEvents(statusFilter);
    } catch (e) {
      console.error(e);
    }
  };

  const handleOpenImage = (event: EventDto) => {
    setSelectedEvent(event);
  };

  const handleCloseImage = () => {
    setSelectedEvent(null);
  };

  return (
    <div className="relative flex flex-col h-full bg-slate-950/90 backdrop-blur-xl border border-slate-800/70 rounded-2xl shadow-lg">
      <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between gap-2">
        <div className="flex flex-col">
          <span className="text-sm text-slate-200 font-medium">
            События оставленных объектов
          </span>
          <span className="text-xs text-slate-500">
            Всего: {events.length}
          </span>
        </div>
        <div className="flex flex-wrap gap-1 justify-end">
          {STATUS_TABS.map((tab) => {
            const active = tab.value === statusFilter;
            return (
              <button
                key={tab.label}
                onClick={() => setStatusFilter(tab.value)}
                className={
                  "text-[11px] px-2 py-1 rounded-full border transition-colors " +
                  (active
                    ? "bg-slate-100 text-slate-900 border-slate-100"
                    : "bg-transparent text-slate-400 border-slate-700 hover:border-slate-500 hover:text-slate-200")
                }
              >
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      {error && (
        <div className="px-4 py-2 text-xs text-red-400 border-b border-slate-800">
          {error}
        </div>
      )}

      <div className="flex-1 overflow-auto px-3 py-3 space-y-2">
        {loading && events.length === 0 && (
          <div className="text-xs text-slate-500">
            Загружаем события...
          </div>
        )}

        {!loading && events.length === 0 && !error && (
          <div className="text-xs text-slate-500">
            Событий пока нет.
          </div>
        )}

        {events.map((ev) => (
          <EventCard
            key={ev.id}
            event={ev}
            onConfirm={handleConfirm}
            onDismiss={handleDismiss}
            onOpenImage={handleOpenImage}
          />
        ))}
      </div>

      {selectedEvent && (
        <ImageModal event={selectedEvent} onClose={handleCloseImage} />
      )}
    </div>
  );
}
