import { Check } from "lucide-react";
import * as React from "react";
export interface CheckboxProps extends Omit<
  React.InputHTMLAttributes<HTMLInputElement>,
  "onChange"
> {
  checked?: boolean;
  onCheckedChange?: (checked: boolean) => void;
}

const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>(
  ({ className, checked, onCheckedChange, disabled, ...props }, ref) => {
    return (
      <label className="relative flex items-center justify-center">
        <input
          type="checkbox"
          className="peer sr-only"
          ref={ref}
          checked={checked}
          disabled={disabled}
          onChange={(e) => onCheckedChange?.(e.target.checked)}
          {...props}
        />
        <div
          className={[
            "flex size-4 shrink-0 items-center justify-center rounded-sm border border-zinc-600 bg-transparent shadow-sm transition-colors cursor-pointer",
            "peer-focus-visible:outline-none peer-focus-visible:ring-1 peer-focus-visible:ring-violet-500",
            "peer-disabled:cursor-not-allowed peer-disabled:opacity-50",
            "peer-checked:bg-violet-600 peer-checked:text-white peer-checked:border-violet-600",
            className,
          ]
            .filter(Boolean)
            .join(" ")}
        >
          {checked && <Check className="size-3" strokeWidth={3} />}
        </div>
      </label>
    );
  },
);
Checkbox.displayName = "Checkbox";

export { Checkbox };
