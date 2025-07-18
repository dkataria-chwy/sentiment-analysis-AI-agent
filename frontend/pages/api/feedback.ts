// @ts-ignore
import { createProxyMiddleware } from 'http-proxy-middleware';

export const config = {
  api: {
    bodyParser: false,
    externalResolver: true,
  },
};

const proxy = createProxyMiddleware({
  target: 'http://localhost:8000', // FastAPI backend
  changeOrigin: true,
  pathRewrite: { '^/api/feedback': '/api/feedback' },
});

export default function handler(req: any, res: any) {
  return proxy(req, res, (result: any) => {
    if (result instanceof Error) {
      throw result;
    }
    return result;
  });
} 