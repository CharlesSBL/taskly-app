import { CircleCheck } from 'lucide-react'
import { Alert } from '../design-system'

export function SuccessNotice({ message }: { message: string }) {
  if (!message) return null
  return (
    <div className="notice-position">
      <Alert variant="success">
        <CircleCheck size={18} aria-hidden="true" />
        {message}
      </Alert>
    </div>
  )
}
