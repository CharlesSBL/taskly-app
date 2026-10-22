import { useMutation, useQueryClient } from '@tanstack/react-query'
import { todoKeys } from '../api/queryKeys'
import { todosApi } from '../api/todos'
import type { Todo, TodoInput } from '../types'

export function useCreateTodoMutation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationKey: todoKeys.create,
    mutationFn: (input: TodoInput) => todosApi.create(input),
    onSuccess: async (saved) => {
      // Stop an older refetch from overwriting the confirmed server response.
      await queryClient.cancelQueries({ queryKey: todoKeys.list })
      queryClient.setQueryData<Todo[]>(todoKeys.list, (current = []) => [
        saved,
        ...current.filter((todo) => todo.id !== saved.id),
      ])
    },
  })
}
