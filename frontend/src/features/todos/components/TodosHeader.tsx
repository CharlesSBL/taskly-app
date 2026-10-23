import { Plus } from 'lucide-react'
import { Badge, Button, Heading, Text } from '../../../design-system'

export function TodosHeader({
  disabled,
  dueSoonCount = 0,
  onCreate,
}: {
  disabled: boolean
  dueSoonCount?: number
  onCreate: () => void
}) {
  return (
    <section className="row spread" aria-labelledby="page-title">
      <div className="stack compact">
        <div className="row compact">
          <Heading id="page-title">Tasks</Heading>
          {dueSoonCount > 0 && (
            <Badge variant="warning">{dueSoonCount} due soon</Badge>
          )}
        </div>
        <Text muted>Create, organize, and complete tasks.</Text>
      </div>
      <Button disabled={disabled} onClick={onCreate}>
        <Plus size={18} aria-hidden="true" />
        New task
      </Button>
    </section>
  )
}
