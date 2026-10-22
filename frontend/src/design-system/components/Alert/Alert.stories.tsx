import type { Meta, StoryObj } from '@storybook/react-vite'
import { Alert } from './Alert'

const meta: Meta<typeof Alert> = {
  title: 'Design System/Alert',
  component: Alert,
  args: { children: 'Your task list is up to date.' },
}

export default meta

type Story = StoryObj<typeof Alert>

export const Info: Story = { args: { variant: 'info' } }
export const Success: Story = {
  args: { variant: 'success', children: 'Task saved successfully.' },
}
export const Warning: Story = {
  args: { variant: 'warning', children: 'Could not save. Please try again.' },
}
