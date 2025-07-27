import { auth } from "@/lib/auth/auth";
import { createServerFileRoute } from "@tanstack/react-start/server";
import addContents from "@/lib/db/addcontents";

export const ServerRoute = createServerFileRoute("/api/addcontents").methods({
    POST: async ({ request }) => {
        const formData = await request.formData();
        const title = formData.get("title") as string;
        const body = formData.get("body") as string;
        const type = formData.get("type") as string;
        const deadline =  "No Deadline";
        const materialId = formData.get("materialId") as string;
        const classId = formData.get("classId") as string;
        console.log({ title, body, type, deadline, materialId, classId });
        // Validate required fields
        if (
            !title ||
            !body ||
            !type ||
            !materialId ||
            !classId ||
            (type === "assignment" && !deadline)
        ) {
            return new Response(
                JSON.stringify({
                    error: "Title, body, type, materialId, classId are required. Deadline is required for assignments.",
                }),
                {
                    status: 400,
                    headers: { "Content-Type": "application/json" },
                }
            );
        }

        const session = await auth.api.getSession({
            headers: request.headers,
        });

        if (session) {
            await addContents({
                title,
                body,
                type,
                deadline,
                materialId,
                classId,
            });
        }

        return new Response(null, {
            status: 303, // or 302
            headers: {
                Location: `/dashboard`, // e.g., "/dashboard" or wherever you want to redirect
            },
        });
    },
});
