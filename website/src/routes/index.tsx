// This file is the main entry point for the application.
// It sets up the home route and handles user authentication.

import { createFileRoute } from "@tanstack/react-router";
import { authClient } from "../lib/auth/auth-client";
import SignIn from "../components/sign-in";

export const Route = createFileRoute("/")({
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
                {session && ( // Render user information if session exists
                    <div>
                        <button onClick={() => authClient.signOut({})}>
                            Sign out
                        </button>
                        <h2>Welcome, {session.user.name}!</h2>
                    </div>
                )}
            </div>
        </>
    );
}
