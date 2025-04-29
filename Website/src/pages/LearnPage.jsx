// src/pages/LearnPage.jsx
import React from "react";
import ImportantChart from "../components/ImportantChart";
import { Link } from "react-router-dom";

export default function LearnPage() {
  return (
    <div className="relative min-h-screen bg-white">
      {/* Header */}
      <header className="w-full max-w-6xl mx-auto py-6 px-4 flex justify-between items-center border-b">
        <h1 className="text-2xl font-bold text-green-700">🌿 Impact Tracker</h1>
        <nav className="space-x-6 text-gray-600 text-sm">
          <Link to="/">Home</Link>
          <Link to="/learn">Learn</Link>
        </nav>
      </header>

      {/* Page Content */}
      <main className="max-w-5xl mx-auto px-4 py-10">
        <h2 className="text-3xl font-semibold mb-6">📘 Feature Importance</h2>
        <ImportantChart />

        <section className="mt-12">
          <h3 className="text-2xl font-semibold mb-2">🧠 How Predictions Are Made</h3>
          <p className="text-gray-700 leading-relaxed">
            Inputs are encoded using label encoders and passed into an XGBoost model.
            We also use <code>predict_proba</code> to calculate confidence in each prediction.
            The feature importance chart shows which features (like weight, material, origin, etc.)
            are most influential in the final eco score classification.
          </p>
        </section>
      </main>

      {/* Footer */}
      <footer className="w-full border-t py-4 text-sm text-center text-gray-400 mt-auto">
        © 2025 EcoTrack. Built with 💚 for a greener future.
      </footer>
    </div>
  );
}
