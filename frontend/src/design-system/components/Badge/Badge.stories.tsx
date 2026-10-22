import type { Meta, StoryObj } from '@storybook/react-vite'
import { Badge } from './Badge'

const meta: Meta<typeof Badge> = {
  title: 'Design System/Badge',
  component: Badge,
  args: {
    children: 'Status',
  },
}

export default meta

type Story = StoryObj<typeof Badge>

export const Neutral: Story = {
  args: { variant: 'neutral' },
}

export const Info: Story = {
  args: { variant: 'info' },
}

export const Success: Story = {
  args: { variant: 'success' },
}

export const Warning: Story = {
  args: { variant: 'warning' },
}
