import { useEffect, useState } from 'react';

/** Delay updates until the user pauses typing (e.g. live search). */
export function useDebouncedValue(value, delayMs = 400) {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(id);
  }, [value, delayMs]);

  return debounced;
}
