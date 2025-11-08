import { render, screen } from "@testing-library/react";
import StageHistory from "./StageHistory";
import type { Job } from "../api/types";

const jobStub: Job = {
  jobId: "job-123",
  assetId: "asset-1",
  stage: "ASR",
  status: "RUNNING",
  progress: 0.3,
  targetLangs: ["es"],
  presets: { default: "neutral" },
  stageHistory: {
    ASR: { status: "success", updatedAt: "2024-01-01T00:00:00Z" },
    TRANSLATE: { status: "running" }
  }
};

describe("StageHistory", () => {
  it("renders stage rows", () => {
    render(<StageHistory job={jobStub} />);
    expect(screen.getByText("ASR")).toBeInTheDocument();
    expect(screen.getByText("TRANSLATE")).toBeInTheDocument();
  });
});
