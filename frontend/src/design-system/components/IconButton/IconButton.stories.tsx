import type { Meta, StoryObj } from '@storybook/react-vite'
import { IconButton } from './IconButton'

const meta: Meta<typeof IconButton> = {
  title: 'Design System/IconButton',
  component: IconButton,
  args: {
    children: '🔍',
    size: 'medium',
    state: 'normal',
  },
}

export default meta

type Story = StoryObj<typeof IconButton>

export const Solid: Story = {
  args: {
    variant: 'solid',
  },
}

export const Ghost: Story = {
  args: {
    variant: 'ghost',
  },
}

export const Sizes: Story = {
  render: (args) => (
    <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
      <IconButton {...args} size="small">
        🔍
      </IconButton>
      <IconButton {...args} size="medium">
        🔍
      </IconButton>
      <IconButton {...args} size="large">
        🔍
      </IconButton>
    </div>
  ),
}

export const States: Story = {
  render: (args) => (
    <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
      <IconButton {...args} state="normal">
        🔍
      </IconButton>
      <IconButton {...args} state="disabled">
        🔍
      </IconButton>
      <IconButton {...args} state="locked">
        🔒
      </IconButton>
    </div>
  ),
}
