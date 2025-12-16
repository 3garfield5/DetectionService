import EventsPanel from "./components/EventsPanel";
import HlsPlayer from "./components/HlsPlayer";

function App() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-slate-100">
      <div className="max-w-6xl mx-auto px-4 py-4 flex flex-col gap-4">
        <header className="flex items-center justify-between gap-4">
          <div className="flex flex-col gap-1">
            <h1 className="text-lg font-semibold tracking-tight">
              Поиск оставленных объектов
            </h1>
            <p className="text-xs text-slate-400">
              Live-мониторинг видеопотока и событий от ML-сервиса
            </p>
          </div>
          <div className="text-xs text-slate-500">
            Backend: <span className="font-mono">localhost:8000</span>
          </div>
        </header>

        <main className="grid grid-cols-1 lg:grid-cols-[minmax(0,2fr)_minmax(0,1.1fr)] gap-4 h-[calc(100vh-5.5rem)]">
          <div className="h-full">
            <HlsPlayer />
          </div>
          <div className="h-full">
            <EventsPanel />
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
