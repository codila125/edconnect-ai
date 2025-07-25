import React, { useState } from "react";

const Tabs = () => {
  const [activeTab, setActiveTab] = useState("login");

  const handleGoogleLogin = () => {
    console.log("Login with Google");
  };

  const handleStudentSignup = () => {
    console.log("Student signup");
  };

  const handleTeacherSignup = () => {
    console.log("Teacher signup");
  };

  return (
    <div className="flex-grow flex items-center justify-center p-6 md:p-10">
      <div className="bg-white/80 backdrop-blur-sm p-8 rounded-2xl shadow-lg max-w-md w-full">
        <div className="text-center mb-8">
          <h2 className="text-3xl font-medium text-black">Welcome to</h2>
          <h1 className="text-5xl font-bold text-black mt-1">ED CONNECT AI</h1>
        </div>
        <p className="text-black mb-8 text-center">Please sign in to continue</p>

        <div className="flex border-b border-gray-300 mb-6">
          <button className={`tab px-4 py-3 w-1/2 text-center ${activeTab === 'login' ? 'tab-active' : 'text-gray-500'}`} onClick={() => setActiveTab("login")}>Sign In</button>
          <button className={`tab px-4 py-3 w-1/2 text-center ${activeTab === 'signup' ? 'tab-active' : 'text-gray-500'}`} onClick={() => setActiveTab("signup")}>Sign Up</button>
        </div>

        {activeTab === "login" ? (
          <div className="space-y-6">
            <button onClick={handleGoogleLogin} className="google-btn w-full py-3 px-4 rounded-lg font-medium flex items-center justify-center">
              <svg className="w-5 h-5 mr-3" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
              </svg>
              Log in with Google
            </button>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="grid grid-cols-1 gap-4">
              <button onClick={handleStudentSignup} className="btn-student py-4 px-4 rounded-lg text-white font-medium flex items-center justify-center">
                Student Sign Up
              </button>
              <button onClick={handleTeacherSignup} className="btn-teacher py-4 px-4 rounded-lg text-white font-medium flex items-center justify-center">
                Teacher Sign Up
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Tabs;
