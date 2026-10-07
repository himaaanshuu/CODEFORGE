import { motion, useReducedMotion } from 'framer-motion'
import type { ReactNode } from 'react'

interface Props {
  children: ReactNode
  onClick?: () => void
  disabled?: boolean
  variant?: 'primary' | 'ghost'
  type?: 'button' | 'submit'
  ariaLabel?: string
}

export function Button({ children, onClick, disabled, variant = 'primary', type = 'button', ariaLabel }: Props) {
  const reduce = useReducedMotion()
  const base =
    'inline-flex items-center justify-center gap-2 rounded-sm px-5 py-2.5 font-display text-xs font-semibold tracking-[0.14em] transition-colors duration-fast disabled:cursor-not-allowed disabled:opacity-45'
  const styles =
    variant === 'primary'
      ? 'bg-burgundy text-cream hover:bg-burgundy-light'
      : 'border border-strong text-ink hover:bg-cream-deep'
  return (
    <motion.button
      type={type}
      onClick={onClick}
      disabled={disabled}
      aria-label={ariaLabel}
      className={`${base} ${styles}`}
      whileHover={reduce || disabled ? undefined : { y: -1 }}
      whileTap={reduce || disabled ? undefined : { scale: 0.97 }}
      transition={{ duration: 0.14 }}
    >
      {children}
    </motion.button>
  )
}
