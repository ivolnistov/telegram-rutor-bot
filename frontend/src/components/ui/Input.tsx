import { type ComponentProps, forwardRef } from 'react'

interface InputProps extends ComponentProps<'input'> {
  icon?: React.ReactNode
  endContent?: React.ReactNode
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className = '', icon, endContent, ...props }, ref) => {
    return (
      <div className="relative w-full">
        {icon && (
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500 pointer-events-none">
            {icon}
          </div>
        )}
        <input
          ref={ref}
          className={`
                        w-full bg-zinc-900/50 border border-zinc-800 rounded-lg
                        py-2 text-zinc-100 placeholder:text-zinc-500 text-sm
                        focus:border-violet-500 focus:ring-1 focus:ring-violet-500
                        outline-none transition-colors
                        ${icon ? 'pl-10' : 'pl-4'}
                        ${endContent ? 'pr-10' : 'pr-4'}
                        ${className}
                    `}
          {...props}
        />
        {endContent && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500">
            {endContent}
          </div>
        )}
      </div>
    )
  },
)

Input.displayName = 'Input'
