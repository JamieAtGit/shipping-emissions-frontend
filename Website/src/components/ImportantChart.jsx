import React, { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LabelList } from "recharts";

export default function ImportantChart() {
  const [data, setData] = useState([]);

  useEffect(() => {
    fetch("http://localhost:5000/api/feature-importance")
      .then((res) => res.json())
      .then(setData)
      .catch((err) => console.error("Feature importances fetch error:", err));
  }, []);

  return (
    <div className="bg-white p-6 rounded-lg shadow-md max-w-3xl mt-10 mx-auto">
      <h3 className="text-lg font-semibold text-gray-700 mb-4">🧠 Feature Importance</h3>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart layout="vertical" data={data} margin={{ top: 10, right: 30, left: 40, bottom: 10 }}>
          <XAxis type="number" unit="%" />
          <YAxis type="category" dataKey="feature" width={100} />
          <Tooltip formatter={(value) => `${value}%`} />
          <Bar dataKey="importance" fill="#34d399">
            <LabelList dataKey="importance" position="right" formatter={(val) => `${val}%`} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
