// Module shims for runtime dependencies that ship without TypeScript
// declarations. Each declaration narrows the exports we actually use; the
// rest stays `any`. Tighten further as new usages appear.

declare module "chrome-har" {
  /**
   * Build a HAR 1.2 log from CDP `{method, params}` events.
   * https://github.com/sitespeedio/chrome-har
   */
  export function harFromMessages(
    messages: ReadonlyArray<{ method: string; params?: any }>,
    options?: { includeTextFromResponseBody?: boolean },
  ): Promise<any>;
}
