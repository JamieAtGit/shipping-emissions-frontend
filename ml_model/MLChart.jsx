// ReactPopup/src/components/MLChart.jsx
import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export default function MLChart({ mlScore, carbonKg }) {
  const data = [
    {
      name: "ML Score",
      value: parseFloat(mlScore || 0),
    },
    {
      name: "CO₂ Estimate",
      value: parseFloat(carbonKg || 0),
    },
  ];

  return (
    <div className="w-full max-w-md mx-auto mt-6">
      <h4 className="text-lg font-medium text-center mb-2">
        🔍 Prediction Comparison
      </h4>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="value" fill="#34D399" radius={[6, 6, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
