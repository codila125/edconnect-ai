import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import AddContent from "@/components/add-content";
import ChatModule from "@/components/chat";
import { createServerFn } from "@tanstack/react-start";
import { getWebRequest } from "@tanstack/react-start/server";
import { auth } from "@/lib/auth/auth";
import db from "@/lib/db/drizzle";
import * as schema from "@/lib/db/schema";
import { eq } from "drizzle-orm";

interface Content {
  id: string;
  title: string;
  body: string;
  classId: string;
  summary: string;
}

interface ApiResponse {
  contents: Content[];
  classId: string;
  error?: string;
}

const authStateFn = createServerFn({
    method: "GET",
    response: "data",
}).handler(async () => {
    const request = getWebRequest();
    if (!request) {
        throw new Error("Unauthorized");
    }

    const session = await auth.api.getSession(request);

    if (!session) {
        throw new Error("Unauthorized");
    }

    const userId = await db
    .select({ id: schema.session.userId })
    .from(schema.session)
    .where(eq(schema.session.userId, session?.user.id))
    .execute();

    if (!userId || userId.length === 0) {
        throw new Error("User not found");
    }

    const userIdValue = userId[0]?.id;
    const classId = await db
    .select({ id: schema.enrollments.classId })
    .from(schema.enrollments)
    .where(eq(schema.enrollments.studentId, userIdValue))
    .execute();

    if (!classId || classId.length === 0) {
       const classId2 = await db
       .select({ id: schema.classes.id })
       .from(schema.classes)
       .where(eq(schema.classes.teacherId, userIdValue))
       .execute();
       console.log("Class ID (Teacher):", classId2);
       return { session: session, urls: [] };
    }

    // Get all contents for the class
    const contentsData = await db
    .select({ 
        materialId: schema.contents.materialId 
    })
    .from(schema.contents)
    .where(eq(schema.contents.classId, classId[0]?.id))
    .execute();

    if (!contentsData || contentsData.length === 0) {
        return { session: session, urls: [] };
    }

    // Get all material URLs for the contents
    const materialIds = contentsData.map(content => content.materialId);
    const urls = await db
    .select({ 
        url: schema.materials.url,
        name: schema.materials.name,
        id: schema.materials.id
    })
    .from(schema.materials)
    .where(eq(schema.materials.id, materialIds[0])) // You might want to use `in` operator for multiple IDs
    .execute();

    return { session: session, urls: urls };
});

export const Route = createFileRoute("/contents/$classId")({
  loader: async () => {
    const result = await authStateFn();
    if (!result) {
      return { session: undefined, urls: [] };
    }
    const { session, urls } = result;
    return { session, urls };
  },
  component: RouteComponent,
});

function RouteComponent() {
  const params = Route.useParams();
  const { session, urls } = Route.useLoaderData();
  const [contents, setContents] = useState<Content[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [currentUserId, setCurrentUserId] = useState(session?.user.id || "");
  
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const storedUserId = localStorage.getItem('userId');
      if (storedUserId) {
        setCurrentUserId(storedUserId);
      } else {
        const newUserId = `user_${Date.now()}`;
        localStorage.setItem('userId', newUserId);
        setCurrentUserId(newUserId);
      }
    }
  }, []);

  useEffect(() => {
    const fetchContents = async () => {
      if (!params.classId) {
        setError("No class ID provided");
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);
        const response = await fetch(`/api/contents/${params.classId}`);
        const data: ApiResponse = await response.json();

        if (!response.ok) {
          throw new Error(data.error || "Failed to fetch contents");
        }

        setContents(data.contents);
      } catch (err) {
        console.error("Fetch error:", err);
        setError(
          err instanceof Error ? err.message : "An error occurred"
        );
      } finally {
        setLoading(false);
      }
    };

    fetchContents();
  }, [params.classId]);

  if (loading) {
    return (
      <div>
        <h1>Loading Contents...</h1>
        <p>Fetching contents for class {params.classId}</p>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <h1>Error</h1>
        <p>{error}</p>
        <button onClick={() => window.location.reload()}>
          Try Again
        </button>
      </div>
    );
  }

  return (
    <>
      <div>
        <h1>Contents for Class</h1>
        

        {/* Display Contents */}
        {contents.length > 0 ? (
          <ul>
            {contents.map((content) => (
              <li key={content.id}>
                <h3>{content.title}</h3>
                <p>{content.body}</p>
                {urls && urls.length > 0 && (
                  <div>
                    <h3>Class Materials</h3>
                    {urls.map((material, index) => (
                      <div key={material.id || index}>
                        <p><strong>{material.name}</strong></p>
                        <a 
                          href={material.url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          >
                          {material.url}
                        </a>
                      </div>
                    ))}
                    <h2>Summary</h2>
                    <p>{content.summary}</p>
                  </div>
                )}
              </li>
            ))}
          </ul>
        ) : (
          <p>No contents found for this class.</p>
        )}
      </div>

      <div>
        {session?.user.role === "teacher" && (
          <AddContent classId={params.classId} />
        )}
      </div>

      <div>
        <h2>Class Chat</h2>
        <ChatModule 
          classId={params.classId}
          currentUserId={currentUserId}
          currentUserName={session?.user.name || "Your Name"}
        />
      </div>
    </>
  );
}