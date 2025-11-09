import axios from "axios";
import type { AxiosRequestConfig } from "axios";
import { config } from "./config";

const client = axios.create({
  baseURL: config.backendBaseUrl,
  timeout: 15000,
});

export async function forwardRequest<T = unknown>(options: AxiosRequestConfig): Promise<T> {
  const headers = {
    ...options.headers,
  };
  if (config.backendApiKey) {
    headers[config.apiKeyHeader] = config.backendApiKey;
  }
  const response = await client.request<T>({ ...options, headers });
  return response.data;
}
