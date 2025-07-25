import { auth } from "@/lib/auth/auth";
import addClass from "@/lib/db/addclass";
import { createServerFileRoute } from "@tanstack/react-start/server";
import { redirect } from "@tanstack/react-router";

export const ServerRoute = createServerFileRoute("/api/addclasses").methods({
    POST: async ({ request }) => {
        const formData = await request.formData();
        const name = formData.get("name") as string;
        const description = formData.get("description") as string;
        const activeStart = formData.get("activestart") as string;
        const activeEnd = formData.get("activeend") as string;

        const session = await auth.api.getSession({
            // Get the session from the request
            headers: request.headers,
        });

        if (session) {
            await addClass({
                name: name,
                description: description,
                activestart: activeStart,
                activeend: activeEnd,
                teacherId: session?.session.userId, // Replace with actual teacher ID logic
            });
        }

        if (!name || !description || !activeStart || !activeEnd) {
            return new Response(
                JSON.stringify({
                    error: "Name, description, and active hours are required",
                }),
                {
                    status: 400,
                    headers: { "Content-Type": "application/json" },
                }
            );
        }

        throw redirect({
            to: "/dashboard", // Redirect to the dashboard after adding the class
        });
    },
});
