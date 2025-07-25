import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/contents')({
  component: RouteComponent,
})

function RouteComponent() {
  return <div>Hello "/contents"!</div>
}
