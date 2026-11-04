export function BrandLogo() {
  return (
    <div className="flex items-center gap-3">
      <svg viewBox="0 0 48 48" className="h-10 w-10" fill="none" aria-hidden="true">
        <defs>
          <linearGradient id="orangeGrad" x1="10" y1="12" x2="26" y2="35" gradientUnits="userSpaceOnUse">
            <stop stopColor="#F59E0B" />
            <stop offset="1" stopColor="#EA580C" />
          </linearGradient>
          <linearGradient id="blueGrad" x1="22" y1="21" x2="35" y2="40" gradientUnits="userSpaceOnUse">
            <stop stopColor="#3B82F6" />
            <stop offset="1" stopColor="#1D4ED8" />
          </linearGradient>
        </defs>
        <rect x="8" y="14" width="26" height="28" rx="4" transform="rotate(-12 8 14)" fill="#334155" opacity="0.6" />
        <rect x="12" y="16" width="26" height="28" rx="4" transform="rotate(-4 12 16)" fill="#1E293B" opacity="0.9" />
        <path d="M 28 18 C 21 15 13 19 13 27 C 13 35 21 39 28 36" stroke="url(#orangeGrad)" strokeWidth="6" strokeLinecap="round" />
        <path d="M 17 38 L 17 25 L 24 32 L 31 25 L 31 38" stroke="url(#blueGrad)" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M 35 11 C 35 15.5 38.5 19 43 19 C 38.5 19 35 22.5 35 27 C 35 22.5 31.5 19 27 19 C 31.5 19 35 15.5 35 11 Z" fill="url(#orangeGrad)" />
      </svg>
      <div className="mt-1 flex flex-col justify-center">
        <div className="flex items-center text-[1.35rem] leading-none font-extrabold tracking-tight">
          <span className="text-slate-800">Catalog</span>
          <span className="bg-linear-to-r from-orange-500 to-blue-600 bg-clip-text text-transparent">
            Muse
          </span>
        </div>
        <span className="mt-1 text-[0.65rem] leading-none font-bold tracking-[0.22em] text-slate-400 uppercase">
          By AsinZen
        </span>
      </div>
    </div>
  );
}
