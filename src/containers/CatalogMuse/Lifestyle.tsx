import { useState } from "react";
import { Check, ChevronRight, LayoutGrid, Loader2, Plus, Wand2, X } from "lucide-react";
import { fileUrl } from "@/lib/catalogApi";
import { artStyles, sceneImages, type Job } from "./types";

type LifestyleProps = {
  job: Job;
  busy: boolean;
  onGenerate: (styles: string[], variations: number) => void;
  onChooseImages: (files: string[]) => void;
  onBack: () => void;
};

export function Lifestyle({ job, busy, onGenerate, onChooseImages, onBack }: LifestyleProps) {
  const incoming = artStyles(job);
  const styleKey = JSON.stringify(incoming);
  const images = sceneImages(job);
  const choosing = job.pending_agent === "scene";
  const [styles, setStyles] = useState<string[]>(incoming.length ? incoming : [""]);
  const [selected, setSelected] = useState<number[]>(incoming.map((_, index) => index));
  const [seenStyleKey, setSeenStyleKey] = useState(styleKey);
  const [variations, setVariations] = useState(2);
  const [picked, setPicked] = useState<string[]>([]);

  if (styleKey !== seenStyleKey) {
    setSeenStyleKey(styleKey);
    const next = JSON.parse(styleKey) as string[];
    if (next.length > 0) {
      setStyles(next);
      setSelected(next.map((_, index) => index));
    }
  }

  const chosenStyles = selected
    .map((index) => styles[index]?.trim() ?? "")
    .filter(Boolean);

  const toggleStyle = (index: number) => {
    setSelected((current) =>
      current.includes(index) ? current.filter((item) => item !== index) : [...current, index],
    );
  };

  const removeStyle = (index: number) => {
    setStyles((current) => current.filter((_, itemIndex) => itemIndex !== index));
    setSelected((current) =>
      current
        .filter((item) => item !== index)
        .map((item) => (item > index ? item - 1 : item)),
    );
  };

  return (
    <div className="space-y-6">
      <section className="rounded-lg border border-slate-200 bg-white p-6">
        <h2 className="mb-4 flex items-center gap-2 font-semibold text-slate-800">
          <LayoutGrid size={20} className="text-blue-600" /> Art Director Agent Options
        </h2>
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <p className="text-sm text-slate-500">
            Select and edit the suggested prompts, or add your own style.
          </p>
          <label className="flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-2 py-1 text-xs font-medium text-slate-500">
            Variations per style
            <select
              value={variations}
              disabled={busy}
              onChange={(event) => setVariations(Number(event.target.value))}
              className="bg-transparent text-sm text-slate-800 outline-none disabled:opacity-50"
            >
              {[1, 2, 3, 4].map((count) => (
                <option key={count} value={count}>
                  {count} {count === 1 ? "Variation" : "Variations"}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div className="mb-6 grid gap-4 md:grid-cols-2">
          {styles.map((style, index) => {
            const active = selected.includes(index);
            const custom = index >= incoming.length;
            return (
              <div
                key={index}
                className={`rounded-lg border-2 p-2 ${active ? "border-blue-600 bg-blue-50/40" : "border-slate-200"}`}
              >
                <div className="flex items-center justify-between">
                  <button
                    type="button"
                    onClick={() => toggleStyle(index)}
                    className="flex items-center gap-2 p-2 text-xs font-semibold tracking-wide text-slate-700 uppercase"
                  >
                    <input type="checkbox" readOnly checked={active} /> Style {index + 1}
                  </button>
                  {custom && (
                    <button
                      type="button"
                      aria-label={`Remove style ${index + 1}`}
                      onClick={() => removeStyle(index)}
                      className="mr-1 shrink-0 rounded p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                    >
                      <X size={14} />
                    </button>
                  )}
                </div>
                <textarea
                  rows={3}
                  value={style}
                  disabled={busy}
                  onChange={(event) =>
                    setStyles((current) =>
                      current.map((item, itemIndex) =>
                        itemIndex === index ? event.target.value : item,
                      ),
                    )
                  }
                  placeholder="Describe the aesthetic prompt..."
                  className="w-full bg-transparent px-2 text-sm outline-none"
                />
              </div>
            );
          })}
          {styles.length < 8 && (
            <button
              type="button"
              disabled={busy}
              onClick={() => {
                setStyles((current) => [...current, ""]);
                setSelected((current) => [...current, styles.length]);
              }}
              className="flex min-h-32 flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed border-slate-300 text-slate-500 disabled:opacity-50"
            >
              <Plus size={24} />
              <span className="text-sm font-medium">Add Custom Style</span>
            </button>
          )}
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            disabled={busy}
            onClick={onBack}
            className="rounded-md border border-slate-200 px-3 py-2 text-sm disabled:opacity-50"
          >
            Back
          </button>
          <button
            type="button"
            disabled={busy || choosing || chosenStyles.length === 0}
            onClick={() => onGenerate(chosenStyles, variations)}
            className="flex items-center gap-2 rounded-md bg-slate-900 px-3 py-2 text-sm text-white disabled:opacity-50"
          >
            {busy && !choosing ? <Loader2 size={16} className="animate-spin" /> : <Wand2 size={16} />}
            {busy && !choosing
              ? "Waiting..."
              : `Generate ${chosenStyles.length * variations} Images`}
          </button>
        </div>
      </section>

      {images.length > 0 && (
        <section className="rounded-lg border border-slate-200 bg-white p-6">
          <h3 className="mb-4 font-semibold text-slate-800">Scene images</h3>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {images.map((image) => {
              const active = picked.includes(image.file);
              const src = fileUrl(job.id, image.file, image.url);
              return (
                <button
                  key={image.file}
                  type="button"
                  onClick={() =>
                    setPicked((current) =>
                      current.includes(image.file)
                        ? current.filter((file) => file !== image.file)
                        : [...current, image.file],
                    )
                  }
                  className={`relative aspect-4/5 overflow-hidden rounded-lg border-2 bg-slate-100 ${active ? "border-green-500" : "border-slate-200"}`}
                >
                  <img src={src} alt={image.file} className="h-full w-full object-cover" />
                  <span className="absolute right-2 bottom-2 rounded bg-white/80 px-1.5 py-0.5 text-[10px] font-medium text-slate-600">
                    {image.style ? `Style ${image.style}` : image.file}
                    {image.variation ? ` · V${image.variation}` : ""}
                  </span>
                  {active && (
                    <span className="absolute top-2 right-2 flex h-6 w-6 items-center justify-center rounded-full bg-green-500 text-white">
                      <Check size={16} />
                    </span>
                  )}
                </button>
              );
            })}
          </div>
          <div className="mt-6 flex items-center justify-end gap-3 border-t border-slate-100 pt-4">
            <span className="text-sm font-medium text-slate-500">{picked.length} approved</span>
            <button
              type="button"
              disabled={busy || !choosing || picked.length === 0}
              onClick={() => onChooseImages(picked)}
              className="flex items-center gap-2 rounded-md bg-blue-600 px-3 py-2 text-sm text-white disabled:opacity-50"
            >
              {busy && choosing ? (
                <>
                  <Loader2 size={16} className="animate-spin" /> Waiting...
                </>
              ) : (
                <>
                  Next Step <ChevronRight size={16} />
                </>
              )}
            </button>
          </div>
        </section>
      )}
    </div>
  );
}
