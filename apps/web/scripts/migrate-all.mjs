import 'dotenv/config';
import { spawnSync } from 'node:child_process';

const localUrl = process.env.LOCAL_DATABASE_URL;
const remoteUrl = process.env.DATABASE_URL;

if (!remoteUrl) {
  console.error('DATABASE_URL is required for remote migrations.');
  process.exit(1);
}

if (!localUrl) {
  console.error('LOCAL_DATABASE_URL is required for local migrations.');
  process.exit(1);
}

const migrate = (url, label) => {
  console.log(`Running migrations for ${label}...`);
  const result = spawnSync('bunx', ['drizzle-kit', 'migrate'], {
    stdio: 'inherit',
    env: { ...process.env, DATABASE_URL: url }
  });
  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
};

migrate(remoteUrl, 'remote');
migrate(localUrl, 'local');
