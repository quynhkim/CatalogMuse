import { useState } from "react";
import { Check, CheckCircle, ShieldCheck } from "lucide-react";
import { fileUrl } from "@/lib/catalogApi";
import { jobMarketplaces, listingCopy, sceneImages, type Job, type Marketplace } from "./types";

type ReviewProps = {
  job: Job;
  onRestart: () => void;
};

export function Review({ job, onRestart }: ReviewProps) {
  const places = jobMarketplaces(job);
  const [tab, setTab] = useState<Marketplace>(places[0] ?? "amazon");
  const active = places.includes(tab) ? tab : (places[0] ?? "amazon");
  const images = sceneImages(job);
  const copy = listingCopy(job, active);

  return (
    <section className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <div className="bg-linear-to-r from-slate-800 to-slate-900 px-6 py-6 text-center text-white">
        <h2 className="mb-2 flex items-center justify-center gap-2 text-2xl font-semibold">
          <CheckCircle size={28} className="text-green-400" /> Ready for Marketplace
        </h2>
        <p className="m-0 text-slate-300">All assets have passed human review.</p>
      </div>
      <div className="grid gap-8 p-8 md:grid-cols-5">
        <div className="md:col-span-2">
          <h3 className="mb-4 border-b border-slate-100 pb-2 font-semibold text-slate-700">
            Approved Visuals ({images.length})
          </h3>
          {images.length === 0 ? (
            <div className="rounded-lg border border-dashed border-slate-300 p-8 text-center text-slate-400">
              No images approved
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-3">
              {images.map((image, index) => (
                <div
                  key={image.file}
                  className={`relative overflow-hidden rounded-lg border border-slate-200 bg-slate-100 ${index === 0 ? "col-span-2 aspect-4/5" : "aspect-square"}`}
                >
                  <img
                    src={fileUrl(job.id, image.file, image.url)}
                    alt={image.file}
                    className="h-full w-full object-cover"
                  />
                  {index === 0 && (
                    <span className="absolute top-2 right-2 flex items-center gap-1 rounded-full bg-green-500 px-2 py-0.5 text-xs text-white">
                      <Check size={12} /> Primary
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
        <div className="md:col-span-3">
          <div className="mb-4 flex items-center justify-between border-b border-slate-100 pb-2 font-semibold text-slate-700">
            Approved Copy
            <span className="flex items-center gap-1 rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
              <ShieldCheck size={12} /> TOS Compliant
            </span>
          </div>
          <div className="flex gap-1 rounded-t-lg border border-b-0 border-slate-200 bg-slate-50 p-2">
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
          <div className="space-y-4 rounded-b-lg border border-slate-200 bg-slate-50 p-5">
            <div>
              <p className="mb-1 text-xs font-medium tracking-wide text-slate-500 uppercase">Final Title</p>
              <p className="text-sm font-semibold text-slate-800">{copy?.title || "No title returned"}</p>
            </div>
            {active === "walmart" ? (
              <>
                {copy?.shortDescription && (
                  <div
                    className="text-sm text-slate-700 [&_li]:ml-4 [&_li]:list-disc"
                    dangerouslySetInnerHTML={{ __html: copy.shortDescription }}
                  />
                )}
                {copy?.shelfDescription && (
                  <div
                    className="text-sm text-slate-700"
                    dangerouslySetInnerHTML={{ __html: copy.shelfDescription }}
                  />
                )}
              </>
            ) : (
              <>
                <ul className="list-disc space-y-2 pl-4 text-sm text-slate-700">
                  {(copy?.bullets ?? []).map((bullet) => (
                    <li key={bullet}>{bullet}</li>
                  ))}
                </ul>
                {copy?.description && <p className="text-sm text-slate-700">{copy.description}</p>}
              </>
            )}
          </div>
          <div className="mt-6">
            <button type="button" onClick={onRestart} className="h-12 rounded-md border border-slate-200 px-4">
              Start New Product
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
