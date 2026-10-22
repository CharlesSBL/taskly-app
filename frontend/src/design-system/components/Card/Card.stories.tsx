import type { Meta, StoryObj } from '@storybook/react-vite'
import { Card } from './Card'

const meta: Meta<typeof Card> = {
  title: 'Design System/Card',
  component: Card,
}

export default meta

type Story = StoryObj<typeof Card>

export const Outline: Story = {
  render: () => <Card variant="outline">Outline card</Card>,
}

export const Elevated: Story = {
  render: () => <Card variant="elevated">Elevated card</Card>,
}
