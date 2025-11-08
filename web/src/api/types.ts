export type JobStage =
  | "INGESTED"
  | "ASR"
  | "TRANSLATE"
  | "TTS"
  | "ALIGN/MIX"
  | "PACKAGE"
  | "PUBLISHED"
  | "DONE";

export type JobStatus = "PENDING" | "RUNNING" | "SUCCESS" | "FAILED";

export interface Job {
  jobId: string;
  assetId: string;
  stage: JobStage;
  status: JobStatus;
  progress: number;
  startedAt?: string;
  endedAt?: string;
  failedStage?: JobStage;
  errorMessage?: string;
  targetLangs: string[];
  presets: Record<string, string>;
}

export interface Asset {
  assetId: string;
  srcLang?: string;
  targetLangs: string[];
  outputs: Record<string, string>;
  storageKeys: {
    raw?: string;
    processed?: string;
    public?: string;
  };
}
