import { createFileRoute } from "@tanstack/react-router"
import { useState, useEffect } from "react"
import AddContent from "@/components/add-content"

interface Content {
  id: string
  title: string
  body: string
  classId: string
}

interface ApiResponse {
  contents: Content[]
  classId: string
  error?: string
}

export const Route = createFileRoute("/contents/$classId")({
  component: RouteComponent,
})

function RouteComponent() {
  const params = Route.useParams()
  const [contents, setContents] = useState<Content[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchContents = async () => {
      if (!params.classId) {
        setError('No class ID provided')
        setLoading(false)
        return
      }

      try {
        setLoading(true)
        setError(null)
        
        const response = await fetch(`/api/contents/${params.classId}`)
        const data: ApiResponse = await response.json()
        
        if (!response.ok) {
          throw new Error(data.error || 'Failed to fetch contents')
        }
        
        setContents(data.contents)
      } catch (err) {
        console.error('Fetch error:', err)
        setError(err instanceof Error ? err.message : 'An error occurred')
      } finally {
        setLoading(false)
      }
    }

    fetchContents()
  }, [params.classId])

  if (loading) {
    return (
      <div>
        <h1>Loading Contents...</h1>
        <p>Fetching contents for class {params.classId}</p>
      </div>
    )
  }

  if (error) {
    return (
      <div>
        <h1>Error</h1>
        <p style={{ color: 'red' }}>{error}</p>
        <button onClick={() => window.location.reload()}>
          Try Again
        </button>
      </div>
    )
  }

  return (
    <>
      <div>Hello "/contents/$classId"!</div>
      <div>
        <h1>Contents for Class {params.classId}</h1>
        {contents.length > 0 ? (
          <ul>
            {contents.map((content) => (
              <li key={content.id} style={{ marginBottom: '1rem', padding: '1rem', border: '1px solid #ccc' }}>
                <h3>{content.title}</h3>
                <p>{content.body}</p>
                <small>Class ID: {content.classId}</small>
              </li>
            ))}
          </ul>
        ) : (
          <p>No contents found for this class.</p>
        )}
      </div>
      <div>
        <h2>Add New Content</h2>
        <AddContent />
      </div>
    </>
  )
}
