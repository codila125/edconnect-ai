import { auth } from "@/lib/auth/auth";
import joinClass from "@/lib/db/joinclass";
import { createServerFileRoute } from "@tanstack/react-start/server";
import { redirect } from "@tanstack/react-router";
import db from "@/lib/db/drizzle";
import * as schema from "@/lib/db/schema";
import { eq } from "drizzle-orm";

export const ServerRoute = createServerFileRoute("/api/joinclass").methods({
    POST: async ({ request }) => {
        const formData = await request.formData();
        const code = formData.get("code") as string;

        const classID = await db.select().from(schema.classes).where(eq(schema.classes.classCode, code));

        const session = await auth.api.getSession({
            // Get the session from the request
            headers: request.headers,
        });

        if (session) {
            await joinClass({
                classId: classID[0]?.id, // Assuming classID is an array and we take the first element
                userId: session?.session.userId, // Replace with actual user ID logic
            });
        }

        if (!code) {
            return new Response(
                JSON.stringify({
                    error: "Class code is required",
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

