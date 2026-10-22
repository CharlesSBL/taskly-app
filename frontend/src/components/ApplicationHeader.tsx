import { AppHeader, Heading, Text } from '../design-system'

export function ApplicationHeader() {
  return (
    <AppHeader>
      <a href="/" aria-label="Taskly — home">
        <Heading level={2}>Taskly</Heading>
      </a>
      <Text muted>Task list</Text>
    </AppHeader>
  )
}
