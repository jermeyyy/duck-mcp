import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import "highlight.js/styles/vs2015.css";
import "./styles/app.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
