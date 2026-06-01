import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/** Merge Tailwind classes with clsx — use everywhere for conditional class names */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Returns the correct display price and unit label for a product.
 * Pass price_unit from the API ('m' | '90m' | '100m' | '180m' | '200m' etc.).
 * price_per_meter always stores the listing price (coil or per-meter).
 */
export function formatProductPrice(
  price_per_meter: number | null | undefined,
  price_per_100m: number | null | undefined,
  price_unit?: string | null
): { value: number; unit: string } | null {
  if (price_per_meter != null && price_per_meter > 0) {
    const suffix = price_unit && price_unit !== 'm' ? `/${price_unit}` : '/m';
    return { value: price_per_meter, unit: suffix };
  }
  // legacy fallback: no price_per_meter but has price_per_100m
  if (price_per_100m != null && price_per_100m > 0) {
    return { value: price_per_100m, unit: '/100m' };
  }
  return null;
}
