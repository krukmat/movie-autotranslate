import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchJob } from "../api";
import type { Job } from "../api/types";
import JobProgress from "../components/JobProgress";
import StageHistory from "../components/StageHistory";

export default function JobDetailPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const [job, setJob] = useState<Job | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) {
      return;
    }
    let isMounted = true;
    const interval = setInterval(async () => {
      try {
        const data = await fetchJob(jobId);
        if (isMounted) {
          setJob(data);
          if (data.status === "SUCCESS" || data.status === "FAILED") {
            clearInterval(interval);
          }
        }
      } catch (err) {
        setError((err as Error).message);
        clearInterval(interval);
      }
    }, 2000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [jobId]);

  if (!jobId) {
    return <p>Missing job id.</p>;
  }

  if (error) {
    return <p>Error: {error}</p>;
  }

  if (!job) {
    return <p>Loading job...</p>;
  }

  return (
    <main>
      <h1>Job {job.jobId}</h1>
      <JobProgress job={job} />
      <p>Status: {job.status}</p>
      <section>
        <h2>Stage history</h2>
        <StageHistory job={job} />
      </section>
      {job.logsKey && (
        <section>
          <h2>Logs</h2>
          <p>
            Logs stored at <code>{job.logsKey}</code> (download via MinIO or the ops panel).
          </p>
        </section>
      )}
      <section>
        <h2>Targets & Preset</h2>
        <p>Languages: {job.targetLangs.join(", ")}</p>
        <p>Preset: {job.presets?.default ?? "neutral"}</p>
      </section>
      {job.status === "SUCCESS" && <Link to={`/watch/${job.assetId}`}>Open player</Link>}
    </main>
  );
}
