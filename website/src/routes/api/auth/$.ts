// This file is default from Better-auth. Do not edit it manually.
// It is used to handle authentication routes in a server-side context.

import { auth } from "../../../lib/auth/auth";
import { createServerFileRoute } from "@tanstack/react-start/server";

export const ServerRoute = createServerFileRoute("/api/auth/$").methods({
    GET: ({ request }) => {
        return auth.handler(request);
    },
    POST: ({ request }) => {
        return auth.handler(request);
    },
});
