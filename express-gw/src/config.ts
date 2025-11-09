import dotenv from "dotenv";

dotenv.config();

export const config = {
  backendBaseUrl: process.env.BACKEND_BASE_URL ?? "http://localhost:8000/v1",
  backendApiKey: process.env.BACKEND_API_KEY ?? "",
  port: Number(process.env.PORT ?? 4000),
  rateLimitPerMinute: Number(process.env.GATEWAY_RATE_LIMIT_PER_MINUTE ?? 120),
  apiKeyHeader: process.env.API_KEY_HEADER ?? "X-API-Key",
};
