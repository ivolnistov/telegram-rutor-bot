import { type ComponentProps, type ReactNode } from 'react'

interface ButtonProps extends ComponentProps<'button'> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost' | 'icon' | 'outline'
  size?: 'sm' | 'md' | 'lg' | 'icon'
  isLoading?: boolean
  children: ReactNode
}

export const Button = ({
  variant = 'primary',
  size = 'md',
  isLoading = false,
  className = '',
  children,
  disabled,
  ...props
}: ButtonProps) => {
  const baseStyles =
    'font-medium transition-colors flex items-center justify-center gap-2 rounded-lg outline-none focus:ring-2 focus:ring-offset-1 focus:ring-offset-zinc-950 disabled:opacity-50 disabled:cursor-not-allowed'

  const variants = {
    primary:
      'bg-violet-600 hover:bg-violet-700 text-white focus:ring-violet-500',
    secondary:
      'bg-zinc-800 hover:bg-zinc-700 text-zinc-200 focus:ring-zinc-500',
    danger: 'bg-red-600 hover:bg-red-700 text-white focus:ring-red-500',
    ghost: 'hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200',
    icon: 'hover:bg-zinc-800 text-zinc-500 hover:text-zinc-300',
    outline:
      'border border-zinc-700 hover:bg-zinc-800 text-zinc-300 focus:ring-zinc-500',
  }

  const sizes = {
    sm: 'px-3 py-1.5 text-xs',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base',
    icon: 'p-2',
  }

  const classes = [baseStyles, variants[variant], sizes[size], className]
    .filter(Boolean)
    .join(' ')

  return (
    <button className={classes} disabled={isLoading || disabled} {...props}>
      {isLoading && <span className="animate-spin mr-2">⟳</span>}
      {children}
    </button>
  )
}
