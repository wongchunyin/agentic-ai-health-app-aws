import {StrictMode} from "react";
import ReactDOM from "react-dom/client";

import "./assets/global.css";
import "./assets/main.css";
import "./assets/chatbot.css";
import "./assets/profile.css";
import "./assets/plan.css";

import App from "./App.jsx";

const root = ReactDOM.createRoot(document.getElementById("root"));

root.render(
  <StrictMode>
    <App />
  </StrictMode>
);
