import type React from "react";

export const Layout: React.FC<{
  children: React.ReactNode;
}> = ({ children }) => {
  return <div className="min-h-screen bg-slate-50">{children}</div>;
};
