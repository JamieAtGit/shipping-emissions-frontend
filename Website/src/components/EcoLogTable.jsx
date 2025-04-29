import React, { useEffect, useState } from "react";
import {
  Table,
  Thead,
  Tr,
  Th,
  Td,
  Tbody,
  Collapse,
  Box,
  Button,
} from "@chakra-ui/react";
import { ChevronDownIcon, ChevronUpIcon } from "@chakra-ui/icons";
import { useDisclosure } from "@chakra-ui/react";

export default function EcoLogTable() {
  const [data, setData] = useState([]);
  const [scoreFilter, setScoreFilter] = useState("");
  const [materialFilter, setMaterialFilter] = useState("");
  const { isOpen, onToggle } = useDisclosure(); // ✅ inside component

  useEffect(() => {
    fetch("http://localhost:5000/api/eco-data")
      .then((res) => res.json())
      .then((rows) => setData(rows))
      .catch((err) => console.error("Error loading eco data:", err));
  }, []);

  const filteredData = data.filter((row) => {
    return (
      (scoreFilter === "" || row.eco_score === scoreFilter) &&
      (materialFilter === "" || row.material === materialFilter)
    );
  });

  const uniqueScores = [...new Set(data.map((row) => row.eco_score))];
  const uniqueMaterials = [...new Set(data.map((row) => row.material))];

  const downloadCSV = () => {
    const headers = [
      "title",
      "material",
      "weight",
      "transport",
      "recyclability",
      "eco_score",
      "co2_emissions",
      "origin",
    ];
    const csvRows = [headers.join(",")];
    filteredData.forEach((row) => {
      const values = headers.map((h) => JSON.stringify(row[h] || ""));
      csvRows.push(values.join(","));
    });
    const csvData = new Blob([csvRows.join("\n")], { type: "text/csv" });
    const url = URL.createObjectURL(csvData);
    const link = document.createElement("a");
    link.href = url;
    link.download = "eco_dataset.csv";
    link.click();
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold text-gray-700">📜 Eco Product Log</h2>
        <button
          onClick={downloadCSV}
          className="bg-green-600 text-white text-sm px-4 py-1 rounded hover:bg-green-700"
        >
          Download CSV
        </button>
      </div>

      <div className="flex gap-4 mb-4">
        <select
          className="border px-3 py-2 rounded"
          value={scoreFilter}
          onChange={(e) => setScoreFilter(e.target.value)}
        >
          <option value="">All Scores</option>
          {uniqueScores.map((score, index) => (
            <option key={index} value={score}>{score}</option>
          ))}

        </select>

        <select
          className="border px-3 py-2 rounded"
          value={materialFilter}
          onChange={(e) => setMaterialFilter(e.target.value)}
        >
          <option value="">All Materials</option>
          {uniqueMaterials.map((mat) => (
            <option key={mat} value={mat}>{mat}</option>
          ))}
        </select>
      </div>

      {/* ✅ Simple table header, no expandable rows here */}
      <Table size="sm" variant="simple">
        <Thead>
          <Tr>
            <Th className="text-center">All Logged Products</Th>
          </Tr>
        </Thead>
      </Table>

      {/* ✅ Toggle all rows below table */}
      <div className="mt-4">
        <Button
          onClick={onToggle}
          rightIcon={isOpen ? <ChevronUpIcon /> : <ChevronDownIcon />}
          colorScheme="green"
          variant="outline"
          mb={4}
        >
          📦 Show Logged Products
        </Button>

        <Collapse in={isOpen} animateOpacity>
          <div className="space-y-4">
            {filteredData.map((row, i) => (
              <Box
                key={i}
                p={4}
                shadow="md"
                borderWidth="1px"
                borderRadius="md"
                bg="gray.50"
              >
                <p><strong className="text-green-700">{row.title}</strong></p>
                <p><strong>Material:</strong> {row.material}</p>
                <p><strong>Weight:</strong> {row.weight} kg</p>
                <p><strong>Transport:</strong> {row.transport}</p>
                <p><strong>Recyclability:</strong> {row.recyclability}</p>
                <p><strong>Eco Score:</strong> {row.eco_score}</p>
                <p><strong>CO₂:</strong> {row.co2_emissions} kg</p>
                <p><strong>Origin:</strong> {row.origin}</p>
              </Box>
            ))}
          </div>
        </Collapse>
      </div>
    </div>
  );
}
