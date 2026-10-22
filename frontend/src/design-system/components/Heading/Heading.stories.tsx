import type { Meta, StoryObj } from '@storybook/react-vite'
import { Heading } from './Heading'

const meta: Meta<typeof Heading> = {
  title: 'Design System/Heading',
  component: Heading,
  args: { children: 'My tasks' },
}

export default meta

type Story = StoryObj<typeof Heading>

export const LevelOne: Story = { args: { level: 1 } }
export const LevelTwo: Story = { args: { level: 2 } }
export const LevelThree: Story = { args: { level: 3 } }
export const Completed: Story = { args: { completed: true } }
