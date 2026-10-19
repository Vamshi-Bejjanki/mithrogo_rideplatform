/** @type {import('next').NextConfig} */
const backend = (process.env.BACKEND_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

const nextConfig = {
  reactStrictMode: true,
  // Django URLs end in "/". Keep them as they are instead of redirecting to the slash-less form.
  skipTrailingSlashRedirect: true,
  async rewrites() {
    // The browser only talks to this app; Next forwards API and media calls to Django (no CORS needed).
    return [
      // `:path*` drops the trailing slash, and every Django API URL ends in one, so add it back.
      { source: "/api/v1/:path*", destination: `${backend}/api/v1/:path*/` },
      { source: "/media/:path*", destination: `${backend}/media/:path*` },
    ];
  },
};

export default nextConfig;
