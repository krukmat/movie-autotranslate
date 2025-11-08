import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { completeUpload, createJob, initUpload } from "../api";

const languages = [
  { value: "en", label: "English" },
  { value: "es", label: "Spanish" },
  { value: "fr", label: "French" },
  { value: "de", label: "German" }
];

export default function UploadPage() {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [targetLang, setTargetLang] = useState("es");
  const [status, setStatus] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!file) {
      setStatus("Select a media file first.");
      return;
    }

    try {
      setStatus("Requesting upload session...");
      const init = await initUpload(file.name, file.size, file.type);
      const uploadUrl = init.parts[0].uploadUrl;
      setStatus("Uploading...");
      const uploadResp = await fetch(uploadUrl, {
        method: "PUT",
        headers: {
          "Content-Type": file.type
        },
        body: await file.arrayBuffer()
      });
      if (!uploadResp.ok) {
        throw new Error("Upload failed");
      }
      const etag = uploadResp.headers.get("ETag")?.replace('"', "") ?? "demo-etag";
      setStatus("Finalizing upload...");
      await completeUpload(init.assetId, init.uploadId, "en", [targetLang], [etag]);
      setStatus("Creating job...");
      const job = await createJob(init.assetId, [targetLang], { default: "neutral" });
      navigate(`/jobs/${job.jobId}`);
    } catch (error) {
      setStatus(`Failed: ${(error as Error).message}`);
    }
  };

  return (
    <main>
      <h1>Movie AutoTranslate</h1>
      <form onSubmit={handleSubmit}>
        <label>
          Video or audio file
          <input type="file" accept="video/*,audio/*" onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
        </label>
        <label>
          Target language
          <select value={targetLang} onChange={(event) => setTargetLang(event.target.value)}>
            {languages.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <button type="submit" disabled={!file}>
          Start dubbing job
        </button>
      </form>
      {status && <p>{status}</p>}
    </main>
  );
}
