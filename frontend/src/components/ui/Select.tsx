import { useState, useRef, useEffect } from 'react'
import { ChevronDown, Check } from 'lucide-react'
import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export interface SelectOption {
  value: string | number
  label: string
  icon?: React.ReactNode
}

interface SelectProps {
  value?: string | number
  onChange: (value: string | number) => void
  options: SelectOption[]
  placeholder?: string
  className?: string
  startIcon?: React.ReactNode
  disabled?: boolean
}

export const Select = ({
  value,
  onChange,
  options,
  placeholder = 'Select...',
  className,
  startIcon,
  disabled,
}: SelectProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  const selectedOption = options.find(
    (opt) => String(opt.value) === String(value),
  )

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [])

  return (
    <div className={twMerge('relative w-full', className)} ref={containerRef}>
      <button
        type="button"
        disabled={disabled}
        onClick={() => {
          if (!disabled) setIsOpen(!isOpen)
        }}
        className={clsx(
          'w-full flex items-center justify-between bg-zinc-900/50 border border-zinc-800 rounded-lg py-2 px-3 text-sm text-left transition-all',
          !disabled &&
            'hover:border-zinc-700 hover:bg-zinc-900/80 focus:outline-none focus:ring-1 focus:ring-violet-500 focus:border-violet-500',
          isOpen && 'border-violet-500 ring-1 ring-violet-500',
          disabled && 'opacity-50 cursor-not-allowed',
        )}
      >
        <span
          className={clsx(
            'flex items-center gap-2 truncate',
            !selectedOption && 'text-zinc-500',
          )}
        >
          {selectedOption?.icon || startIcon}
          {selectedOption ? selectedOption.label : placeholder}
        </span>
        <ChevronDown
          className={clsx(
            'size-4  text-zinc-500 transition-transform',
            isOpen && 'rotate-180',
          )}
        />
      </button>

      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-zinc-900 border border-zinc-800 rounded-lg shadow-xl max-h-60 overflow-y-auto animate-in fade-in zoom-in-95 duration-100">
          <div className="p-1">
            {options.map((option) => {
              const isSelected = String(option.value) === String(value)
              return (
                <button
                  key={option.value}
                  type="button"
                  onClick={(e) => {
                    e.preventDefault()
                    e.stopPropagation()
                    onChange(option.value)
                    setIsOpen(false)
                  }}
                  className={clsx(
                    'w-full flex items-center justify-between px-3 py-2 text-sm rounded-md transition-colors',
                    isSelected
                      ? 'bg-violet-500/10 text-violet-400'
                      : 'text-zinc-300 hover:bg-zinc-800 hover:text-white',
                  )}
                >
                  <span className="flex items-center gap-2 truncate">
                    {option.icon}
                    {option.label}
                  </span>
                  {isSelected && <Check className="size-3.5 " />}
                </button>
              )
            })}
            {options.length === 0 && (
              <div className="px-3 py-2 text-xs text-zinc-500 text-center italic">
                No options available
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
