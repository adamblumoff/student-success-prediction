const path = require('node:path');

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  outputFileTracingRoot: path.join(__dirname, '../..'),
  experimental: {
    serverActions: {
      bodySizeLimit: '50mb'
    }
  }
};

module.exports = nextConfig;
