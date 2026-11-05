import { useState } from "react";
import { AlertCircle, CheckCircle, Loader2, ShieldCheck } from "lucide-react";
import {
  jobMarketplaces,
  listingCopy,
  ruleViolations,
  violations,
  type Job,
  type ListingCopy,
  type Marketplace,
} from "./types";

type SeoProps = {
  job: Job;
  busy: boolean;
  onApprove: () => void;
  onChange: (note: string) => void;
  onBack: () => void;
};

export function Seo({ job, busy, onApprove, onChange, onBack }: SeoProps) {
  const places = jobMarketplaces(job);
  const [tab, setTab] = useState<Marketplace>(places[0] ?? "amazon");
  const [note, setNote] = useState("");
  const active = places.includes(tab) ? tab : (places[0] ?? "amazon");
  const copy = listingCopy(job, active);
  const issues = violations(job);
  const placeIssues = ruleViolations(job, active);
  const waiting = job.pending_agent === "rules";
  const canApprove = waiting && job.approve_allowed === true && issues.length === 0;

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <section className="overflow-hidden rounded-lg border border-slate-200 bg-white lg:col-span-2">
        <div className="flex gap-1 border-b border-slate-200 bg-slate-50 p-2">
          {places.map((marketplace) => (
            <button
              key={marketplace}
              type="button"
              onClick={() => setTab(marketplace)}
              className={`rounded-md px-3 py-2 text-sm font-medium ${
                active === marketplace
                  ? marketplace === "amazon"
                    ? "bg-white text-orange-600"
                    : "bg-white text-blue-600"
                  : "text-slate-500"
              }`}
            >
              {marketplace === "amazon" ? "Amazon Listing" : "Walmart Listing"}
            </button>
          ))}
        </div>
        <div className="space-y-4 p-6">
          {copy ? (
            <ListingFields copy={copy} walmart={active === "walmart"} />
          ) : (
            <p className="text-sm text-slate-500">
              {waiting ? "Copy is not in this response yet." : "The copywriter and auditor are preparing the listing..."}
            </p>
          )}
          <label className="block text-sm font-medium text-slate-700">
            Note for the copywriter
            <textarea
              rows={2}
              value={note}
              disabled={busy}
              onChange={(event) => setNote(event.target.value)}
              placeholder="Drop the size from the title."
              className="mt-1 w-full rounded-md border border-slate-200 px-3 py-2 font-normal outline-none focus:border-blue-500 disabled:opacity-50"
            />
          </label>
          <button
            type="button"
            disabled={busy || !note.trim() || !waiting}
            onClick={() => onChange(note.trim())}
            className="inline-flex items-center gap-2 rounded-md border border-slate-200 px-3 py-2 text-sm disabled:opacity-50"
          >
            {busy && <Loader2 size={14} className="animate-spin" />}
            {busy ? "Waiting..." : "Send changes"}
          </button>
        </div>
      </section>

      <aside className="flex flex-col overflow-hidden rounded-lg border border-slate-800 bg-slate-900 font-mono text-sm text-slate-300">
        <div className="flex items-center justify-between border-b border-slate-800 bg-slate-950 px-3 py-3">
          <span className="flex items-center gap-2 font-semibold text-sky-400">
            <ShieldCheck size={16} /> Muse Spark Auditor
          </span>
          <span className={`h-2 w-2 rounded-full ${issues.length ? "bg-yellow-400" : "bg-green-500"}`} />
        </div>
        <div className="flex flex-1 flex-col gap-3 p-4">
          {placeIssues.length === 0 && issues.length === 0 ? (
            <p className="m-0 flex gap-2 text-green-400">
              <CheckCircle size={16} className="mt-0.5 shrink-0" />
              {waiting ? "Every selected marketplace is clear." : "Waiting for the rules audit."}
            </p>
          ) : (
            (placeIssues.length ? placeIssues : issues).map((issue) => (
              <p key={issue} className="m-0 flex gap-2 text-yellow-300">
                <AlertCircle size={16} className="mt-0.5 shrink-0" /> {issue}
              </p>
            ))
          )}
        </div>
        <div className="flex gap-3 border-t border-slate-800 bg-slate-950 p-4">
          <button type="button" disabled={busy} onClick={onBack} className="text-slate-400 disabled:opacity-50">
            Back
          </button>
          <button
            type="button"
            disabled={busy || !canApprove}
            onClick={onApprove}
            className="inline-flex flex-1 items-center justify-center gap-2 rounded-md bg-blue-600 py-2 text-white disabled:opacity-50"
          >
            {busy && <Loader2 size={14} className="animate-spin" />}
            {busy ? "Waiting..." : "Approve listing"}
          </button>
        </div>
      </aside>
    </div>
  );
}

function ListingFields({ copy, walmart }: { copy: ListingCopy; walmart: boolean }) {
  return (
    <>
      <Field label="Product Title" value={copy.title} />
      {walmart ? (
        <>
          <HtmlField label="Key Features" html={copy.shortDescription} />
          <HtmlField label="Shelf Description" html={copy.shelfDescription} />
        </>
      ) : (
        <>
          <Field label="Key Features (Bullet Points)" value={copy.bullets.join("\n")} multiline />
          <Field label="Product Description" value={copy.description} multiline />
        </>
      )}
    </>
  );
}

function Field({ label, value, multiline = false }: { label: string; value: string; multiline?: boolean }) {
  return (
    <label className="block text-sm font-medium text-slate-700">
      {label}
      {multiline ? (
        <textarea readOnly rows={4} value={value} className="mt-1 w-full rounded-md border border-slate-200 px-3 py-2 font-normal" />
      ) : (
        <input readOnly value={value} className="mt-1 w-full rounded-md border border-slate-200 px-3 py-2 font-semibold" />
      )}
    </label>
  );
}

function HtmlField({ label, html }: { label: string; html: string }) {
  return (
    <div>
      <p className="mb-1 text-sm font-medium text-slate-700">{label}</p>
      {html ? (
        <div
          className="rounded-md border border-slate-200 px-3 py-2 text-sm [&_li]:ml-4 [&_li]:list-disc"
          dangerouslySetInnerHTML={{ __html: html }}
        />
      ) : (
        <p className="text-sm text-slate-400">None returned</p>
      )}
    </div>
  );
}
