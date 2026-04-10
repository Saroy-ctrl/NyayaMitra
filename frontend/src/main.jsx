/**
 * main.jsx — React application bootstrap
 *
 * Mounts <App /> into the #root div defined in index.html.
 * StrictMode is enabled to surface side-effect issues during development.
 */

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <App />
  </StrictMode>
);
