import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "@/containers/App";

document.documentElement.classList.remove("dark");
try {
  localStorage.setItem("theme", "light");
} catch {
  // no-op
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
