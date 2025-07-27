import { authClient } from "../lib/auth/auth-client";

export default function SignIn() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Main Card */}
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/20 p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-light text-slate-800 mb-2">EdConnect AI</h1>
            <p className="text-slate-500 text-sm">Choose your account type to continue</p>
          </div>

          {/* Buttons Container */}
          <div className="space-y-4">
            {/* Teacher Button */}
            <button
              onClick={() =>
                authClient.signIn.social({
                  provider: "google",
                  errorCallbackURL: "/error",
                  callbackURL: "/dashboard",
                  newUserCallbackURL: "/api/hello/teacher",
                  disableRedirect: false,
                })
              }
              className="w-full group relative overflow-hidden bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white py-4 px-6 rounded-xl font-medium transition-all duration-300 ease-out transform hover:scale-[1.02] hover:shadow-lg active:scale-[0.98]"
            >
              <div className="absolute inset-0 bg-white/10 transform translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700 ease-out"></div>
              <div className="relative flex items-center justify-center space-x-3">
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2C13.1 2 14 2.9 14 4C14 5.1 13.1 6 12 6C10.9 6 10 5.1 10 4C10 2.9 10.9 2 12 2ZM21 9V7L15 4V6C15 7.1 14.1 8 13 8V22H11V16H9V22H7V8C5.9 8 5 7.1 5 6V4L3 7V9H1V7C1 6.45 1.22 5.95 1.59 5.59L6.59 0.59C6.95 0.22 7.45 0 8 0H16C16.55 0 17.05 0.22 17.41 0.59L22.41 5.59C22.78 5.95 23 6.45 23 7V9H21Z"/>
                </svg>
                <span>Sign in as Teacher</span>
              </div>
            </button>

            {/* Student Button */}
            <button
              onClick={() =>
                authClient.signIn.social({
                  provider: "google",
                  errorCallbackURL: "/error",
                  callbackURL: "/dashboard",
                  newUserCallbackURL: "/api/hello/student",
                  disableRedirect: false,
                })
              }
              className="w-full group relative overflow-hidden bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-700 hover:to-emerald-800 text-white py-4 px-6 rounded-xl font-medium transition-all duration-300 ease-out transform hover:scale-[1.02] hover:shadow-lg active:scale-[0.98]"
            >
              <div className="absolute inset-0 bg-white/10 transform translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700 ease-out"></div>
              <div className="relative flex items-center justify-center space-x-3">
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 3L1 9L5 11.18V17.18L12 21L19 17.18V11.18L21 10.09V17H23V9L12 3ZM18.82 9L12 12.72L5.18 9L12 5.28L18.82 9ZM17 16L12 18.72L7 16V12.27L12 15L17 12.27V16Z"/>
                </svg>
                <span>Sign in as Student</span>
              </div>
            </button>
          </div>

          {/* Footer */}
          <div className="mt-8 pt-6 border-t border-slate-200">
            <div className="flex items-center justify-center space-x-2 text-slate-500 text-xs">
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12.017 11.215c-.3-.5-.8-.7-1.4-.7s-1.1.2-1.4.7c-.1.2-.2.4-.2.6v.9c-.3-.1-.6-.1-.9-.1-1.8 0-3.2 1.4-3.2 3.2s1.4 3.2 3.2 3.2c1.8 0 3.2-1.4 3.2-3.2 0-.6-.2-1.1-.5-1.6v-.9c0-.2.1-.4.2-.6.3-.5.8-.7 1.4-.7s1.1.2 1.4.7c.1.2.2.4.2.6v.9c-.3.1-.6.1-.9.1-1.8 0-3.2 1.4-3.2 3.2s1.4 3.2 3.2 3.2c1.8 0 3.2-1.4 3.2-3.2 0-.6-.2-1.1-.5-1.6v-.9c0-.2-.1-.4-.2-.6zm-3.4 7.4c-.6 0-1.1-.5-1.1-1.1s.5-1.1 1.1-1.1 1.1.5 1.1 1.1-.5 1.1-1.1 1.1zm6.8 0c-.6 0-1.1-.5-1.1-1.1s.5-1.1 1.1-1.1 1.1.5 1.1 1.1-.5 1.1-1.1 1.1zm3.6-13.4c0-1.1-.9-2-2-2h-13c-1.1 0-2 .9-2 2v8c0 1.1.9 2 2 2h13c1.1 0 2-.9 2-2v-8z"/>
              </svg>
              <span>Powered by Google Authentication</span>
            </div>
          </div>
        </div>

        {/* Decorative Elements */}
        <div className="absolute top-10 left-10 w-20 h-20 bg-blue-200/30 rounded-full blur-xl"></div>
        <div className="absolute bottom-10 right-10 w-32 h-32 bg-emerald-200/30 rounded-full blur-xl"></div>
      </div>
    </div>
  );
}