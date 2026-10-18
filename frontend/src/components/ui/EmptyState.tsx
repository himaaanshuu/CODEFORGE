import type { ReactNode } from 'react'

interface Props {
  title: string
  message: string
  action?: ReactNode
}

export function EmptyState({ title, message, action }: Props) {
  return (
    <div className="mx-auto flex max-w-lg flex-col items-center px-6 py-20 text-center">
      <span className="chip">{title}</span>
      <p className="mt-4 text-sm leading-relaxed text-subtle">{message}</p>
      {action && <div className="mt-6 flex justify-center">{action}</div>}
    </div>
  )
}
