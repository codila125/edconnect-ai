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
        <>
            <div>
                {isPending && <p>Loading...</p>}
                {!isPending && <div>{!session && <SignIn />}</div>}
                {error && <p>Error: {error.message}</p>}
            </div>
        </>
    );
}
