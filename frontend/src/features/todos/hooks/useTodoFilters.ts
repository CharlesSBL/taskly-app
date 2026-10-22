import { useState } from 'react'
import type { Filter, Sort, Todo } from '../types'
import { selectTodos } from '../utils/todos'

export function useTodoFilters(todos: Todo[]) {
  const [filter, setFilter] = useState<Filter>('all')
  const [search, setSearch] = useState('')
  const [sort, setSort] = useState<Sort>('newest')
  return {
    filter,
    setFilter,
    search,
    setSearch,
    sort,
    setSort,
    visible: selectTodos(todos, filter, search, sort),
  }
}
