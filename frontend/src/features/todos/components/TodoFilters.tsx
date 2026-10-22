import { Input, Select } from '../../../design-system'
import type { Filter, Sort } from '../types'

interface TodoFiltersProps {
  filter: Filter
  search: string
  sort: Sort
  onFilterChange: (filter: Filter) => void
  onSearchChange: (search: string) => void
  onSortChange: (sort: Sort) => void
}

export function TodoFilters({
  filter,
  search,
  sort,
  onFilterChange,
  onSearchChange,
  onSortChange,
}: TodoFiltersProps) {
  return (
    <section className="filters-layout" aria-label="Task filters">
      <Input
        label="Search tasks"
        placeholder="Type to search…"
        value={search}
        onChange={(event) => onSearchChange(event.target.value)}
      />
      <Select
        label="Status"
        value={filter}
        onChange={(event) => onFilterChange(event.target.value as Filter)}
        options={[
          { value: 'all', label: 'All statuses' },
          { value: 'active', label: 'To do' },
          { value: 'completed', label: 'Completed' },
        ]}
      />
      <Select
        label="Sort by"
        value={sort}
        onChange={(event) => onSortChange(event.target.value as Sort)}
        options={[
          { value: 'newest', label: 'Newest' },
          { value: 'priority', label: 'Priority' },
          { value: 'due', label: 'Due date' },
        ]}
      />
    </section>
  )
}
