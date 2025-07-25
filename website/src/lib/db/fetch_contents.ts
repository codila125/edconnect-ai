import db from "./drizzle";
import * as schema from "./schema";
import { eq } from "drizzle-orm";

export const getContentsByClassId = async (classId: string) => {
    const contents = await db
        .select()
        .from(schema.contents)
        .where(eq(schema.contents.classId, classId));
    return contents;
};
