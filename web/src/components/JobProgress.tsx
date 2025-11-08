import type { Job } from "../api/types";

interface Props {
  job: Job;
}

const stageOrder: Job["stage"][] = ["ASR", "TRANSLATE", "TTS", "ALIGN/MIX", "PACKAGE", "PUBLISHED", "DONE"];

export default function JobProgress({ job }: Props) {
  return (
    <ol className="job-progress">
      {stageOrder.map((stage) => {
        const isActive = job.stage === stage;
        const isCompleted = stageOrder.indexOf(stage) < stageOrder.indexOf(job.stage);
        return (
          <li key={stage} data-active={isActive} data-complete={isCompleted}>
            <strong>{stage}</strong>
          </li>
        );
      })}
    </ol>
  );
}
