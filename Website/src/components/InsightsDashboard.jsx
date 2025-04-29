import React, { useEffect, useState } from "react";
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { motion } from "framer-motion";

const COLORS = [
  "#34d399", "#60a5fa", "#fbbf24", "#f87171", "#a78bfa",
  "#f472b6", "#2dd4bf", "#facc15", "#fb923c", "#818cf8"
];

export default function InsightsDashboard() {
  const [scoreData, setScoreData] = useState([]);
  const [materialData, setMaterialData] = useState([]);

  useEffect(() => {
    fetch("http://localhost:5000/insights")
      .then((res) => res.json())
      .then((data) => {
        if (!Array.isArray(data)) return;

        const scores = data.map((d) => d.true_eco_score).filter(Boolean);
        const materials = data.map((d) => d.material).filter(Boolean);

        // ✅ Score breakdown
        const scoreCounts = scores.reduce((acc, score) => {
          acc[score] = (acc[score] || 0) + 1;
          return acc;
        }, {});
        setScoreData(
          Object.entries(scoreCounts).map(([score, count]) => ({
            name: score,
            value: count,
          }))
        );

        // ✅ Top materials (deduped + sorted)
        const deduped = materials.reduce((acc, curr) => {
          const existing = acc.find((item) => item.name === curr);
          if (existing) existing.value += 1;
          else acc.push({ name: curr, value: 1 });
          return acc;
        }, []);
        setMaterialData(deduped.sort((a, b) => b.value - a.value).slice(0, 10));
      })
      .catch((err) => console.error("Failed to load insights:", err));
  }, []);

  return (
    <div className="bg-white rounded-2xl shadow-md p-6 mt-10 max-w-3xl w-full">
      <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
        📊 <span>Insights Dashboard</span>
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 🔵 Eco Score Bar Chart */}
        <div>
          <h3 className="text-sm font-medium text-gray-500 mb-2">
            Eco Score Distribution
          </h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={scoreData} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#34d399" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* 🟢 Pie Chart w/ animation */}
        <div>
          <h3 className="text-sm font-medium text-gray-500 mb-2">
            Top Materials Used
          </h3>
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, ease: "easeOut" }}
          >
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={materialData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={70}
                  innerRadius={30}
                  label
                  isAnimationActive={true}
                  animationBegin={0}
                  animationDuration={900}
                  animationEasing="ease-out"
                >
                  {materialData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={COLORS[index % COLORS.length]}
                    />
                  ))}
                </Pie>
                <Tooltip />
                <Legend layout="vertical" verticalAlign="middle" align="right" />
              </PieChart>
            </ResponsiveContainer>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
