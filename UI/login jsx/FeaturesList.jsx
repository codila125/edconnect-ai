import React from "react";

const features = [
  "Empowering students with smart summaries and practice questions from their learning materials.",
  "Seamlessly connect with professors using built-in messaging.",
  "Access and organize all your course materials in one centralized, easy-to-use platform."
];

const FeaturesList = () => {
  return (
    <div className="mt-8 space-y-6 flex-grow flex flex-col justify-center">
      {features.map((text, idx) => (
        <div key={idx} className="flex items-start">
          <div className="feature-icon mr-4">
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                clipRule="evenodd"
              />
            </svg>
          </div>
          <p className="text-lg">{text}</p>
        </div>
      ))}
    </div>
  );
};

export default FeaturesList;