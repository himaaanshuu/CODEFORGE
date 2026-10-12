import type { ReactNode } from 'react'

interface Props {
  title: string
  message: string
  action?: ReactNode
}

export function EmptyState({ title, message, action }: Props) {
  return (
    <div className="mx-auto max-w-xl px-6 py-16 text-center">
      <p className="eyebrow">{title}</p>
      <p className="mt-3 text-sm leading-relaxed text-subtle">{message}</p>
      {action && <div className="mt-6 flex justify-center">{action}</div>}
    </div>
  )
}
