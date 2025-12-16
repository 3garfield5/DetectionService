export type EventStatus = "new" | "confirmed" | "dismissed";

export interface EventDto {
  id: number;
  object_id: number | null;
  owner_id: number | null;
  bbox: number[] | null;
  frame_snapshot_url: string;
  status: EventStatus;
  event_timestamp: string;
  created_at: string;
  updated_at: string;
}

const API_BASE =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function fetchEvents(status?: EventStatus): Promise<EventDto[]> {
  const params = new URLSearchParams();
  if (status) params.set("status", status);
  params.set("limit", "100");
  params.set("offset", "0");

  const resp = await fetch(`${API_BASE}/events?` + params.toString());
  if (!resp.ok) {
    throw new Error(`Failed to fetch events: ${resp.status}`);
  }
  return resp.json();
}

export async function fetchStreamHlsUrl(): Promise<string> {
  const resp = await fetch(`${API_BASE}/streams/hls`);
  if (!resp.ok) {
    throw new Error(`Failed to fetch hls url: ${resp.status}`);
  }
  const data = await resp.json();
  return data.hls_url as string;
}


export async function updateEventStatus(
  id: number,
  status: EventStatus
): Promise<EventDto> {
  const resp = await fetch(`${API_BASE}/events/${id}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ status }),
  });

  if (!resp.ok) {
    throw new Error(`Failed to update event: ${resp.status}`);
  }
  return resp.json();
}

