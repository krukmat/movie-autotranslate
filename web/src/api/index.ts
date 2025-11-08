import client from "./client";
import type { Asset, Job } from "./types";

export async function initUpload(filename: string, size: number, contentType: string) {
  const { data } = await client.post("/upload/init", {
    filename,
    size,
    contentType
  });
  return data as {
    assetId: string;
    uploadId: string;
    parts: { partNumber: number; uploadUrl: string }[];
    partSize: number;
  };
}

export async function completeUpload(
  assetId: string,
  uploadId: string,
  srcLang: string,
  targetLangs: string[],
  etags: string[]
) {
  await client.post("/upload/complete", {
    assetId,
    uploadId,
    srcLang,
    targetLangs,
    etags
  });
}

export async function createJob(assetId: string, targetLangs: string[], presets: Record<string, string>) {
  const { data } = await client.post("/jobs/translate", {
    assetId,
    targetLangs,
    presets
  });
  return data as Job;
}

export async function fetchJob(jobId: string) {
  const { data } = await client.get(`/jobs/${jobId}`);
  return data as Job;
}

export async function fetchAsset(assetId: string) {
  const { data } = await client.get(`/assets/${assetId}`);
  return data as Asset;
}
