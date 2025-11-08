import { FormEvent, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { completeUpload, createJob, initUpload } from "../api";

const languages = [
  { value: "en", label: "English" },
  { value: "es", label: "Spanish" },
  { value: "fr", label: "French" },
  { value: "de", label: "German" }
];

const voicePresets = [
  { value: "neutral", label: "Neutral" },
  { value: "female_bright", label: "Female Bright" },
  { value: "male_deep", label: "Male Deep" },
  { value: "elderly_female", label: "Elderly Female" },
  { value: "elderly_male", label: "Elderly Male" }
];

export default function UploadPage() {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [targetLangs, setTargetLangs] = useState<string[]>(["es"]);
  const [defaultPreset, setDefaultPreset] = useState("neutral");
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const isSubmitDisabled = useMemo(() => {
    return !file || targetLangs.length === 0;
  }, [file, targetLangs]);

  const toggleLanguage = (value: string) => {
    setTargetLangs((prev) => (prev.includes(value) ? prev.filter((lang) => lang !== value) : [...prev, value]));
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!file) {
      setError("Select a media file first.");
      return;
    }
    if (targetLangs.length === 0) {
      setError("Select at least one target language.");
      return;
    }
    setError(null);

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
      const etag = uploadResp.headers.get("ETag")?.replace(/"/g, "") ?? "demo-etag";
      setStatus("Finalizing upload...");
      await completeUpload(init.assetId, init.uploadId, "en", targetLangs, [etag]);
      setStatus("Creating job...");
      const job = await createJob(init.assetId, targetLangs, { default: defaultPreset });
      navigate(`/jobs/${job.jobId}`);
    } catch (err) {
      setStatus(null);
      setError((err as Error).message);
    }
  };

  return (
    <main>
      <h1>Movie AutoTranslate</h1>
      <form onSubmit={handleSubmit} className="upload-form">
        <label>
          Video or audio file
          <input type="file" accept="video/*,audio/*" onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
        </label>
        <fieldset>
          <legend>Target languages</legend>
          {languages.map((option) => (
            <label key={option.value} className="checkbox">
              <input
                type="checkbox"
                value={option.value}
                checked={targetLangs.includes(option.value)}
                onChange={() => toggleLanguage(option.value)}
              />
              {option.label}
            </label>
          ))}
          <p className="hint">Select one or more target languages. English is assumed as the source language for now.</p>
        </fieldset>
        <label>
          Voice preset
          <select value={defaultPreset} onChange={(event) => setDefaultPreset(event.target.value)}>
            {voicePresets.map((preset) => (
              <option key={preset.value} value={preset.value}>
                {preset.label}
              </option>
            ))}
          </select>
        </label>
        <button type="submit" disabled={isSubmitDisabled}>
          Start dubbing job
        </button>
      </form>
      {status && <p>{status}</p>}
      {error && <p className="error">{error}</p>}
    </main>
  );
}
