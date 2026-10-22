import { Drawer } from '../../../design-system'
import { useCreateTodoMutation } from '../hooks/useCreateTodoMutation'
import { useUpdateTodoMutation } from '../hooks/useUpdateTodoMutation'
import type { Todo, TodoInput } from '../types'
import { TodoForm } from './TodoForm'

export function TodoEditor({
  todo,
  busy,
  onClose,
  onSaved,
}: {
  todo: Todo | 'new'
  busy: boolean
  onClose: () => void
  onSaved: (message: string) => void
}) {
  const createTodo = useCreateTodoMutation()
  const updateTodo = useUpdateTodoMutation()
  const mutation = todo === 'new' ? createTodo : updateTodo
  const pending = busy || mutation.isPending

  async function save(input: TodoInput) {
    if (pending) return
    try {
      if (todo === 'new') await createTodo.mutateAsync(input)
      else await updateTodo.mutateAsync({ id: todo.id, input })
      onSaved(todo === 'new' ? 'New task added.' : 'Changes saved.')
    } catch {
      // The mutation exposes the server error to the form and permits retrying.
    }
  }

  return (
    <Drawer
      isOpen
      title={todo === 'new' ? 'New task' : 'Edit task'}
      busy={pending}
      onClose={onClose}
    >
      <TodoForm
        initial={todo === 'new' ? undefined : todo}
        busy={pending}
        error={mutation.error?.message ?? null}
        onSubmit={save}
        onCancel={onClose}
      />
    </Drawer>
  )
}
