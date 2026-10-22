import type { Meta, StoryObj } from '@storybook/react-vite'
import { Select } from './Select'

const meta: Meta<typeof Select> = {
  title: 'Design System/Select',
  component: Select,
  args: {
    label: 'Category',
    helperText: 'Select one category.',
    tooltip: 'Category is required for project details.',
    options: [
      { value: '', label: 'Select a category' },
      { value: 'internal', label: 'Internal' },
      { value: 'external', label: 'External' },
      { value: 'vendor', label: 'Vendor' },
    ],
  },
}

export default meta

type Story = StoryObj<typeof Select>

export const Default: Story = {}

export const WithError: Story = {
  args: {
    error: 'Please choose a category',
  },
}

export const Disabled: Story = {
  args: {
    state: 'disabled',
    value: 'internal',
  },
}

export const Locked: Story = {
  args: {
    state: 'locked',
    value: 'vendor',
    helperText: 'This value is locked.',
  },
}
