import type { Job } from "../api/types";

interface Props {
  job: Job;
}

const statusColor: Record<string, string> = {
  success: "#0f9d58",
  failed: "#d93025",
  skipped: "#fbbc05",
};

export default function StageHistory({ job }: Props) {
  const entries = Object.entries(job.stageHistory ?? {});
  if (entries.length === 0) {
    return <p>No stage history recorded yet.</p>;
  }

  return (
    <table className="stage-history">
      <thead>
        <tr>
          <th>Stage</th>
          <th>Status</th>
          <th>Details</th>
          <th>Updated</th>
        </tr>
      </thead>
      <tbody>
        {entries.map(([stage, info]) => {
          const color = statusColor[(info.status || "").toLowerCase()] ?? "#5f6368";
          return (
            <tr key={stage}>
              <td>{stage}</td>
              <td style={{ color }}>{info.status}</td>
              <td>
                {info.details
                  ? Object.entries(info.details)
                      .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(", ") : String(v)}`)
                      .join(" · ")
                  : "—"}
              </td>
              <td>{info.updatedAt ? new Date(info.updatedAt).toLocaleString() : "—"}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
