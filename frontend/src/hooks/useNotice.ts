import { useCallback, useEffect, useState } from 'react'

export function useNotice() {
  const [notice, setNotice] = useState<{ message: string } | null>(null)
  const notify = useCallback((message: string) => setNotice({ message }), [])
  useEffect(() => {
    if (!notice) return
    const timeout = window.setTimeout(() => setNotice(null), 4000)
    return () => window.clearTimeout(timeout)
  }, [notice])
  return { message: notice?.message ?? '', notify }
}
