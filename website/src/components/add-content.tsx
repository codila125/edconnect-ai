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

// Function to trigger PDF summarization in background
const triggerBackgroundSummarization = (pdfUrl: string) => {
    // Fire and forget - don't await this
    fetch(`http://localhost:8000/summarize?pdf_url=${encodeURIComponent(pdfUrl)}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        },
    })
    .then(response => {
        if (response.ok) {
            console.log(`Background summarization started for: ${pdfUrl}`);
        } else {
            console.warn(`Background summarization request failed: ${response.status}`);
        }
    })
    .catch(error => {
        console.error('Background summarization error:', error);
        // Don't throw - this is background processing
    });
};

const Upload = ({ classId }: { classId: string }) => {
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [materialId, setMaterialId] = useState<string | null>(null);
    const [pdfUrl, setPdfUrl] = useState<string | null>(null);
    const [isSubmitting, setIsSubmitting] = useState(false);

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
            setPdfUrl(urlData.publicUrl);

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

    // Handle form submission
    const handleFormSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        
        if (!materialId || !pdfUrl) {
            alert("Please upload a PDF file first");
            return;
        }

        setIsSubmitting(true);
        
        try {
            // Get form data
            const formData = new FormData(event.currentTarget);
            
            // Submit form to your existing API
            const response = await fetch("/api/addcontents", {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                throw new Error(`Failed to add content: ${response.status}`);
            }

            // Content addition successful - start background summarization
            triggerBackgroundSummarization(pdfUrl);
            
            // Show success message and reset form immediately
            alert("Content added successfully! PDF summary will be generated in the background.");
            event.currentTarget.reset();
            setMaterialId(null);
            setPdfUrl(null);

        } catch (error) {
            console.error("Form submission error:", error);
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <>
            <h1>Add Contents</h1>
            <form onSubmit={handleFormSubmit}>
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
                <input type="hidden" name="materialId" value={materialId ?? ""} />
                <input type="hidden" name="classId" value={classId ?? ""} />

                <button 
                    type="submit" 
                    disabled={!materialId || isSubmitting || uploadMutation.isPending}
                >
                    {isSubmitting ? "Adding Content..." : "Add Content"}
                </button>
                
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
                        disabled={uploadMutation.isPending || isSubmitting}
                        className=""
                    >
                        {uploadMutation.isPending ? (
                            <div className="flex gap-1">
                                <span
                                    className=""
                                    style={{ animationDelay: "0ms" }}
                                >
                                    Uploading...
                                </span>
                            </div>
                        ) : (
                            "+"
                        )}
                    </button>
                    
                    {materialId && (
                        <div className="ml-2 text-sm text-green-600">
                            ✓ PDF uploaded successfully
                        </div>
                    )}
                </div>
            </form>
        </>
    );
};

export default Upload;