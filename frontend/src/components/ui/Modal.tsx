import { X } from "lucide-react";
import { type ReactNode, useEffect } from "react";
import { createPortal } from "react-dom";

interface ModalProps {
  isOpen?: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  className?: string;
}

export const Modal = ({
  isOpen = true,
  onClose,
  title,
  children,
  className = "",
}: ModalProps) => {
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("keydown", handleEscape);
    };
  }, [onClose]);

  if (!isOpen) return null;

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="absolute inset-0" onClick={onClose} />
      <div
        className={`
                    bg-zinc-900 border border-zinc-700 rounded-2xl w-full max-w-lg p-6
                    shadow-2xl scale-100 animate-in zoom-in-95 duration-200 relative z-10
                    max-h-[85vh] overflow-y-auto custom-scrollbar
                    ${className}
                `}
        onClick={(e) => {
          e.stopPropagation();
        }}
      >
        {title && (
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-bold text-zinc-100">{title}</h3>
            <button
              onClick={onClose}
              className="text-zinc-500 hover:text-zinc-300 transition-colors p-1"
            >
              <X className="size-5 " />
            </button>
          </div>
        )}
        {children}
      </div>
    </div>,
    document.body,
  );
};
