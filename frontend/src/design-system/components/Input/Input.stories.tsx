import type { Meta, StoryObj } from '@storybook/react-vite'
import { Input } from './Input'

const meta: Meta<typeof Input> = {
  title: 'Design System/Input',
  component: Input,
  args: {
    label: 'Role title',
    placeholder: 'Frontend Engineer',
    helperText: 'Use a short and clear title.',
  },
}

export default meta

type Story = StoryObj<typeof Input>

export const Text: Story = {}

export const Textarea: Story = {
  args: {
    multiline: true,
    label: 'Description',
    placeholder: 'Tell us about your scope...',
  },
}

export const WithError: Story = {
  args: {
    error: 'This field is required',
  },
}

export const Locked: Story = {
  args: {
    label: 'Resource name',
    value: 'Hiring Pipeline',
    state: 'locked',
    tooltip: 'Resource name is immutable after creation.',
    helperText: 'This value cannot be changed.',
  },
}

export const Disabled: Story = {
  args: {
    label: 'Owner',
    value: 'John Doe',
    state: 'disabled',
  },
}
