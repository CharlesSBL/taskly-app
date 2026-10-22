import { Plus } from 'lucide-react'
import { Button, Card, Heading, Text } from '../../../design-system'

export function TodoEmptyState({
  hasTodos,
  disabled,
  onCreate,
}: {
  hasTodos: boolean
  disabled: boolean
  onCreate: () => void
}) {
  return (
    <Card>
      <Heading level={3}>
        {hasTodos ? 'No matching tasks' : 'Add your first task'}
      </Heading>
      <Text muted>
        {hasTodos
          ? 'Change the status filter or search to find your tasks.'
          : 'Write down what you need to do and get started.'}
      </Text>
      {!hasTodos && (
        <div>
          <Button variant="secondary" disabled={disabled} onClick={onCreate}>
            <Plus size={16} aria-hidden="true" />
            Add your first task
          </Button>
        </div>
      )}
    </Card>
  )
}
