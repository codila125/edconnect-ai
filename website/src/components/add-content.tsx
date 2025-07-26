import { useRef } from "react";
import { useMutation } from "@tanstack/react-query";
import db from "../lib/db/drizzle";
import { createServerFn } from "@tanstack/react-start";
import { supabase } from "../lib/supabase";
import * as schema from "../lib/db/schema";
import { eq } from "drizzle-orm";
import { useState } from "react";

const saveContents = createServerFn({ method: "POST" })
    .validator((data: { url: string; name: string }) => data)
    .handler(async ({ data }) => {
        await db.insert(schema.materials).values({
            url: data.url,
            name: data.name,
        });
        const materialId = await db
            .select({ id: schema.materials.id })
            .from(schema.materials)
            .where(eq(schema.materials.url, data.url));

        return {
            id: materialId[0].id,
            url: data.url,
            name: data.name,
        };
    });

const Upload = ({ classId }: { classId: string }) => {
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [materialId, setMaterialId] = useState<string | null>(null);

    // Upload mutation
    const uploadMutation = useMutation({
        mutationFn: async (file: File) => {
            const fileExt = file.name.split(".").pop();
            const fileName = `${Date.now()}-${Math.random().toString(36).substring(2)}.${fileExt}`;

            // Upload file to Supabase
            const { error } = await supabase.storage
                .from(import.meta.env.VITE_SUPABASE_BUCKET_NAME || "")
                .upload(fileName, file, {
                    cacheControl: "3600",
                    upsert: false,
                });

            if (error) throw error;

            // Get public URL
            const { data: urlData } = supabase.storage
                .from(import.meta.env.VITE_SUPABASE_BUCKET_NAME || "")
                .getPublicUrl(fileName);

            const saveResult = await saveContents({
                data: {
                    url: urlData.publicUrl,
                    name: file.name,
                },
            });

            setMaterialId(saveResult.id);

            return {
                publicUrl: urlData.publicUrl,
                fileName: fileName,
                saveResult: saveResult,
            };
        },
        onSuccess: async () => {
            if (fileInputRef.current) {
                fileInputRef.current.value = "";
            }
        },
        onError: (error) => {
            console.error("Upload failed:", error);
            alert("Upload failed: " + error.message);
        },
    });

    const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file && file.type.startsWith("application/pdf")) {
            uploadMutation.mutate(file);
        } else {
            alert("Please select a valid PDF file");
        }
    };

    const triggerFileSelect = () => {
        fileInputRef.current?.click();
    };

    return (
        <>
            <h1>Add Contents</h1>
            <form method="post" action="/api/addcontents">
                <label>
                    Title:
                    <input type="text" name="title" required />
                </label>
                <br />
                <label>
                    Body:
                    <textarea name="body" required></textarea>
                </label>
                <br />
                <label>
                    Type:
                    <select name="type" required>
                        <option value="assignment">Assignment</option>
                        <option value="material">Material</option>
                    </select>
                </label>
                <br />
                {/* <label>
                    Deadline:
                    <input type="datetime-local" name="deadline" />
                </label> */}
                <br />
                <input type="hidden" name="materialId" value={materialId ?? ""} />
                <input type="hidden" name="classId" value={classId ?? ""} />

                <button type="submit" disabled={!materialId}>Add Content</button>
                <div className="flex items-center">
                    <input
                        ref={fileInputRef}
                        type="file"
                        accept="application/pdf"
                        onChange={handleFileSelect}
                        className="hidden"
                    />

                    <button
                        type="button"
                        onClick={triggerFileSelect}
                        disabled={uploadMutation.isPending}
                        className=""
                    >
                        {uploadMutation.isPending ? (
                            <div className="flex gap-1">
                                <span
                                    className=""
                                    style={{ animationDelay: "0ms" }}
                                ></span>
                            </div>
                        ) : (
                            "+"
                        )}
                    </button>
                    <div>
                        material id
                        {materialId && <span>{materialId}</span>}
                    </div>
                    <div>
                        class id
                        {classId && <span>{classId}</span>}
                    </div>
                </div>
            </form>
        </>
    );
};

export default Upload;
