import { useState } from "react";
import { Check, CheckCircle, MessageSquare, RefreshCcw } from "lucide-react";
import { fileUrl } from "@/lib/catalogApi";
import { agentOutput, cutoutSource, type Job } from "./types";

type CutoutProps = {
  job: Job;
  originalUrl: string;
  busy: boolean;
  error?: string;
  onApprove: () => void;
  onRecut: (note: string) => void;
  onCancel: () => void;
};

export function Cutout({ job, originalUrl, busy, error = "", onApprove, onRecut, onCancel }: CutoutProps) {
  const [showRecut, setShowRecut] = useState(false);
  const [note, setNote] = useState("");
  const cutout = cutoutSource(job);
  const segment = job.agents?.find((agent) => agent.name === "segment");
  const concept = agentOutput(job, "segment")?.concept;
  const cutoutSrc = cutout ? fileUrl(job.id, cutout.file, cutout.url) : "";
  const failed = job.status === "failed" || segment?.state === "failed";
  const creating = !cutoutSrc && !failed && job.pending_agent !== "segment";
  const canDecide = job.pending_agent === "segment" || failed;

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-6">
      <h2 className="mb-6 flex items-center gap-2 text-lg font-semibold text-slate-800">
        <CheckCircle size={24} className="text-blue-600" /> Agentic Segmentation Review
      </h2>
      <div className="mb-6 grid gap-6 md:grid-cols-2">
        <figure>
          <figcaption className="mb-3 font-medium text-slate-700">Original Supplier Photo</figcaption>
          <div className="flex aspect-square items-center justify-center overflow-hidden rounded-lg bg-slate-200">
            {originalUrl ? (
              <img src={originalUrl} alt="Original supplier photo" className="h-full w-full object-contain" />
            ) : (
              <span className="text-sm text-slate-500">Original photo is kept in this session</span>
            )}
          </div>
        </figure>
        <figure>
          <figcaption className="mb-3 font-medium text-slate-700">
            SAM 3.1 Transparent Cutout
            {typeof concept === "string" && concept ? ` · ${concept}` : ""}
          </figcaption>
          <div className="flex aspect-square items-center justify-center overflow-hidden rounded-lg border border-slate-200 bg-slate-100">
            {cutoutSrc ? (
              <img src={cutoutSrc} alt="Cutout" className="h-full w-full object-contain" />
            ) : (
              <span className="px-6 text-center text-sm text-slate-500">
                {creating ? "Creating the cutout..." : "Cutout is not ready yet"}
              </span>
            )}
          </div>
        </figure>
      </div>
      <div className="flex items-center justify-between border-t border-slate-100 pt-6">
        <button
          type="button"
          disabled={busy}
          onClick={onCancel}
          className="text-sm text-slate-600 hover:text-slate-900 disabled:opacity-50"
        >
          Cancel
        </button>
        {showRecut ? (
          <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 p-2">
            <MessageSquare size={16} className="text-slate-400" />
            <input
              autoFocus
              value={note}
              disabled={busy}
              onChange={(event) => setNote(event.target.value)}
              placeholder="Required"
              className="w-60 bg-transparent text-sm outline-none disabled:opacity-50"
            />
            <button
              type="button"
              disabled={busy || !note.trim()}
              onClick={() => onRecut(note.trim())}
              className="inline-flex items-center gap-1 rounded bg-blue-600 px-2 py-1 text-xs text-white disabled:opacity-50"
            >
              {busy && <RefreshCcw size={12} className="animate-spin" />}
              {busy ? "Waiting..." : "Submit Recut"}
            </button>
            <button
              type="button"
              disabled={busy}
              onClick={() => setShowRecut(false)}
              className="px-1 text-sm disabled:opacity-50"
            >
              ✕
            </button>
          </div>
        ) : (
          <div className="flex gap-2">
            <button
              type="button"
              disabled={busy || !canDecide}
              onClick={() => setShowRecut(true)}
              className="flex items-center gap-2 rounded-md border border-slate-200 px-3 py-2 text-sm disabled:opacity-50"
            >
              <RefreshCcw size={16} /> Recut
            </button>
            <button
              type="button"
              disabled={busy || !cutoutSrc}
              onClick={onApprove}
              className="flex items-center gap-2 rounded-md bg-blue-600 px-3 py-2 text-sm text-white disabled:opacity-50"
            >
              {busy ? <RefreshCcw size={16} className="animate-spin" /> : <Check size={16} />}
              {busy ? "Waiting..." : "Approve Cutout"}
            </button>
          </div>
        )}
      </div>
      {showRecut && (
        <p className="mt-3 text-right text-sm text-slate-500">
          A short note, at most 4 words and no period, exclamation mark, or question mark, replaces
          the noun and runs SAM again.
        </p>
      )}
      {error && (
        <p className="mt-4 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </p>
      )}
    </section>
  );
}
