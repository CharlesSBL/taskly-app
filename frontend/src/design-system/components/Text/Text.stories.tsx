import type { Meta, StoryObj } from '@storybook/react-vite'
import { Text } from './Text'

const meta: Meta<typeof Text> = {
  title: 'Design System/Text',
  component: Text,
  args: { children: 'Create, organize, and complete tasks.' },
}

export default meta

type Story = StoryObj<typeof Text>

export const Body: Story = {}
export const Small: Story = { args: { size: 'small' } }
export const Muted: Story = { args: { muted: true } }
export const PreserveWhitespace: Story = {
  args: { preserveWhitespace: true, children: 'First step\nSecond step' },
}
