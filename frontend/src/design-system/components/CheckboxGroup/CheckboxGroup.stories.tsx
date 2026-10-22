import type { Meta, StoryObj } from '@storybook/react-vite'
import { useState } from 'react'
import { CheckboxGroup } from './CheckboxGroup'

const meta: Meta<typeof CheckboxGroup> = {
  title: 'Design System/CheckboxGroup',
  component: CheckboxGroup,
  args: {
    label: 'Team members needed',
    tooltip: 'Select all roles required for this project.',
    options: ['FE devs', 'BE devs', 'Designer', 'Data Eng', 'Product Owner'],
    helper: 'Pick all needed roles.',
  },
}

export default meta

type Story = StoryObj<typeof CheckboxGroup>

export const Default: Story = {
  render: (args) => {
    const [value, setValue] = useState<string[]>(['Product Owner'])
    return <CheckboxGroup {...args} value={value} onChange={setValue} />
  },
}

export const WithError: Story = {
  render: (args) => {
    const [value, setValue] = useState<string[]>([])
    return (
      <CheckboxGroup
        {...args}
        value={value}
        onChange={setValue}
        error="Select at least one option"
      />
    )
  },
}
