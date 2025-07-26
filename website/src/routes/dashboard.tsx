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
        return <div>Loading...</div>;
    }

    const { role, classes } = loaderData;

    // Normalize classes for students (extract .classes property)
    const normalizedClasses =
        role === "student"
            ? classes.map((item: any) => item.classes)
            : classes;

    return (
        <>
            <div>Hello "/dashboard"!</div>
            <div>
                <p>Role: {role}</p>
            </div>
            <div>
                {session && (
                    <>
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
                        >
                            Sign Out
                        </button>
                        {role === "teacher" && (
                            <div>
                                <AddClass />
                            </div>
                        )}
                        {role === "student" && (
                            <div>
                                <JoinClass />
                            </div>
                        )}
                        <div>
                            <Classes classes={normalizedClasses} />
                        </div>
                    </>
                )}
            </div>
        </>
    );
}
