import axios from "axios";

const client = axios.create({
  baseURL: "http://localhost:8000/v1",
  timeout: 15000
});

export interface StageHistoryEntry {
  status: string;
  details?: Record<string, unknown>;
  updatedAt?: string;
}

export interface Job {
  jobId: string;
  assetId: string;
  stage: string;
  status: string;
  progress: number;
  failedStage?: string;
  errorMessage?: string;
  targetLangs: string[];
  presets: Record<string, string>;
  stageHistory?: Record<string, StageHistoryEntry>;
  logsKey?: string;
}

export interface Asset {
  assetId: string;
  outputs: Record<string, string>;
  storageKeys: Record<string, string>;
}

export interface UploadInitResponse {
  assetId: string;
  uploadId: string;
  parts: { partNumber: number; uploadUrl: string }[];
  partSize: number;
}

export interface JobListResponse {
  items: Job[];
  total: number;
  page: number;
  pageSize: number;
}

export async function fetchJobs(page = 1, pageSize = 20): Promise<JobListResponse> {
  const { data } = await client.get("/jobs", { params: { page, pageSize } });
  return data as JobListResponse;
}

export async function fetchJob(jobId: string): Promise<Job> {
  const { data } = await client.get(`/jobs/${jobId}`);
  return data as Job;
}

export async function fetchAsset(assetId: string): Promise<Asset> {
  const { data } = await client.get(`/assets/${assetId}`);
  return data as Asset;
}

export async function initUpload(filename: string, size: number, contentType: string): Promise<UploadInitResponse> {
  const { data } = await client.post("/upload/init", { filename, size, contentType });
  return data as UploadInitResponse;
}

export async function completeUpload(
  assetId: string,
  uploadId: string,
  srcLang: string,
  targetLangs: string[],
  etags: string[]
): Promise<void> {
  await client.post("/upload/complete", { assetId, uploadId, srcLang, targetLangs, etags });
}

export async function createJob(assetId: string, targetLangs: string[], presets: Record<string, string>): Promise<Job> {
  const { data } = await client.post("/jobs/translate", { assetId, targetLangs, presets });
  return data as Job;
}

export async function retryJob(jobId: string, resumeFrom?: string): Promise<Job> {
  const { data } = await client.post(`/jobs/${jobId}/retry`, resumeFrom ? { resumeFrom } : {});
  return data as Job;
}
