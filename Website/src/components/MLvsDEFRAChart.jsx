import { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LabelList,
} from "recharts";

export default function MLvsDEFRAChart({ showML, mlScore, defraCarbonKg, mlCarbonKg }) {
  const [chartData, setChartData] = useState([]);
  const [reduction, setReduction] = useState(null);

  // Colors
  const defraColor = showML ? "#d1d5db" : "#9ca3af";
  const mlColor = "#4ade80";

  useEffect(() => {
    if (mlCarbonKg !== undefined && defraCarbonKg !== undefined) {
      const newData = [];

      if (!showML) {
        newData.push({ name: "DEFRA", CO2: defraCarbonKg });
      }

      newData.push({ name: "ML Model", CO2: mlCarbonKg });
      setChartData(newData);

      if (!showML && defraCarbonKg > 0 && mlCarbonKg > 0) {
        const percent = ((defraCarbonKg - mlCarbonKg) / defraCarbonKg) * 100;
        setReduction(percent.toFixed(1));
      } else {
        setReduction(null);
      }
    }
  }, [mlCarbonKg, defraCarbonKg, showML]);

  return (
    <div
      style={{
        marginTop: "1.5rem",
        padding: "1rem",
        border: "1px solid #ddd",
        borderRadius: "12px",
        background: "#f9f9f9",
      }}
    >
      <h3 style={{ fontSize: "1.2rem", marginBottom: "0.25rem" }}>📊 Carbon Emissions Comparison</h3>
      <p style={{ fontSize: "0.85rem", color: "#4b5563", marginBottom: "1rem" }}>
        Currently viewing: <strong>{showML ? "ML Model only" : "DEFRA vs ML Model"}</strong>
      </p>

      <ResponsiveContainer width="100%" height={250}>
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 10, right: 30, left: 30, bottom: 10 }}
        >
          <XAxis type="number" unit=" kg CO₂" tickFormatter={(v) => `${v.toFixed(2)} kg`} />
          <YAxis type="category" dataKey="name" width={90} />
          <Tooltip
            formatter={(value) =>
              `${new Intl.NumberFormat().format(parseFloat(value).toFixed(2))} kg CO₂`
            }
          />
          <Legend />

          {/* DEFRA */}
          {!showML && (
            <Bar
              dataKey="CO2"
              data={chartData.filter((d) => d.name === "DEFRA")}
              fill={defraColor}
              name="DEFRA"
              isAnimationActive={true}
            >
              <LabelList
                dataKey="CO2"
                position="right"
                formatter={(value) => `${parseFloat(value).toFixed(2)} kg`}
              />
            </Bar>
          )}

          {/* ML Model */}
          <Bar
            dataKey="CO2"
            data={chartData.filter((d) => d.name === "ML Model")}
            fill={mlColor}
            name="ML Model"
            isAnimationActive={true}
          >
            <LabelList
              dataKey="CO2"
              position="right"
              formatter={(value) => `${parseFloat(value).toFixed(2)} kg`}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      <p style={{ marginTop: "0.75rem", fontSize: "0.9rem" }}>
        Model Eco Score: <strong>{mlScore || "N/A"}</strong>
      </p>

      {reduction && !showML && (
        <p style={{ marginTop: "0.3rem", fontSize: "0.9rem", color: "#16a34a" }}>
          🌱 ML estimate is <strong>{reduction}%</strong> lower than DEFRA
        </p>
      )}
    </div>
  );
}
