import { type ReactNode } from 'react'

interface CardProps {
  children: ReactNode
  className?: string
  onClick?: () => void
}

export const Card = ({ children, className = '', onClick }: CardProps) => {
  return (
    <div
      onClick={onClick}
      className={`
                bg-zinc-900/30 border border-zinc-800/80 rounded-xl p-5
                transition-all duration-200
                ${onClick ? 'cursor-pointer hover:bg-zinc-900/50 hover:border-violet-500/30' : ''}
                ${className}
            `}
    >
      {children}
    </div>
  )
}
