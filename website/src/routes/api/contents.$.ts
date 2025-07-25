import { createServerFileRoute } from "@tanstack/react-start/server";
import { getContentsByClassId } from "../../lib/db/fetch_contents";
export const ServerRoute = createServerFileRoute("/api/contents/$").methods({
    GET: async ({ params }) => {
        try {
            const classId = params._splat;

            if (!classId) {
                return new Response(
                    JSON.stringify({ error: "Class ID is required" }),
                    {
                        status: 400,
                        headers: { "Content-Type": "application/json" },
                    }
                );
            }

            const contents = await getContentsByClassId(classId);

            return new Response(JSON.stringify({ contents, classId }), {
                status: 200,
                headers: { "Content-Type": "application/json" },
            });
        } catch (error) {
            console.error("API Error:", error);
            return new Response(
                JSON.stringify({ error: "Failed to fetch contents" }),
                {
                    status: 500,
                    headers: { "Content-Type": "application/json" },
                }
            );
        }
    },
});
