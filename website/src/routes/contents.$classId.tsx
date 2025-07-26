import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import AddContent from "@/components/add-content";
import ChatModule from "@/components/chat";
import { createServerFn } from "@tanstack/react-start";
import { getWebRequest } from "@tanstack/react-start/server";
import { auth } from "@/lib/auth/auth";
interface Content {
  id: string;
  title: string;
  body: string;
  classId: string;
}

interface ApiResponse {
  contents: Content[];
  classId: string;
  error?: string;
}


const authStateFn = createServerFn({
    method: "GET", // HTTP method to use
    response: "data", // Response handling mode
}).handler(async () => {
    const request = getWebRequest();
    if (!request) {
        throw new Error("Unauthorized");
    }

    const session = await auth.api.getSession(request);

    return { session: session };
});

export const Route = createFileRoute("/contents/$classId")({
  loader: async () => {
    const { session } = await authStateFn();
    return { session };
  },
  component: RouteComponent,
});

function RouteComponent() {
  const params = Route.useParams();
  const { session } = Route.useLoaderData();
  const [contents, setContents] = useState<Content[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  console.log("RouteComponent session:", session?.user.id);
  // You'll need to get the current user ID somehow - this is just an example
  const [currentUserId, setCurrentUserId] = useState(session?.user.id || "");
  
  useEffect(() => {
    // Set user ID from localStorage after component mounts
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
        <p style={{ color: "red" }}>{error}</p>
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
        {contents.length > 0 ? (
          <ul>
            {contents.map((content) => (
              <li
                key={content.id}
                style={{
                  marginBottom: "1rem",
                  padding: "1rem",
                  border: "1px solid #ccc",
                }}
              >
                <h3>{content.title}</h3>
                <p>{content.body}</p>
              </li>
            ))}
          </ul>
        ) : (
          <p>No contents found for this class.</p>
        )}
      </div>

      <div>
        {session?.user.role === "teacher" && (<>
          <AddContent classId={params.classId} />
        </>)}
      </div>

      {/* Add the Chat Module */}
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