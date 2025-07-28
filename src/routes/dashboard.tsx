import { createFileRoute, redirect, useNavigate } from "@tanstack/react-router";
import { createServerFn } from "@tanstack/react-start";
import { auth } from "../lib/auth/auth";
import { getWebRequest } from "@tanstack/react-start/server";
import { authClient } from "../lib/auth/auth-client";
import db from "../lib/db/drizzle";
import * as schema from "../lib/db/schema";
import { eq } from "drizzle-orm";
import AddClass from "@/components/add-class";
import Classes from "@/components/show-class";
import JoinClass from "@/components/join-class";

const authStateFn = createServerFn({
    method: "GET", // HTTP method to use
    response: "data", // Response handling mode
}).handler(async () => {
    const request = getWebRequest();
    if (!request) {
        throw new Error("Unauthorized");
    }

    const session = await auth.api.getSession(request);

    if (!session) {
        throw redirect({
            to: "/",
        });
    }

    const existingRoleResult = await db // Query the database to check if the user already has a role
        .select({ role: schema.user.role })
        .from(schema.user)
        .where(eq(schema.user.id, session.session.userId))
        .limit(1);

    if (existingRoleResult[0]?.role === "teacher") {
        const classes = await db // Fetch classes from the database
            .select() // Select all columns
            .from(schema.classes)
            .where(eq(schema.classes.teacherId, session.session.userId));

        return {
            role: existingRoleResult[0]?.role,
            classes: classes,
        };
    } else if (existingRoleResult[0]?.role === "student") {
        const stdclasses = await db // Fetch classes for students
            .select() // Select all columns
            .from(schema.classes)
            .innerJoin(
                schema.enrollments,
                eq(schema.classes.id, schema.enrollments.classId)
            )
            .where(eq(schema.enrollments.studentId, session.session.userId));

        return {
            role: existingRoleResult[0]?.role,
            classes: stdclasses,
        };
    }
});

export const Route = createFileRoute("/dashboard")({
    // beforeLoad: async () => await authStateFn(),
    loader: async () => {
        const authData = await authStateFn();
        return authData;
    },
    component: RouteComponent,
});

function RouteComponent() {
    const { data: session } = authClient.useSession();
    const loaderData = Route.useLoaderData();
    const navigate = useNavigate();

    if (!loaderData) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center p-4">
                <div className="text-center">
                    <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/20 p-12 max-w-md">
                        {/* Loading Spinner */}
                        <div className="flex justify-center mb-6">
                            <div className="relative">
                                <div className="w-12 h-12 border-4 border-slate-200 rounded-full"></div>
                                <div className="absolute top-0 left-0 w-12 h-12 border-4 border-blue-600 rounded-full animate-spin border-t-transparent"></div>
                            </div>
                        </div>

                        <h2 className="text-xl font-light text-slate-800 mb-2">
                            Loading
                        </h2>
                        <p className="text-slate-500 text-sm">
                            Preparing your dashboard...
                        </p>
                    </div>
                </div>
            </div>
        );
    }

    const { role, classes } = loaderData;

    // Normalize classes for students (extract .classes property)
    const normalizedClasses =
        role === "student" ? classes.map((item: any) => item.classes) : classes;

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
            {session && (
                <>
                    {/* Header */}
                    <div className="bg-white/70 backdrop-blur-sm border-b border-white/20 sticky top-0 z-10">
                        <div className="max-w-7xl mx-auto px-6 py-4">
                            <div className="flex items-center justify-between">
                                {/* Welcome Section */}
                                <div>
                                    <h1 className="text-2xl font-light text-slate-800">
                                        Welcome back
                                    </h1>
                                    <p className="text-slate-500 text-sm capitalize">
                                        {role} Dashboard
                                    </p>
                                </div>

                                {/* Sign Out Button */}
                                <button
                                    onClick={async () => {
                                        await authClient.signOut({
                                            fetchOptions: {
                                                onSuccess: () => {
                                                    navigate({ to: "/" });
                                                },
                                            },
                                        });
                                    }}
                                    className="group relative overflow-hidden bg-gradient-to-r from-slate-600 to-slate-700 hover:from-slate-700 hover:to-slate-800 text-white py-2 px-4 rounded-xl font-medium transition-all duration-300 ease-out transform hover:scale-[1.02] hover:shadow-lg active:scale-[0.98]"
                                >
                                    <div className="absolute inset-0 bg-white/10 transform translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700 ease-out"></div>
                                    <div className="relative flex items-center space-x-2">
                                        <svg
                                            className="w-4 h-4"
                                            viewBox="0 0 24 24"
                                            fill="currentColor"
                                        >
                                            <path d="M17 7l-1.41 1.41L18.17 11H8v2h10.17l-2.58 2.59L17 17l5-5zM4 5h8V3H4c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h8v-2H4V5z" />
                                        </svg>
                                        <span>Sign Out</span>
                                    </div>
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* Main Content */}
                    <div className="max-w-7xl mx-auto px-6 py-8">
                        {/* Action Section */}
                        <div className="mb-12">
                            {role === "teacher" && (
                                <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border border-white/20 p-8">
                                    <div className="flex items-center mb-6">
                                        <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-blue-600 rounded-xl flex items-center justify-center mr-4">
                                            <svg
                                                className="w-6 h-6 text-white"
                                                viewBox="0 0 24 24"
                                                fill="currentColor"
                                            >
                                                <path d="M12 2C13.1 2 14 2.9 14 4C14 5.1 13.1 6 12 6C10.9 6 10 5.1 10 4C10 2.9 10.9 2 12 2ZM21 9V7L15 4V6C15 7.1 14.1 8 13 8V22H11V16H9V22H7V8C5.9 8 5 7.1 5 6V4L3 7V9H1V7C1 6.45 1.22 5.95 1.59 5.59L6.59 0.59C6.95 0.22 7.45 0 8 0H16C16.55 0 17.05 0.22 17.41 0.59L22.41 5.59C22.78 5.95 23 6.45 23 7V9H21Z" />
                                            </svg>
                                        </div>
                                        <div>
                                            <h2 className="text-xl font-semibold text-slate-800">
                                                Teacher Tools
                                            </h2>
                                            <p className="text-slate-500 text-sm">
                                                Create and manage your classes
                                            </p>
                                        </div>
                                    </div>
                                    <AddClass />
                                </div>
                            )}

                            {role === "student" && (
                                <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border border-white/20 p-8">
                                    <div className="flex items-center mb-6">
                                        <div className="w-12 h-12 bg-gradient-to-r from-emerald-500 to-emerald-600 rounded-xl flex items-center justify-center mr-4">
                                            <svg
                                                className="w-6 h-6 text-white"
                                                viewBox="0 0 24 24"
                                                fill="currentColor"
                                            >
                                                <path d="M12 3L1 9L5 11.18V17.18L12 21L19 17.18V11.18L21 10.09V17H23V9L12 3ZM18.82 9L12 12.72L5.18 9L12 5.28L18.82 9ZM17 16L12 18.72L7 16V12.27L12 15L17 12.27V16Z" />
                                            </svg>
                                        </div>
                                        <div>
                                            <h2 className="text-xl font-semibold text-slate-800">
                                                Student Hub
                                            </h2>
                                            <p className="text-slate-500 text-sm">
                                                Join new classes and access your
                                                courses
                                            </p>
                                        </div>
                                    </div>
                                    <JoinClass />
                                </div>
                            )}
                        </div>

                        {/* Classes Section */}
                        <div>
                            <Classes classes={normalizedClasses} />
                        </div>
                    </div>

                    {/* Decorative Elements */}
                    <div className="fixed top-10 left-10 w-20 h-20 bg-blue-200/30 rounded-full blur-xl pointer-events-none"></div>
                    <div className="fixed bottom-10 right-10 w-32 h-32 bg-emerald-200/30 rounded-full blur-xl pointer-events-none"></div>
                </>
            )}
        </div>
    );
}
