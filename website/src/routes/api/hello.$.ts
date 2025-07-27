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
            return new Response(
                `<html>
    <head>
      <title>Unauthorized</title>
      <style>
        body { font-family: sans-serif; background: #f8fafc; color: #1e293b; display: flex; align-items: center; justify-content: center; height: 100vh; }
        .error-box { background: #fff; border-radius: 1rem; box-shadow: 0 2px 8px #0001; padding: 2rem 3rem; text-align: center; }
        .error-title { color: #dc2626; font-size: 1.5rem; margin-bottom: 1rem; }
        .error-msg { color: #334155; font-size: 1.1rem; }
        a { display: inline-block; margin-top: 1.5rem; color: #2563eb; text-decoration: underline; }
      </style>
    </head>
    <body>
      <div class="error-box">
        <div class="error-title">Unauthorized</div>
        <div class="error-msg">You are not authorized to access this page.</div>
        <a href="/">Go to Home</a>
      </div>
    </body>
  </html>`,
                {
                    status: 401,
                    headers: { "Content-Type": "text/html" },
                }
            );
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
                `<html>
    <head>
      <title>Role Assignment Error</title>
      <style>
        body { font-family: sans-serif; background: #f8fafc; color: #1e293b; display: flex; align-items: center; justify-content: center; height: 100vh; }
        .error-box { background: #fff; border-radius: 1rem; box-shadow: 0 2px 8px #0001; padding: 2rem 3rem; text-align: center; }
        .error-title { color: #dc2626; font-size: 1.5rem; margin-bottom: 1rem; }
        .error-msg { color: #334155; font-size: 1.1rem; }
        a { display: inline-block; margin-top: 1.5rem; color: #2563eb; text-decoration: underline; }
      </style>
    </head>
    <body>
      <div class="error-box">
        <div class="error-title">Role Assignment Error</div>
        <div class="error-msg">User already has the role <b>${existingRole}</b>.</div>
        <a href="/dashboard">Go to Dashboard</a>
      </div>
    </body>
  </html>`,
                {
                    status: 400,
                    headers: { "Content-Type": "text/html" },
                }
            );
        }

        if (role !== "teacher" && role !== "student") {
            // Validate the role to be assigned
            return new Response(
                `<html>
    <head>
      <title>Invalid Role</title>
      <style>
        body { font-family: sans-serif; background: #f8fafc; color: #1e293b; display: flex; align-items: center; justify-content: center; height: 100vh; }
        .error-box { background: #fff; border-radius: 1rem; box-shadow: 0 2px 8px #0001; padding: 2rem 3rem; text-align: center; }
        .error-title { color: #dc2626; font-size: 1.5rem; margin-bottom: 1rem; }
        .error-msg { color: #334155; font-size: 1.1rem; }
        a { display: inline-block; margin-top: 1.5rem; color: #2563eb; text-decoration: underline; }
      </style>
    </head>
    <body>
      <div class="error-box">
        <div class="error-title">Invalid Role</div>
        <div class="error-msg">The role you tried to assign is not allowed.</div>
        <a href="/dashboard">Go to Dashboard</a>
      </div>
    </body>
  </html>`,
                {
                    status: 400,
                    headers: { "Content-Type": "text/html" },
                }
            );
        }

        await sendRole({ role, userId: session.session.userId }); // Call the sendRole function to
        // update the user's role in the database
        // wait for the role to be updated

        return redirect({
            to: `/dashboard`, // Redirect to the dashboard after assigning the role
        });
    },
});

// Mostly the return is in JSON format, but you can also return HTML or other formats
// based on the requirements of your application.
