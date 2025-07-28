import db from "./drizzle";
import * as schema from "./schema";

export default async function addContents({
    title,
    body,
    type,
    deadline,
    materialId, // <-- Accept materialId
    classId, // <-- Accept classId
}: {
    title: string;
    body: string;
    type: string;
    deadline: string;
    materialId: string; // <-- Add materialId to the type
    classId: string; // <-- Add classId to the type
}) {
    // Only allow valid types as per schema
    const allowedTypes = ["assignment", "material"];
    if (!allowedTypes.includes(type)) {
        throw new Error(`Invalid type: ${type}`);
    }

    await db.insert(schema.contents).values({
        classId,
        title,
        body,
        type: type as "assignment" | "material",
        deadline: deadline ? deadline : "No Deadline", // Default to "No Deadline" if not provided
        materialId,
    });
    console.log(`Content ${title} added successfully`);
}
