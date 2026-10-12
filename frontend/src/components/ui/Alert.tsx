import type { ReactNode } from 'react'
import { AlertTriangle, CheckCircle2, Info } from 'lucide-react'

export type AlertVariant = 'error' | 'info' | 'success'

const variantStyle: Record<AlertVariant, { wrap: string; Icon: typeof Info }> = {
  error: { wrap: 'border-bad/40 border-l-bad bg-bad/5 text-bad', Icon: AlertTriangle },
  info: { wrap: 'border-info/40 border-l-info bg-info/5 text-ink', Icon: Info },
  success: { wrap: 'border-ok/40 border-l-ok bg-ok/5 text-ok', Icon: CheckCircle2 },
}

interface Props {
  variant?: AlertVariant
  title?: string
  children: ReactNode
  className?: string
}

/** Consistent framed banner for errors, progress notes, and success states. */
export function Alert({ variant = 'error', title, children, className = '' }: Props) {
  const { wrap, Icon } = variantStyle[variant]
  return (
    <div
      role={variant === 'error' ? 'alert' : 'status'}
      className={`flex gap-3 border border-l-4 p-4 text-sm ${wrap} ${className}`}
    >
      <Icon size={16} aria-hidden className="mt-0.5 shrink-0" />
      <div className="min-w-0">
        {title && <p className="font-semibold">{title}</p>}
        <div className={title ? 'mt-0.5 break-words' : 'break-words'}>{children}</div>
      </div>
    </div>
  )
}
