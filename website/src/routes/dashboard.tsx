import { createFileRoute, redirect, useNavigate } from "@tanstack/react-router";
import { createServerFn } from "@tanstack/react-start";
import { auth } from "../lib/auth/auth";
import { getWebRequest } from "@tanstack/react-start/server";
import { authClient } from "../lib/auth/auth-client";
import db from "../lib/db/drizzle";
import * as schema from "../lib/db/auth-schema";
import { eq } from "drizzle-orm";

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

    return { session: session.session, role: existingRoleResult[0]?.role };
});

export const Route = createFileRoute("/dashboard")({
    beforeLoad: async () => await authStateFn(),
    loader: async () => await authStateFn(),
    component: RouteComponent,
});

function RouteComponent() {
    const { data: session } = authClient.useSession();
    const { role: role } = Route.useLoaderData();
    const navigate = useNavigate();

    return (
        <>
            <div>Hello "/dashboard"!</div>
            <div>
                <p>Role: {role}</p>
            </div>
            <div>
                {session && (
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
                )}
            </div>
        </>
    );
}
