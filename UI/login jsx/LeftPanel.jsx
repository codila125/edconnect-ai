import React from "react";
import FeaturesList from "./FeaturesList";

const LeftPanel = () => {
  return (
    <div className="login-container hidden md:flex md:w-1/3 flex-col justify-between p-8 text-white relative">
      <div className="floating-shape shape-1" />
      <div className="floating-shape shape-2" />

      <div className="relative z-10 flex flex-col h-full">
        <div className="flex items-center mb-6">
          <svg className="w-14 h-14 mr-3" viewBox="0 0 48 48" fill="none">
            <path d="M24 6L6 15L24 24L42 15L24 6Z" fill="white" />
            <path d="M12 18V30L24 36L36 30V18" stroke="white" strokeWidth="2" />
            <path d="M24 24V36" stroke="white" strokeWidth="2" />
            <path d="M30 12L18 18" stroke="white" strokeWidth="2" />
          </svg>
          <h1 className="text-4xl font-bold">ED CONNECT AI</h1>
        </div>
        <FeaturesList />
      </div>
    </div>
  );
};

export default LeftPanel;