import { NavLink } from "react-router-dom";
import { Images } from "lucide-react";

export const Sidebar = () => {
  return (
    <aside className="fixed left-0 top-0 z-50 flex h-full w-16 flex-col border-r border-border bg-card">
      <div className="flex items-center justify-center border-b border-border p-2">
        <NavLink
          to="/"
          className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-primary-foreground"
          title="Catalog Muse"
        >
          <Images className="h-5 w-5" />
        </NavLink>
      </div>
    </aside>
  );
};
