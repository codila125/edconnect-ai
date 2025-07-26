import { useNavigate } from "@tanstack/react-router";
import type { classes } from "../lib/db/interface";

const Classes = ({ classes }: { classes: classes[] }) => {
  const navigate = useNavigate();
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-10">
          <h1 className="text-4xl font-light text-slate-800 mb-3">Your Classes</h1>
          <p className="text-slate-500">Select a class to view its contents</p>
        </div>

        {/* Classes Grid */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {classes.map((cls) => (
            <div key={cls.id} className="group">
              <button
                onClick={() => {
                  navigate({ to: `/contents/${cls.id}` });
                }}
                className="w-full text-left bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border border-white/20 p-6 transition-all duration-300 ease-out transform hover:scale-[1.02] hover:shadow-xl hover:bg-white/90 active:scale-[0.98]"
              >
                {/* Class Header */}
                <div className="mb-4">
                  <h2 className="text-xl font-semibold text-slate-800 mb-2 group-hover:text-blue-700 transition-colors duration-300">
                    {cls.className}
                  </h2>
                  <div className="w-12 h-1 bg-gradient-to-r from-blue-500 to-emerald-500 rounded-full transform scale-x-0 group-hover:scale-x-100 transition-transform duration-300 origin-left"></div>
                </div>

                {/* Description */}
                <p className="text-slate-600 mb-4 line-clamp-3 leading-relaxed">
                  {cls.description}
                </p>

                {/* Active Hours */}
                <div className="flex items-center space-x-2 text-sm text-slate-500">
                  <svg className="w-4 h-4 flex-shrink-0" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2zm0 18c-4.4 0-8-3.6-8-8s3.6-8 8-8 8 3.6 8 8-3.6 8-8 8zm.5-13H11v6l5.2 3.2.8-1.3-4.5-2.7V7z"/>
                  </svg>
                  <span>
                    Active from <span className="font-medium text-slate-700">{cls.activeStart}</span> to <span className="font-medium text-slate-700">{cls.activeEnd}</span>
                  </span>
                </div>

                {/* Hover Arrow */}
                <div className="flex items-center justify-end mt-4 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                  <div className="flex items-center space-x-2 text-blue-600">
                    <span className="text-sm font-medium">View Contents</span>
                    <svg className="w-4 h-4 transform group-hover:translate-x-1 transition-transform duration-300" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
                    </svg>
                  </div>
                </div>
              </button>
            </div>
          ))}
        </div>

        {/* Empty State */}
        {classes.length === 0 && (
          <div className="text-center py-16">
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border border-white/20 p-12 max-w-md mx-auto">
              <svg className="w-16 h-16 text-slate-400 mx-auto mb-4" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
              </svg>
              <h3 className="text-xl font-light text-slate-800 mb-2">No Classes Yet</h3>
              <p className="text-slate-500">Create your first class to get started</p>
            </div>
          </div>
        )}

        {/* Decorative Elements */}
        <div className="fixed top-10 left-10 w-20 h-20 bg-blue-200/30 rounded-full blur-xl pointer-events-none"></div>
        <div className="fixed bottom-10 right-10 w-32 h-32 bg-emerald-200/30 rounded-full blur-xl pointer-events-none"></div>
      </div>
    </div>
  );
};

export default Classes;