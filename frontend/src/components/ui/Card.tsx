import { type ReactNode } from 'react'

interface CardProps {
  children: ReactNode
  className?: string
  onClick?: () => void
}

export const Card = ({ children, className = '', onClick }: CardProps) => {
  const Component = onClick ? 'button' : 'div'

  return (
    <Component
      onClick={onClick}
      type={onClick ? 'button' : undefined}
      onKeyDown={
        onClick
          ? (e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault()
                onClick()
              }
            }
          : undefined
      }
      className={`
                bg-zinc-900/30 border border-zinc-800/80 rounded-xl p-5
                transition-all duration-200 text-left
                ${onClick ? 'cursor-pointer hover:bg-zinc-900/50 hover:border-violet-500/30' : ''}
                ${className}
            `}
    >
      {children}
    </Component>
  )
}
