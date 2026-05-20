// Browser-side globals exposed by capture.mjs via CDP `Runtime.addBinding`.
// Tests evaluate page-side code that references these.
declare global {
  interface Window {
    harBrowseMark: (payload: string) => Promise<unknown>;
  }
}

export {};
