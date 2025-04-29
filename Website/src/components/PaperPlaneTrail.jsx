import React from "react";

export default function PaperPlaneTrail() {
  return (
    <svg
      viewBox="0 0 1000 300"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="absolute top-0 left-0 w-full opacity-20 z-0 animate-fly"
      preserveAspectRatio="xMidYMid meet"
    >
      <path
        d="M0 150 Q 100 200 200 150 T 400 150 Q 500 100 600 150 T 800 150 Q 900 200 1000 150"
        stroke="black"
        strokeDasharray="12"
        strokeLinecap="round"
        strokeWidth="2"
      />
      <polygon
        points="1000,145 985,140 990,150 985,160"
        fill="black"
      />
    </svg>
  );
}
