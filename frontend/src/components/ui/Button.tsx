import { motion, useReducedMotion } from 'framer-motion'
import type { ReactNode } from 'react'

interface Props {
  children: ReactNode
  onClick?: () => void
  disabled?: boolean
  variant?: 'primary' | 'ghost'
  size?: 'sm' | 'md'
  type?: 'button' | 'submit'
  ariaLabel?: string
  title?: string
  full?: boolean
}

export function Button({
  children,
  onClick,
  disabled,
  variant = 'primary',
  size = 'md',
  type = 'button',
  ariaLabel,
  title,
  full,
}: Props) {
  const reduce = useReducedMotion()
  const base =
    'inline-flex items-center justify-center gap-2 rounded-sm font-display font-semibold tracking-[0.1em] transition-colors duration-fast disabled:cursor-not-allowed disabled:opacity-45'
  const sizing =
    size === 'sm'
      ? 'px-3.5 py-2 text-[0.6875rem]'
      : 'px-5 py-2.5 text-xs'
  const styles =
    variant === 'primary'
      ? 'bg-burgundy text-on-accent hover:bg-burgundy-light'
      : 'border border-strong bg-surface text-fg hover:bg-raised'
  return (
    <motion.button
      type={type}
      onClick={onClick}
      disabled={disabled}
      aria-label={ariaLabel}
      title={title}
      className={`${base} ${sizing} ${styles} ${full ? 'w-full' : ''}`}
      whileHover={reduce || disabled ? undefined : { y: -1 }}
      whileTap={reduce || disabled ? undefined : { scale: 0.98 }}
      transition={{ duration: 0.14 }}
    >
      {children}
    </motion.button>
  )
}
