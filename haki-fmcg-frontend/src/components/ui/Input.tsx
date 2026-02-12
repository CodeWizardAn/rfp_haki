import { forwardRef, type InputHTMLAttributes, type TextareaHTMLAttributes, type ReactNode } from 'react';
import { cn } from '@/lib/utils';

// --- Text Input ---

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, leftIcon, rightIcon, className, id, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, '-');
    return (
      <div className="w-full">
        {label && (
          <label htmlFor={inputId} className="block text-caption text-muted-silver mb-1.5">
            {label}
          </label>
        )}
        <div className="relative">
          {leftIcon && (
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-silver">
              {leftIcon}
            </span>
          )}
          <input
            ref={ref}
            id={inputId}
            className={cn(
              'w-full glass-input px-3 py-2.5 text-body text-ghost-white placeholder:text-muted-silver/50',
              'transition-all duration-200',
              'focus:outline-none focus:border-electric-cyan/40 focus:shadow-[0_0_0_2px_rgba(0,212,255,0.15)]',
              leftIcon && 'pl-10',
              rightIcon && 'pr-10',
              error && 'border-coral-flame/60 focus:border-coral-flame/80 focus:shadow-[0_0_0_2px_rgba(255,71,87,0.15)]',
              className,
            )}
            {...props}
          />
          {rightIcon && (
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-silver">
              {rightIcon}
            </span>
          )}
        </div>
        {error && <p className="mt-1 text-xs text-coral-flame">{error}</p>}
        {hint && !error && <p className="mt-1 text-xs text-muted-silver">{hint}</p>}
      </div>
    );
  },
);

Input.displayName = 'Input';

// --- TextArea ---

interface TextAreaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
}

export const TextArea = forwardRef<HTMLTextAreaElement, TextAreaProps>(
  ({ label, error, className, id, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, '-');
    return (
      <div className="w-full">
        {label && (
          <label htmlFor={inputId} className="block text-caption text-muted-silver mb-1.5">
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          id={inputId}
          className={cn(
            'w-full glass-input px-3 py-2.5 text-body text-ghost-white placeholder:text-muted-silver/50 resize-y min-h-[100px]',
            'transition-all duration-200',
            'focus:outline-none focus:border-electric-cyan/40 focus:shadow-[0_0_0_2px_rgba(0,212,255,0.15)]',
            error && 'border-coral-flame/60',
            className,
          )}
          {...props}
        />
        {error && <p className="mt-1 text-xs text-coral-flame">{error}</p>}
      </div>
    );
  },
);

TextArea.displayName = 'TextArea';

// --- Select ---

interface SelectOption {
  value: string;
  label: string;
}

interface SelectProps extends Omit<InputHTMLAttributes<HTMLSelectElement>, 'onChange'> {
  label?: string;
  error?: string;
  options: SelectOption[];
  placeholder?: string;
  onChange?: (value: string) => void;
  value?: string;
}

export function Select({ label, error, options, placeholder, onChange, value, className, id }: SelectProps) {
  const selectId = id || label?.toLowerCase().replace(/\s+/g, '-');
  return (
    <div className="w-full">
      {label && (
        <label htmlFor={selectId} className="block text-caption text-muted-silver mb-1.5">
          {label}
        </label>
      )}
      <select
        id={selectId}
        value={value}
        onChange={(e) => onChange?.(e.target.value)}
        className={cn(
          'w-full glass-input px-3 py-2.5 text-body text-ghost-white appearance-none cursor-pointer',
          'transition-all duration-200',
          'focus:outline-none focus:border-electric-cyan/40 focus:shadow-[0_0_0_2px_rgba(0,212,255,0.15)]',
          'bg-[url("data:image/svg+xml,%3csvg%20xmlns=%27http://www.w3.org/2000/svg%27%20fill=%27none%27%20viewBox=%270%200%2024%2024%27%20stroke=%27%238892B0%27%20stroke-width=%272%27%3e%3cpath%20stroke-linecap=%27round%27%20stroke-linejoin=%27round%27%20d=%27M19%209l-7%207-7-7%27/%3e%3c/svg%3e")] bg-[length:18px] bg-[right_12px_center] bg-no-repeat',
          error && 'border-coral-flame/60',
          className,
        )}
      >
        {placeholder && (
          <option value="" disabled>
            {placeholder}
          </option>
        )}
        {options.map((opt) => (
          <option key={opt.value} value={opt.value} className="bg-midnight-blue text-ghost-white">
            {opt.label}
          </option>
        ))}
      </select>
      {error && <p className="mt-1 text-xs text-coral-flame">{error}</p>}
    </div>
  );
}
