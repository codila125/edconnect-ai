import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import AddContent from "@/components/add-content";
import ChatModule from "@/components/chat";
import { createServerFn } from "@tanstack/react-start";
import { getWebRequest } from "@tanstack/react-start/server";
import { auth } from "@/lib/auth/auth";
import db from "@/lib/db/drizzle";
import * as schema from "@/lib/db/schema";
import { eq } from "drizzle-orm";

interface Content {
    id: string;
    title: string;
    body: string;
    classId: string;
    summary: string;
}

interface ApiResponse {
    contents: Content[];
    classId: string;
    error?: string;
}

const authStateFn = createServerFn({
    method: "GET",
    response: "data",
}).handler(async () => {
    const request = getWebRequest();
    if (!request) {
        throw new Error("Unauthorized");
    }

    const session = await auth.api.getSession(request);

    if (!session) {
        throw new Error("Unauthorized");
    }

    // Get classId from the URL params
    const url = new URL(request.url);
    const pathParts = url.pathname.split("/");
    const classId = pathParts[pathParts.length - 1];

    const userId = await db
        .select({ id: schema.session.userId })
        .from(schema.session)
        .where(eq(schema.session.userId, session?.user.id))
        .execute();

    if (!userId || userId.length === 0) {
        throw new Error("User not found");
    }

    const userIdValue = userId[0]?.id;

    // Check if user is enrolled in this class
    const classEnrollment = await db
        .select({ id: schema.enrollments.classId })
        .from(schema.enrollments)
        .where(eq(schema.enrollments.studentId, userIdValue))
        .execute();

    // If not enrolled, check if user is the teacher of this class
    if (
        !classEnrollment ||
        classEnrollment.length === 0 ||
        !classEnrollment.some((e) => e.id === classId)
    ) {
        const teacherClass = await db
            .select({ id: schema.classes.id })
            .from(schema.classes)
            .where(eq(schema.classes.teacherId, userIdValue))
            .execute();

        if (
            !teacherClass ||
            teacherClass.length === 0 ||
            !teacherClass.some((c) => c.id === classId)
        ) {
            return { session: session, urls: [] };
        }
    }

    // Get all contents for the specific class
    const contentsData = await db
        .select({
            materialId: schema.contents.materialId,
        })
        .from(schema.contents)
        .where(eq(schema.contents.classId, classId))
        .execute();

    if (!contentsData || contentsData.length === 0) {
        return { session: session, urls: [] };
    }

    // Get all material URLs for the contents
    const materialIds = contentsData.map((content) => content.materialId);
    const urls = await db
        .select({
            url: schema.materials.url,
            name: schema.materials.name,
            id: schema.materials.id,
        })
        .from(schema.materials)
        .where(eq(schema.materials.id, materialIds[0])) // You might want to use `in` operator for multiple IDs
        .execute();

    return { session: session, urls: urls };
});

export const Route = createFileRoute("/contents/$classId")({
    loader: async () => {
        const result = await authStateFn();
        if (!result) {
            return { session: undefined, urls: [] };
        }
        const { session, urls } = result;

        return { session, urls };
    },
    component: RouteComponent,
});

function RouteComponent() {
    const params = Route.useParams();
    const { session, urls } = Route.useLoaderData();
    const [contents, setContents] = useState<Content[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const [currentUserId, setCurrentUserId] = useState(session?.user.id || "");

    useEffect(() => {
        if (typeof window !== "undefined") {
            const storedUserId =
                sessionStorage.getItem("userId") ||
                localStorage.getItem("userId");
            if (storedUserId) {
                setCurrentUserId(storedUserId);
            } else {
                const newUserId = `user_${Date.now()}`;
                sessionStorage.setItem("userId", newUserId);
                setCurrentUserId(newUserId);
            }
        }
    }, []);

    useEffect(() => {
        const fetchContents = async () => {
            if (!params.classId) {
                setError("No class ID provided");
                setLoading(false);
                return;
            }

            try {
                setLoading(true);
                setError(null);
                const response = await fetch(`/api/contents/${params.classId}`);
                const data: ApiResponse = await response.json();

                if (!response.ok) {
                    throw new Error(data.error || "Failed to fetch contents");
                }

                setContents(data.contents);
            } catch (err) {
                console.error("Fetch error:", err);
                setError(
                    err instanceof Error ? err.message : "An error occurred"
                );
            } finally {
                setLoading(false);
            }
        };

        fetchContents();
    }, [params.classId]);

    if (loading) {
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
                            Loading Contents
                        </h2>
                        <p className="text-slate-500 text-sm">
                            Fetching contents for class {params.classId}
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
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center p-4">
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
                                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zM13 17h-2v-2h2v2zm0-4h-2V7h2v6z" />
                                </svg>
                            </div>
                        </div>

                        <h2 className="text-xl font-semibold text-red-800 mb-3">
                            Error Loading Contents
                        </h2>
                        <p className="text-red-600 text-sm mb-6 leading-relaxed">
                            {error}
                        </p>

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
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
            <div className="max-w-6xl mx-auto p-6">
                {/* Header */}
                <div className="text-center mb-10">
                    <h1 className="text-4xl font-light text-slate-800 mb-3">
                        Class Contents
                    </h1>
                </div>

                {/* Contents Section */}
                <div className="mb-12">
                    {contents.length > 0 ? (
                        <div className="space-y-8">
                            {contents.map((content) => (
                                <div
                                    key={content.id}
                                    className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border border-white/20 overflow-hidden"
                                >
                                    {/* Content Header */}
                                    <div className="bg-gradient-to-r from-blue-50 to-emerald-50 p-6 border-b border-white/20">
                                        <h3 className="text-2xl font-semibold text-slate-800 mb-2">
                                            {content.title}
                                        </h3>
                                    </div>

                                    {/* Content Body */}
                                    <div className="p-6">
                                        <div className="prose prose-slate max-w-none mb-6">
                                            <p className="text-slate-700 leading-relaxed">
                                                {content.body}
                                            </p>
                                        </div>

                                        {/* Materials Section */}
                                        {urls && urls.length > 0 && (
                                            <div className="border-t border-slate-200 pt-6">
                                                <h4 className="text-lg font-semibold text-slate-800 mb-4 flex items-center">
                                                    <svg
                                                        className="w-5 h-5 mr-2 text-blue-600"
                                                        viewBox="0 0 24 24"
                                                        fill="currentColor"
                                                    >
                                                        <path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm4 18H6V4h7v5h5v11z" />
                                                    </svg>
                                                    Class Materials
                                                </h4>
                                                <div className="space-y-3 mb-6">
                                                    {urls.map(
                                                        (material, index) => (
                                                            <div
                                                                key={
                                                                    material.id ||
                                                                    index
                                                                }
                                                                className="bg-slate-50 rounded-xl p-4 border border-slate-200"
                                                            >
                                                                <p className="font-medium text-slate-800 mb-2">
                                                                    {
                                                                        material.name
                                                                    }
                                                                </p>
                                                                <a
                                                                    href={
                                                                        material.url
                                                                    }
                                                                    target="_blank"
                                                                    rel="noopener noreferrer"
                                                                    className="inline-flex items-center text-blue-600 hover:text-blue-800 transition-colors duration-200"
                                                                >
                                                                    <svg
                                                                        className="w-4 h-4 mr-2"
                                                                        viewBox="0 0 24 24"
                                                                        fill="currentColor"
                                                                    >
                                                                        <path d="M19 19H5V5h7V3H5c-1.11 0-2 .9-2 2v14c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2v-7h-2v7zM14 3v2h3.59l-9.83 9.83 1.41 1.41L19 6.41V10h2V3h-7z" />
                                                                    </svg>
                                                                    Open
                                                                    Material
                                                                </a>
                                                            </div>
                                                        )
                                                    )}
                                                </div>

                                                {/* Summary Section */}
                                                <div className="bg-gradient-to-r from-emerald-50 to-blue-50 rounded-xl p-6">
                                                    <h4 className="text-lg font-semibold text-slate-800 mb-3 flex items-center">
                                                        <svg
                                                            className="w-5 h-5 mr-2 text-emerald-600"
                                                            viewBox="0 0 24 24"
                                                            fill="currentColor"
                                                        >
                                                            <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                                        </svg>
                                                        Summary
                                                    </h4>
                                                    <p className="text-slate-700 leading-relaxed">
                                                        {content.summary}
                                                    </p>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-16">
                            <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border border-white/20 p-12 max-w-md mx-auto">
                                <svg
                                    className="w-16 h-16 text-slate-400 mx-auto mb-4"
                                    viewBox="0 0 24 24"
                                    fill="currentColor"
                                >
                                    <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z" />
                                </svg>
                                <h3 className="text-xl font-light text-slate-800 mb-2">
                                    No Contents Available
                                </h3>
                                <p className="text-slate-500">
                                    No contents found for this class yet.
                                </p>
                            </div>
                        </div>
                    )}
                </div>

                {/* Teacher Actions */}
                {session?.user.role === "teacher" && (
                    <div className="mb-12">
                        <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border border-white/20 p-8">
                            <div className="flex items-center mb-6">
                                <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-blue-600 rounded-xl flex items-center justify-center mr-4">
                                    <svg
                                        className="w-6 h-6 text-white"
                                        viewBox="0 0 24 24"
                                        fill="currentColor"
                                    >
                                        <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" />
                                    </svg>
                                </div>
                                <div>
                                    <h2 className="text-xl font-semibold text-slate-800">
                                        Add New Content
                                    </h2>
                                    <p className="text-slate-500 text-sm">
                                        Create new content for your students
                                    </p>
                                </div>
                            </div>
                            <AddContent classId={params.classId} />
                        </div>
                    </div>
                )}

                {/* Chat Section */}
                <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border border-white/20 overflow-hidden">
                    <div className="bg-gradient-to-r from-emerald-50 to-blue-50 p-6 border-b border-white/20">
                        <h2 className="text-xl font-semibold text-slate-800 flex items-center">
                            <svg
                                className="w-6 h-6 mr-3 text-emerald-600"
                                viewBox="0 0 24 24"
                                fill="currentColor"
                            >
                                <path d="M20 2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h4v3c0 .6.4 1 1 1 .2 0 .5-.1.7-.3L16.4 18H20c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z" />
                            </svg>
                            Class Chat
                        </h2>
                    </div>
                    <div className="p-6">
                        <ChatModule
                            classId={params.classId}
                            currentUserId={currentUserId}
                            currentUserName={session?.user.name || "Your Name"}
                        />
                    </div>
                </div>

                {/* Decorative Elements */}
                <div className="fixed top-10 left-10 w-20 h-20 bg-blue-200/30 rounded-full blur-xl pointer-events-none"></div>
                <div className="fixed bottom-10 right-10 w-32 h-32 bg-emerald-200/30 rounded-full blur-xl pointer-events-none"></div>
            </div>
        </div>
    );
}
