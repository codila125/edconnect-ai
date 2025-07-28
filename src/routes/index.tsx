// This file is the main entry point for the application.
// It sets up the home route and handles user authentication.
import { createFileRoute, redirect } from "@tanstack/react-router";
import { authClient } from "../lib/auth/auth-client";
import SignIn from "../components/sign-in";
import { createServerFn } from "@tanstack/react-start";
import { getWebRequest } from "@tanstack/react-start/server";
import { auth } from "../lib/auth/auth";

const authStateFn = createServerFn({
    method: "GET", // HTTP method to use
    response: "data", // Response handling mode
}).handler(async () => {
    const request = getWebRequest();
    if (!request) {
        throw new Error("Unauthorized");
    }
    const session = await auth.api.getSession(request);
    if (session) {
        throw redirect({
            to: "/dashboard",
        });
    }
    return { session: session };
});

export const Route = createFileRoute("/")({
    beforeLoad: async () => {
        await authStateFn();
    },
    component: Home,
});

function Home() {
    const { data: session, isPending, error } = authClient.useSession();

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center p-4">
            {/* Loading State */}
            {isPending && (
                <div className="text-center">
                    <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/20 p-12 max-w-md">
                        {/* Loading Spinner */}
                        <div className="flex justify-center mb-6">
                            <div className="relative">
                                <div className="w-12 h-12 border-4 border-slate-200 rounded-full"></div>
                                <div className="absolute top-0 left-0 w-12 h-12 border-4 border-blue-600 rounded-full animate-spin border-t-transparent"></div>
                            </div>
                        </div>

                        {/* Loading Text */}
                        <h2 className="text-xl font-light text-slate-800 mb-2">
                            Loading
                        </h2>
                        <p className="text-slate-500 text-sm">
                            Checking your authentication status...
                        </p>

                        {/* Loading Animation Dots */}
                        <div className="flex justify-center space-x-1 mt-4">
                            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                            <div
                                className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"
                                style={{ animationDelay: "0.2s" }}
                            ></div>
                            <div
                                className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"
                                style={{ animationDelay: "0.4s" }}
                            ></div>
                        </div>
                    </div>
                </div>
            )}

            {/* Sign In Component */}
            {!isPending && !session && <SignIn />}

            {/* Error State */}
            {error && (
                <div className="text-center max-w-md">
                    <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-red-200/50 p-8">
                        {/* Error Icon */}
                        <div className="flex justify-center mb-6">
                            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center">
                                <svg
                                    className="w-8 h-8 text-red-600"
                                    viewBox="0 0 24 24"
                                    fill="currentColor"
                                >
                                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
                                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zM13 17h-2v-2h2v2zm0-4h-2V7h2v6z" />
                                </svg>
                            </div>
                        </div>

                        {/* Error Content */}
                        <h2 className="text-xl font-semibold text-red-800 mb-3">
                            Authentication Error
                        </h2>
                        <p className="text-red-600 text-sm mb-6 leading-relaxed">
                            {error.message}
                        </p>

                        {/* Retry Button */}
                        <button
                            onClick={() => window.location.reload()}
                            className="group relative overflow-hidden bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 text-white py-3 px-6 rounded-xl font-medium transition-all duration-300 ease-out transform hover:scale-[1.02] hover:shadow-lg active:scale-[0.98]"
                        >
                            <div className="absolute inset-0 bg-white/10 transform translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700 ease-out"></div>
                            <div className="relative flex items-center justify-center space-x-2">
                                <svg
                                    className="w-4 h-4"
                                    viewBox="0 0 24 24"
                                    fill="currentColor"
                                >
                                    <path d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z" />
                                </svg>
                                <span>Try Again</span>
                            </div>
                        </button>
                    </div>
                </div>
            )}

            {/* Decorative Elements */}
            <div className="fixed top-10 left-10 w-20 h-20 bg-blue-200/30 rounded-full blur-xl pointer-events-none"></div>
            <div className="fixed bottom-10 right-10 w-32 h-32 bg-emerald-200/30 rounded-full blur-xl pointer-events-none"></div>
        </div>
    );
}
