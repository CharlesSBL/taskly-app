import { useQuery } from '@tanstack/react-query'
import { todoKeys } from '../api/queryKeys'
import { todosApi } from '../api/todos'

export function useTodosQuery() {
  return useQuery({
    queryKey: todoKeys.list,
    queryFn: ({ signal }) => todosApi.list(signal),
  })
}
