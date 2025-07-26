// src/components/Login.jsx
import React from "react";
import LeftPanel from "./LeftPanel";
import RightPanel from "./RightPanel";

const Login = () => {
  return (
    <div className="flex flex-col md:flex-row h-screen">
      <LeftPanel />
      <RightPanel />
    </div>
  );
};

export default Login;