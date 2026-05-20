import { test } from 'node:test';
import { spawnSync } from 'node:child_process';
import path from 'node:path';

test('tsc --noEmit (whole project)', () => {
  const pkgRoot = path.resolve(import.meta.dirname, '..');
  const { status, stdout, stderr } = spawnSync(
    'npx',
    ['tsc', '--noEmit', '-p', pkgRoot],
    { encoding: 'utf8' },
  );
  if (status !== 0) {
    throw new Error(`tsc failed (exit ${status})\n${stdout}${stderr}`);
  }
});
