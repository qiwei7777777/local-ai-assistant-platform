import { createServer } from "http";
import { parse } from "url";
import next from "next";
import { createProxyMiddleware } from "http-proxy-middleware";

const dev = process.env.NODE_ENV !== "production";
const hostname = "0.0.0.0";
const port = 3000;
const backendTarget =
  process.env.BACKEND_PROXY_TARGET?.trim() || "http://127.0.0.1:8000";

const app = next({ dev, hostname, port });
const handle = app.getRequestHandler();

app.prepare().then(() => {
  const proxy = createProxyMiddleware({
    target: backendTarget,
    changeOrigin: true,
    proxyTimeout: 300_000,
    timeout: 300_000,
    pathFilter: ["/api/**"],
  });

  createServer((req, res) => {
    const parsedUrl = parse(req.url!, true);
    if (parsedUrl.pathname?.startsWith("/api/")) {
      proxy(req, res);
    } else {
      handle(req, res, parsedUrl);
    }
  }).listen(port, hostname, () => {
    console.log(`> Ready on http://${hostname}:${port}`);
  });
});
