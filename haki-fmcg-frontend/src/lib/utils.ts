import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/** Merge Tailwind classes with clsx — use everywhere for conditional class names */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
