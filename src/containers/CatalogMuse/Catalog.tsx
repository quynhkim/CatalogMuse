import { ExternalLink, Image as ImageIcon, Package, Plus, ShoppingBag, ShoppingCart } from "lucide-react";
import type { CatalogItem } from "./types";

type CatalogProps = {
  catalog: CatalogItem[];
  onAddNew: () => void;
};

export function Catalog({ catalog, onAddNew }: CatalogProps) {
  return (
    <div>
      <div className="mb-6 flex items-end justify-between">
        <div>
          <h2 className="m-0 text-2xl font-semibold text-slate-800">Product Catalog</h2>
          <p className="mt-1 text-slate-500">Manage and sync your published marketplace listings.</p>
        </div>
        <button
          type="button"
          onClick={onAddNew}
          className="flex h-10 items-center gap-2 rounded-md bg-blue-600 px-3 text-sm text-white"
        >
          <Plus size={16} /> New Product
        </button>
      </div>
      {catalog.length === 0 ? (
        <section className="rounded-lg border border-slate-200 bg-white py-12 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full border border-slate-100 bg-slate-50">
            <Package size={32} className="text-slate-300" />
          </div>
          <h3 className="m-0 text-lg font-semibold text-slate-700">Your catalog is empty</h3>
          <p className="mx-auto mt-2 mb-6 max-w-sm text-slate-500">
            You haven't published any products yet. Run a product through the CatalogMuse pipeline to generate compliant assets.
          </p>
          <button type="button" onClick={onAddNew} className="h-10 rounded-md bg-slate-900 px-4 text-sm text-white">
            Start New Pipeline
          </button>
        </section>
      ) : (
        <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-200 bg-slate-50 text-slate-500">
              <tr>
                <th className="px-4 py-3 font-medium">Product details</th>
                <th className="px-4 py-3 font-medium">Marketplaces</th>
                <th className="px-4 py-3 font-medium">Visuals</th>
                <th className="px-4 py-3 font-medium">Date Added</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 text-right font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {catalog.map((item) => (
                <tr key={item.id} className="border-b border-slate-100 last:border-0">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      <div className="h-10 w-10 overflow-hidden rounded border border-slate-200 bg-slate-100">
                        {item.imageUrl && <img src={item.imageUrl} alt="" className="h-full w-full object-cover" />}
                      </div>
                      <div>
                        <div className="max-w-64 truncate font-semibold text-slate-800">{item.title}</div>
                        <div className="text-xs text-slate-400">{item.id}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      {item.marketplaces.includes("Amazon") && (
                        <span className="rounded-md border border-orange-100 bg-orange-50 p-1.5 text-orange-600">
                          <ShoppingBag size={14} />
                        </span>
                      )}
                      {item.marketplaces.includes("Walmart") && (
                        <span className="rounded-md border border-blue-100 bg-blue-50 p-1.5 text-blue-600">
                          <ShoppingCart size={14} />
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className="inline-flex items-center gap-1 rounded border border-slate-200 px-2 py-0.5 text-xs">
                      <ImageIcon size={12} /> {item.imageCount} Assets
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-600">{item.date}</td>
                  <td className="px-4 py-3">
                    <span className="inline-flex items-center gap-1.5 rounded-full bg-green-50 px-2 py-0.5 text-xs text-green-700">
                      <span className="h-1.5 w-1.5 rounded-full bg-green-500" /> Active
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right text-slate-400">
                    <ExternalLink size={16} className="ml-auto" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
