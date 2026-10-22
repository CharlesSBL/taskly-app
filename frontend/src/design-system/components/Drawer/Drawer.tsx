import { useEffect, useId, useRef } from 'react'
import { X } from 'lucide-react'
import { IconButton } from '../IconButton'
import { Heading } from '../Heading'
import type { DrawerProps } from './Drawer.types'
import { Content, Header, Overlay, Panel } from './Drawer.styles'

/** Side drawer with native focus management and dismissal blocked while busy. */
export function Drawer({
  title,
  isOpen,
  onClose,
  children,
  busy = false,
}: DrawerProps) {
  const ref = useRef<HTMLDialogElement>(null)
  const titleId = useId()
  useEffect(() => {
    const dialog = ref.current!
    if (!isOpen) return
    dialog.showModal()
    const field = dialog.querySelector<HTMLElement>(
      'input:not(:disabled), textarea:not(:disabled), select:not(:disabled)',
    )
    field?.focus()
    return () => dialog.close()
  }, [isOpen])

  return (
    <Overlay
      ref={ref}
      aria-labelledby={titleId}
      aria-modal="true"
      aria-busy={busy}
      onCancel={(event) => {
        event.preventDefault()
        if (!busy) onClose()
      }}
      onClick={(event) => {
        if (event.target === event.currentTarget && !busy) onClose()
      }}
    >
      <Panel>
        <Header>
          <Heading level={2} id={titleId}>
            {title}
          </Heading>
          <IconButton
            type="button"
            variant="ghost"
            aria-label="Close"
            disabled={busy}
            onClick={onClose}
          >
            <X size={20} />
          </IconButton>
        </Header>
        <Content>{children}</Content>
      </Panel>
    </Overlay>
  )
}
