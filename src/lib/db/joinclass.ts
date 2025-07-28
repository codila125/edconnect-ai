import db from "./drizzle";
import * as schema from "./schema";

export default async function joinClass({
    classId,
    userId, // Assuming you have a userId to associate the class with a user
}: {
    classId: string; // Class ID
    userId: string; // User ID
}) {
    await db.insert(schema.enrollments).values({
        classId: classId,
        studentId: userId,
    });
    return console.log(`User ${userId} joined class ${classId} successfully`);
}
