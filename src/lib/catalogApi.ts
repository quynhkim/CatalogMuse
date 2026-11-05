import api from "@/lib/axios";
import type { Job } from "@/containers/CatalogMuse/types";

const MAX_IMAGE_BYTES = 8 * 1024 * 1024;

export function apiBase() {
  return import.meta.env.VITE_API_BASE_URL.replace(/\/$/, "");
}

export function fileUrl(jobId: string, file?: string, url?: string) {
  if (url) return url;
  if (!file) return "";
  return `${apiBase()}/v1/jobs/${encodeURIComponent(jobId)}/files/${encodeURIComponent(file)}`;
}

export function readImageFile(file: File) {
  if (file.size >= MAX_IMAGE_BYTES) {
    return Promise.reject(new Error("Image must be under 8 MB"));
  }
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result ?? "");
      const comma = result.indexOf(",");
      resolve(comma >= 0 ? result.slice(comma + 1) : result);
    };
    reader.onerror = () => reject(reader.error ?? new Error("Could not read image"));
    reader.readAsDataURL(file);
  });
}

export async function createJob(spec: string, imageBase64: string, marketplaces: string[]) {
  const body: { spec: string; image_base64: string; marketplaces?: string[] } = {
    spec,
    image_base64: imageBase64,
  };
  const selected = marketplaces.filter((item) => item === "amazon" || item === "walmart");
  const amazonOnly = selected.length === 0 || (selected.length === 1 && selected[0] === "amazon");
  if (!amazonOnly) body.marketplaces = selected;
  const { data } = await api.post<Job>("/v1/jobs", body);
  if (!data?.id) {
    throw new Error("Catalog Muse did not return a job id");
  }
  return data;
}

const jobsInFlight = new Map<string, Promise<Job>>();

export function getJob(jobId: string) {
  const existing = jobsInFlight.get(jobId);
  if (existing) return existing;

  const request = api
    .get<Job>(`/v1/jobs/${encodeURIComponent(jobId)}`)
    .then(({ data }) => {
      if (!data?.id) throw new Error("Unknown job");
      return data;
    })
    .finally(() => {
      if (jobsInFlight.get(jobId) === request) jobsInFlight.delete(jobId);
    });

  jobsInFlight.set(jobId, request);
  return request;
}

export async function decide(jobId: string, body: Record<string, unknown>) {
  const { data } = await api.post<Job>(
    `/v1/jobs/${encodeURIComponent(jobId)}/decisions`,
    body,
  );
  return data;
}

type JobListener = {
  onJob: (job: Job) => void;
  onError: (message: string) => void;
};

type JobStream = {
  source: EventSource;
  listeners: Set<JobListener>;
  closeTimer: number | null;
};

const jobStreams = new Map<string, JobStream>();

function closeJobStream(jobId: string) {
  const stream = jobStreams.get(jobId);
  if (!stream) return;
  if (stream.closeTimer !== null) window.clearTimeout(stream.closeTimer);
  stream.source.close();
  jobStreams.delete(jobId);
}

export function watchJob(
  jobId: string,
  onJob: (job: Job) => void,
  onError: (message: string) => void,
) {
  let stream = jobStreams.get(jobId);
  if (!stream) {
    const source = new EventSource(
      `${apiBase()}/v1/jobs/${encodeURIComponent(jobId)}/events`,
    );
    stream = { source, listeners: new Set(), closeTimer: null };
    const current = stream;
    source.addEventListener("status", (event) => {
      const message = event as MessageEvent<string>;
      try {
        const job = JSON.parse(message.data) as Job;
        current.listeners.forEach((listener) => listener.onJob(job));
        if (job.status === "approved" || job.status === "failed") closeJobStream(jobId);
      } catch {
        current.listeners.forEach((listener) =>
          listener.onError("Catalog Muse sent a status the app could not read"),
        );
      }
    });
    source.addEventListener("error", (event) => {
      if (!(event instanceof MessageEvent) || !event.data) return;
      const message = String(event.data);
      current.listeners.forEach((listener) => listener.onError(message));
      closeJobStream(jobId);
    });
    jobStreams.set(jobId, stream);
  }

  if (stream.closeTimer !== null) {
    window.clearTimeout(stream.closeTimer);
    stream.closeTimer = null;
  }
  const listener = { onJob, onError };
  stream.listeners.add(listener);

  return () => {
    const active = jobStreams.get(jobId);
    if (!active) return;
    active.listeners.delete(listener);
    if (active.listeners.size > 0) return;
    active.closeTimer = window.setTimeout(() => {
      if (jobStreams.get(jobId) === active && active.listeners.size === 0) {
        closeJobStream(jobId);
      }
    }, 0);
  };
}

export function errorMessage(error: unknown) {
  if (typeof error === "object" && error && "response" in error) {
    const data = (error as { response?: { data?: { error?: unknown; message?: unknown } } })
      .response?.data;
    if (typeof data?.error === "string" && data.error) return data.error;
    if (typeof data?.message === "string" && data.message) return data.message;
  }
  if (error instanceof Error) return error.message;
  return "Catalog Muse request failed";
}
