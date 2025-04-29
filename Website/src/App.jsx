// src/App.jsx
import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import HomePage from "./pages/HomePage";
import LearnPage from "./pages/LearnPage";
import PredictPage from "./pages/PredictPage"; // <== Add this line

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/learn" element={<LearnPage />} />
        <Route path="/predict" element={<PredictPage />} /> {/* 👈 Add this */}
      </Routes>
    </Router>
  );
}
