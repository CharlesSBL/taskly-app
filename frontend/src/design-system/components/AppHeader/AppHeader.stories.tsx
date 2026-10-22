import type { Meta, StoryObj } from '@storybook/react-vite'
import { AppHeader } from './AppHeader'
import { Text } from '../Text'

const meta: Meta<typeof AppHeader> = {
  title: 'Design System/AppHeader',
  component: AppHeader,
}

export default meta

type Story = StoryObj<typeof AppHeader>

export const Default: Story = {
  render: (args) => (
    <AppHeader {...args}>
      <a href="/" aria-label="Taskly — home">
        Taskly
      </a>
      <Text muted>Task list</Text>
    </AppHeader>
  ),
}
