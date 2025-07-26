// this acts as a server route to handle user role assignment
// It checks if the user is authenticated, retrieves their current role,
// and allows them to assign a new role (either 'teacher' or 'student').
// If the user already has a role, it returns an error. If the role is invalid,
// it also returns an error. If everything is valid, it updates the user's role
// in the database and returns the new role.
import { createServerFileRoute } from "@tanstack/react-start/server";
import { auth } from "../../lib/auth/auth";
import sendRole from "../../lib/db/role";
import db from "../../lib/db/drizzle";
import * as schema from "../../lib/db/schema";
import { eq } from "drizzle-orm";
import { redirect } from "@tanstack/react-router";

export const ServerRoute = createServerFileRoute("/api/hello/$").methods({
    GET: async ({ request, params }) => {
        // Handle GET request to assign a role to the user
        // param will contain the role to be assigned, like 'teacher' or 'student' from $

        const session = await auth.api.getSession({
            // Get the session from the request
            headers: request.headers,
        });

        if (!session || !session.session.userId) {
            // Check if the session is valid and userId exists
            return new Response(JSON.stringify({ error: "Unauthorized" }), {
                status: 401,
                headers: { "Content-Type": "application/json" },
            });
        }

        const role = params._splat; // Extract the role from the request parameters

        const existingRoleResult = await db // Query the database to check if the user already has a role
            .select({ role: schema.user.role })
            .from(schema.user)
            .where(eq(schema.user.id, session.session.userId))
            .limit(1);

        const existingRole = existingRoleResult[0]?.role; // Get the existing role from the query result

        if (existingRole === role) {
            throw redirect({
                to: `/dashboard`, // If the user already has the requested role, redirect to the dashboard
            });
        }

        if (existingRole === "teacher" || existingRole === "student") {
            return new Response(
                JSON.stringify({
                    error: `User already has the role ${existingRole}`, // If the user already has a role,
                    // return an error
                }),
                {
                    status: 400,
                    headers: { "Content-Type": "application/json" },
                }
            );
        }

        if (role !== "teacher" && role !== "student") {
            // Validate the role to be assigned
            return new Response(JSON.stringify({ error: "Invalid role" }), {
                status: 400,
                headers: { "Content-Type": "application/json" },
            });
        }

        await sendRole({ role, userId: session.session.userId }); // Call the sendRole function to
        // update the user's role in the database
        // wait for the role to be updated

        redirect({
            to: `/dashboard`, // Redirect to the dashboard after assigning the role
        });
    },
});

// Mostly the return is in JSON format, but you can also return HTML or other formats
// based on the requirements of your application.
