import { useState } from "react";
import { FileText, Image as ImageIcon, Loader2, ShoppingBag, ShoppingCart, UploadCloud, Wand2 } from "lucide-react";

const MAX_IMAGE_BYTES = 8 * 1024 * 1024;

type IntakeProps = {
  busy: boolean;
  onSubmit: (input: {
    spec: string;
    file: File;
    previewUrl: string;
    marketplaces: string[];
  }) => void;
};

export function Intake({ busy, onSubmit }: IntakeProps) {
  const [spec, setSpec] = useState("");
  const [amazon, setAmazon] = useState(true);
  const [walmart, setWalmart] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [localError, setLocalError] = useState("");

  const chooseFile = (next: File | undefined) => {
    if (!next) return;
    if (next.size >= MAX_IMAGE_BYTES) {
      setLocalError("Image must be under 8 MB");
      return;
    }
    setLocalError("");
    setFile(next);
    setPreviewUrl(URL.createObjectURL(next));
  };

  const submit = () => {
    if (!file || !previewUrl) {
      setLocalError("Add a supplier photo");
      return;
    }
    if (!spec.trim()) {
      setLocalError("Product spec is required");
      return;
    }
    const marketplaces = [amazon ? "amazon" : "", walmart ? "walmart" : ""].filter(Boolean);
    onSubmit({ spec: spec.trim(), file, previewUrl, marketplaces });
  };

  return (
    <div className="grid gap-6 md:grid-cols-2">
      <section className="rounded-lg border border-slate-200 bg-white p-6">
        <h2 className="mb-4 flex items-center gap-2 font-semibold text-slate-800">
          <ImageIcon size={20} className="text-blue-600" /> Raw Supplier Image
        </h2>
        <label
          className="flex h-64 cursor-pointer flex-col items-center justify-center overflow-hidden rounded-lg border-2 border-dashed border-slate-300 bg-slate-50"
          onDragOver={(event) => event.preventDefault()}
          onDrop={(event) => {
            event.preventDefault();
            chooseFile(event.dataTransfer.files[0]);
          }}
        >
          {previewUrl ? (
            <img src={previewUrl} alt="Supplier upload" className="h-full w-full object-contain" />
          ) : (
            <>
              <UploadCloud size={48} className="mb-3 text-slate-400" />
              <p className="m-0 text-sm font-medium text-slate-600">Drag and drop a raw image here</p>
              <p className="mt-1 mb-0 text-xs text-slate-400">JPG or PNG under 8 MB</p>
            </>
          )}
          <input
            type="file"
            accept="image/jpeg,image/png"
            className="hidden"
            onChange={(event) => chooseFile(event.target.files?.[0])}
          />
        </label>
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-6">
        <h2 className="mb-4 flex items-center gap-2 font-semibold text-slate-800">
          <FileText size={20} className="text-blue-600" /> Product Details
        </h2>
        <label className="mb-1.5 block text-sm font-medium text-slate-700">Product Spec Sheet</label>
        <textarea
          rows={5}
          value={spec}
          onChange={(event) => setSpec(event.target.value)}
          placeholder="Paste supplier specs here (dimensions, materials, features)..."
          className="mb-4 w-full rounded-md border border-slate-200 px-3 py-2 text-sm outline-none focus:border-blue-500"
        />
        <p className="mb-2 text-sm font-medium text-slate-700">Target Marketplaces</p>
        <div className="mb-6 flex gap-4">
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={amazon} onChange={(event) => setAmazon(event.target.checked)} />
            <ShoppingBag size={16} className="text-orange-500" /> Amazon
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={walmart} onChange={(event) => setWalmart(event.target.checked)} />
            <ShoppingCart size={16} className="text-blue-600" /> Walmart
          </label>
        </div>
        {localError && <p className="mb-3 text-sm text-red-600">{localError}</p>}
        <button
          type="button"
          disabled={busy}
          onClick={submit}
          className="flex h-12 w-full items-center justify-center gap-2 rounded-md bg-blue-600 font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {busy ? <Loader2 size={16} className="animate-spin" /> : <Wand2 size={16} />}
          {busy ? "Waiting..." : "Generate Agentic Cutout"}
        </button>
      </section>
    </div>
  );
}
