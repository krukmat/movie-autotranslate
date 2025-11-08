import axios from "axios";

const client = axios.create({
  baseURL: "http://localhost:8000/v1",
  timeout: 15000
});

export interface Job {
  jobId: string;
  assetId: string;
  stage: string;
  status: string;
  progress: number;
}

export interface Asset {
  assetId: string;
  outputs: Record<string, string>;
}

export async function fetchJobs(): Promise<Job[]> {
  const { data } = await client.get("/jobs");
  return data as Job[];
}

export async function fetchJob(jobId: string): Promise<Job> {
  const { data } = await client.get(`/jobs/${jobId}`);
  return data as Job;
}

export async function fetchAsset(assetId: string): Promise<Asset> {
  const { data } = await client.get(`/assets/${assetId}`);
  return data as Asset;
}
