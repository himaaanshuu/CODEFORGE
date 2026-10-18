import type { ReactNode } from 'react'
import { AlertTriangle, CheckCircle2, Info } from 'lucide-react'

export type AlertVariant = 'error' | 'info' | 'success'

const variantStyle: Record<AlertVariant, { wrap: string; Icon: typeof Info }> = {
  error: { wrap: 'border-bad/35 bg-bad/8 text-bad', Icon: AlertTriangle },
  info: { wrap: 'border-info/35 bg-info/8 text-fg', Icon: Info },
  success: { wrap: 'border-ok/35 bg-ok/8 text-ok', Icon: CheckCircle2 },
}

interface Props {
  variant?: AlertVariant
  title?: string
  children: ReactNode
  className?: string
}

export function Alert({ variant = 'error', title, children, className = '' }: Props) {
  const { wrap, Icon } = variantStyle[variant]
  return (
    <div
      role={variant === 'error' ? 'alert' : 'status'}
      className={`flex gap-3 rounded-sm border p-4 text-sm ${wrap} ${className}`}
    >
      <Icon size={16} aria-hidden className="mt-0.5 shrink-0" />
      <div className="min-w-0">
        {title && <p className="font-semibold">{title}</p>}
        <div className={title ? 'mt-0.5 break-words' : 'break-words'}>{children}</div>
      </div>
    </div>
  )
}
