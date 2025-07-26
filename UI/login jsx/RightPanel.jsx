import React, { useEffect, useState } from "react";
import Tabs from "./Tabs";

const RightPanel = () => {
  const [semester, setSemester] = useState("");

  useEffect(() => {
    const now = new Date();
    const month = now.getMonth();
    const year = now.getFullYear();
    let sem;
    if (month <= 4) sem = `Spring Semester ${year}`;
    else if (month <= 7) sem = `Summer Semester ${year}`;
    else sem = `Fall Semester ${year}`;
    setSemester(sem);
  }, []);

  return (
    <div
      className="form-container w-full md:w-2/3 flex flex-col h-full relative"
      style={{
        backgroundImage: "url('teach.jpeg')",
        backgroundSize: "cover",
        backgroundPosition: "center"
      }}
    >
      <div className="absolute inset-0 bg-black/40 z-0" />
      <div className="relative z-10 flex flex-col h-full">
        <div className="flex justify-between items-center p-6 border-b border-gray-200 bg-white/60 backdrop-blur-sm z-10">
          <div className="flex items-center md:hidden">
            <svg className="w-10 h-10 mr-2 text-blue-800" viewBox="0 0 48 48" fill="none">
              <path d="M24 6L6 15L24 24L42 15L24 6Z" fill="currentColor" />
              <path d="M12 18V30L24 36L36 30V18" stroke="currentColor" strokeWidth="2" />
              <path d="M24 24V36" stroke="currentColor" strokeWidth="2" />
              <path d="M30 12L18 18" stroke="currentColor" strokeWidth="2" />
            </svg>
            <span className="font-bold text-xl">ED CONNECT AI</span>
          </div>
          <div className="bg-blue-100 text-blue-800 px-4 py-2 rounded-full text-sm font-medium">
            <span>{semester}</span>
          </div>
        </div>
        <Tabs />
      </div>
    </div>
  );
};

export default RightPanel;