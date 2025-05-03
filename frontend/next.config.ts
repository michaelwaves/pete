import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  experimental: {
    serverComponentsExternalPackages: ['child_process', 'util', 'path'],
  },
  webpack: (config) => {
    config.externals = [...(config.externals || []), 'child_process', 'util', 'path'];
    return config;
  },
};

export default nextConfig;
