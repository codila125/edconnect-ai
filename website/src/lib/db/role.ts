// this file is responsible for assigning roles to users in the database
// It updates the user's role in the database based on the provided userId and role.
// The function sendRole takes an object with role and userId as parameters and updates the user's
// role in the database using Drizzle ORM. It logs a message indicating the role assignment.
// The role comes from user interface through API and userID comes from API
import db from "./drizzle";
import * as schema from "./auth-schema";
import { eq } from "drizzle-orm";

export default async function sendRole({
    role,
    userId,
}: {
    role: "teacher" | "student"; // Role can be either 'teacher' or 'student'
    //we can customize this to include more roles in the future
    //like admin, superadmin, etc.
    //but for now, we are keeping it simple with just teacher and student
    userId: string;
    // User ID is a string that uniquely identifies the user in the database
}) {
    await db
        .update(schema.user) // Update the user table in the database
        .set({ role: role })
        .where(eq(schema.user.id, userId)); // Set the role of the user where the user ID matches
    // the provided userId from current session
    return console.log(`Role ${role} assigned to user with ID ${userId}`);
}
