import React, { useState } from 'react'
import { twMerge } from 'tailwind-merge'

interface TooltipProps {
  content: React.ReactNode
  children: React.ReactNode
  className?: string
  delay?: number
}

export const Tooltip = ({
  content,
  children,
  className,
  delay = 200,
}: TooltipProps) => {
  const [isVisible, setIsVisible] = useState(false)
  const [timeoutId, setTimeoutId] = useState<ReturnType<
    typeof setTimeout
  > | null>(null)

  const handleMouseEnter = () => {
    const id = setTimeout(() => {
      setIsVisible(true)
    }, delay)
    setTimeoutId(id)
  }

  const handleMouseLeave = () => {
    if (timeoutId) clearTimeout(timeoutId)
    setIsVisible(false)
  }

  return (
    <div
      className="relative inline-flex"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {children}
      {isVisible && (
        <div
          className={twMerge(
            'absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2.5 py-1 text-xs font-medium text-white bg-zinc-900 border border-zinc-800 rounded shadow-xl whitespace-nowrap z-50 pointer-events-none animate-in fade-in zoom-in-95 duration-200',
            className,
          )}
        >
          {content}
          <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-px size-2  bg-zinc-900 border-r border-b border-zinc-800 rotate-45" />
        </div>
      )}
    </div>
  )
}
