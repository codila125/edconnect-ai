import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/")({
    component: Home,
});

function Home() {
    return (
        <>
            <div>
                <h1>Welcome to the Masterminds Hackathon!</h1>
                <p>
                    This is a simple React application demonstrating routing and
                    server functions.
                </p>
                <p>Check the console for server function output.</p>
            </div>
        </>
    );
}
