import { useState, type FormEvent } from 'react'
import type { TodoInput } from '../types'
import { priorityLabels, validateTodo } from '../utils/todos'
import { Alert, Button, Input, Select, Text } from '../../../design-system'

const emptyTodo: TodoInput = {
  title: '',
  description: '',
  priority: 'medium',
  due_date: null,
  completed: false,
}

export function TodoForm({
  initial = emptyTodo,
  onSubmit,
  onCancel,
  busy,
  error,
}: {
  initial?: TodoInput
  onSubmit: (todo: TodoInput) => Promise<void>
  onCancel: () => void
  busy: boolean
  error: string | null
}) {
  const [values, setValues] = useState<TodoInput>({ ...initial })
  const [errors, setErrors] = useState<Record<string, string>>({})
  const change = (key: keyof TodoInput, value: string | null) =>
    setValues((current) => ({ ...current, [key]: value }))
  function submit(event: FormEvent) {
    event.preventDefault()
    const nextErrors = validateTodo(values)
    setErrors(nextErrors)
    if (!Object.keys(nextErrors).length)
      void onSubmit({
        ...values,
        title: values.title.trim(),
        description: values.description.trim(),
      })
  }
  return (
    <form onSubmit={submit} noValidate className="stack">
      <Text muted>
        Write down what is on your mind. Make room to get things done.
      </Text>
      <fieldset disabled={busy} className="form-fields stack">
        <div className="field">
          <Input
            autoFocus
            id="title"
            label="Task title *"
            value={values.title}
            onChange={(e) => change('title', e.target.value)}
            placeholder="What would you like to do?"
            error={errors.title}
            required
          />
        </div>
        <div className="field">
          <Input
            multiline
            id="description"
            label="Description (optional)"
            rows={3}
            value={values.description}
            onChange={(e) => change('description', e.target.value)}
            placeholder="Details worth remembering…"
            error={errors.description}
          />
        </div>
        <div className="form-row">
          <div className="field">
            <Select
              id="priority"
              label="Priority"
              value={values.priority}
              onChange={(e) => change('priority', e.target.value)}
              options={Object.entries(priorityLabels).map(([value, label]) => ({
                value,
                label,
              }))}
            />
          </div>
          <div className="field">
            <Input
              id="due_date"
              label="Due date (optional)"
              type="date"
              value={values.due_date ?? ''}
              onChange={(e) => change('due_date', e.target.value || null)}
              error={errors.due_date}
            />
          </div>
        </div>
      </fieldset>
      {error && <Alert variant="warning">{error}</Alert>}
      <div className="row actions">
        <Button
          type="button"
          variant="secondary"
          disabled={busy}
          onClick={onCancel}
        >
          Cancel
        </Button>
        <Button type="submit" disabled={busy}>
          {busy ? 'Saving…' : 'Save task'}
        </Button>
      </div>
    </form>
  )
}
