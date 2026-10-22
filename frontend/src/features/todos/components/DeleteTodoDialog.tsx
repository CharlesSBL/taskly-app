import { Alert, Button, Drawer, Text } from '../../../design-system'
import { useDeleteTodoMutation } from '../hooks/useDeleteTodoMutation'
import type { Todo } from '../types'

export function DeleteTodoDialog({
  todo,
  busy,
  onClose,
  onDeleted,
}: {
  todo: Todo
  busy: boolean
  onClose: () => void
  onDeleted: () => void
}) {
  const deleteTodo = useDeleteTodoMutation()
  const pending = busy || deleteTodo.isPending
  async function remove() {
    if (pending) return
    try {
      await deleteTodo.mutateAsync(todo.id)
      onDeleted()
    } catch {
      // Keep confirmation open so the server error is visible and retry is possible.
    }
  }
  return (
    <Drawer isOpen title="Delete task?" busy={pending} onClose={onClose}>
      <Text>The task “{todo.title}” will be permanently deleted.</Text>
      {deleteTodo.error && (
        <Alert variant="warning">{deleteTodo.error.message}</Alert>
      )}
      <div className="row actions">
        <Button variant="secondary" disabled={pending} onClick={onClose}>
          Cancel
        </Button>
        <Button
          variant="danger"
          disabled={pending}
          onClick={() => void remove()}
        >
          {pending ? 'Deleting…' : 'Delete task'}
        </Button>
      </div>
    </Drawer>
  )
}
