import express from "express";
import cors from "cors";
import morgan from "morgan";
import rateLimit from "express-rate-limit";
import { config } from "./config";
import { forwardRequest } from "./backendClient";

const app = express();
app.use(cors());
app.use(express.json({ limit: "25mb" }));
app.use(morgan("combined"));
app.use(
  rateLimit({
    windowMs: 60 * 1000,
    max: config.rateLimitPerMinute,
    message: "Too many requests from this IP, please try again later.",
  })
);

const prefix = "/api";

app.post(`${prefix}/upload/init`, async (req, res, next) => {
  try {
    const data = await forwardRequest({ method: "POST", url: "/upload/init", data: req.body });
    res.json(data);
  } catch (error) {
    next(error);
  }
});

app.post(`${prefix}/upload/complete`, async (req, res, next) => {
  try {
    const data = await forwardRequest({ method: "POST", url: "/upload/complete", data: req.body });
    res.json(data);
  } catch (error) {
    next(error);
  }
});

app.post(`${prefix}/jobs/translate`, async (req, res, next) => {
  try {
    const data = await forwardRequest({ method: "POST", url: "/jobs/translate", data: req.body });
    res.json(data);
  } catch (error) {
    next(error);
  }
});

app.get(`${prefix}/jobs`, async (req, res, next) => {
  try {
    const data = await forwardRequest({ method: "GET", url: "/jobs", params: req.query });
    res.json(data);
  } catch (error) {
    next(error);
  }
});

app.get(`${prefix}/jobs/:id`, async (req, res, next) => {
  try {
    const data = await forwardRequest({ method: "GET", url: `/jobs/${req.params.id}` });
    res.json(data);
  } catch (error) {
    next(error);
  }
});

app.post(`${prefix}/jobs/:id/retry`, async (req, res, next) => {
  try {
    const data = await forwardRequest({ method: "POST", url: `/jobs/${req.params.id}/retry`, data: req.body });
    res.json(data);
  } catch (error) {
    next(error);
  }
});

app.delete(`${prefix}/jobs/:id`, async (req, res, next) => {
  try {
    await forwardRequest({ method: "DELETE", url: `/jobs/${req.params.id}` });
    res.status(204).end();
  } catch (error) {
    next(error);
  }
});

app.get(`${prefix}/jobs/:id/events`, async (req, res, next) => {
  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");

  let active = true;
  const send = async () => {
    if (!active) return;
    try {
      const data = await forwardRequest({ method: "GET", url: `/jobs/${req.params.id}` });
      res.write(`data: ${JSON.stringify(data)}\n\n`);
      if (data.status === "SUCCESS" || data.status === "FAILED" || data.status === "CANCELLED") {
        res.end();
        active = false;
        return;
      }
    } catch (err) {
      res.write(`event: error\ndata: ${JSON.stringify({ error: (err as Error).message })}\n\n`);
    }
    setTimeout(send, 2000);
  };

  req.on("close", () => {
    active = false;
  });

  send().catch(next);
});

// Error handler
app.use((err: any, _req: express.Request, res: express.Response, _next: express.NextFunction) => {
  const status = err.response?.status || 500;
  const message = err.response?.data || { error: err.message };
  res.status(status).json(message);
});

if (process.env.NODE_ENV !== "test") {
  app.listen(config.port, () => {
    console.log(`Express gateway listening on port ${config.port}`);
  });
}

export default app;
