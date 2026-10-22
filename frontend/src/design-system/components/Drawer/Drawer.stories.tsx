import type { Meta, StoryObj } from '@storybook/react-vite'
import { useState } from 'react'
import { Button } from '../Button'
import { Drawer } from './Drawer'

const meta: Meta<typeof Drawer> = {
  title: 'Design System/Drawer',
  component: Drawer,
}

export default meta

type Story = StoryObj<typeof Drawer>

export const Default: Story = {
  render: () => {
    const [open, setOpen] = useState(true)
    return (
      <>
        <Button type="button" onClick={() => setOpen(true)}>
          Open drawer
        </Button>
        <Drawer
          title="Resource notes"
          isOpen={open}
          onClose={() => setOpen(false)}
        >
          <p>Keep track of decisions and next steps.</p>
        </Drawer>
      </>
    )
  },
}
