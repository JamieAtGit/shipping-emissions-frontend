// src/components/ChallengeForm.jsx
import React, { useState } from "react";

export default function ChallengeForm({ productId, predictedScore }) {
  const [userScore, setUserScore] = useState("");
  const [comment, setComment] = useState("");
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch("/api/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          product_id: productId,
          predicted_score: predictedScore,
          user_score: userScore,
          comment: comment,
        }),
      });

      if (response.ok) {
        setSuccess(true);
        setUserScore("");
        setComment("");
      } else {
        console.error("Feedback submission failed");
      }
    } catch (error) {
      console.error("Error submitting feedback:", error);
    }
  };

  return (
    <div className="mt-6 p-4 border rounded-md shadow-md">
      <h3 className="text-lg font-semibold mb-2">Challenge the Prediction</h3>
      {success ? (
        <div className="text-green-500">Thank you for your feedback!</div>
      ) : (
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block mb-1">What do you believe the correct eco-score is?</label>
            <select
              value={userScore}
              onChange={(e) => setUserScore(e.target.value)}
              required
              className="border rounded p-2 w-full"
            >
              <option value="">Select Score</option>
              <option value="A">A (Most Eco-Friendly)</option>
              <option value="B">B</option>
              <option value="C">C</option>
              <option value="D">D</option>
              <option value="E">E (Least Eco-Friendly)</option>
            </select>
          </div>

          <div className="mb-4">
            <label className="block mb-1">Why? (Optional)</label>
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              rows="3"
              className="border rounded p-2 w-full"
              placeholder="Tell us why you think differently..."
            />
          </div>

          <button
            type="submit"
            className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded"
          >
            Submit Feedback
          </button>
        </form>
      )}
    </div>
  );
}
