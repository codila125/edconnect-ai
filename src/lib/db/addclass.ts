import db from "./drizzle";
import * as schema from "./schema";

export default async function addClass({
    name,
    description,
    activestart,
    activeend,
    teacherId, // Assuming you have a teacherId to associate the class with a teacher
}: {
    name: string; // Class name
    description: string; // Class description
    activestart: string; // Class active start time
    activeend: string; // Class active end time
    teacherId: string; // Teacher ID
}) {
    await db.insert(schema.classes).values({
        className: name,
        description,
        activeStart: activestart,
        activeEnd: activeend,
        teacherId,
    });
    return console.log(`Class ${name} added successfully`);
}
