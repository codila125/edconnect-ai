/// <reference types="vite/client" />
import type { ReactNode } from "react";
import {
    Outlet,
    createRootRoute,
    HeadContent,
    Scripts,
} from "@tanstack/react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const queryClient = new QueryClient();

export const Route = createRootRoute({
    head: () => ({
        meta: [
            {
                charSet: "utf-8",
            },
            {
                name: "viewport",
                content: "width=device-width, initial-scale=1",
            },
            {
                title: "ED-Connect AI",
            },
        ],
    }),
    component: RootComponent,
    notFoundComponent: () => <div>Not Found</div>,
    errorComponent: () => <div>Error occurred</div>,
});

function RootComponent() {
    return (
        <RootDocument>
            <QueryClientProvider client={queryClient}>
                <Outlet />
            </QueryClientProvider>
        </RootDocument>
    );
}

function RootDocument({ children }: Readonly<{ children: ReactNode }>) {
    return (
        <html>
            <head>
                <HeadContent />
            </head>
            <body>
                {children}
                <Scripts />
            </body>
        </html>
    );
}
