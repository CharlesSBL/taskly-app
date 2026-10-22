import { useIsMutating } from '@tanstack/react-query'
import { todoKeys } from '../api/queryKeys'

export function useTodosBusy() {
  return useIsMutating({ mutationKey: todoKeys.all }) > 0
}
