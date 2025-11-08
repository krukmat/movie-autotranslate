import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { fetchAsset } from "../api";
import type { Asset } from "../api/types";
import HlsPlayer from "../components/HlsPlayer";

export default function WatchPage() {
  const { assetId } = useParams<{ assetId: string }>();
  const [asset, setAsset] = useState<Asset | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!assetId) {
      return;
    }
    fetchAsset(assetId)
      .then((data) => setAsset(data))
      .catch((err) => setError((err as Error).message));
  }, [assetId]);

  if (!assetId) {
    return <p>Missing asset id.</p>;
  }
  if (error) {
    return <p>Error: {error}</p>;
  }
  if (!asset) {
    return <p>Loading asset...</p>;
  }

  const publishedTracks = useMemo(() => {
    return Object.entries(asset.storageKeys)
      .filter(([key]) => key.startsWith("public_"))
      .map(([key, value]) => ({
        language: key.replace("public_", ""),
        url: value
      }));
  }, [asset.storageKeys]);

  const masterUrl = asset.outputs.hls || asset.storageKeys.public;
  const [selectedTrack, setSelectedTrack] = useState(masterUrl || "");
  useEffect(() => {
    setSelectedTrack(masterUrl || "");
  }, [masterUrl]);

  if (!masterUrl) {
    return <p>No published HLS manifest yet. Check back later.</p>;
  }

  return (
    <main>
      <h1>Playback</h1>
      {publishedTracks.length > 0 && (
        <label>
          Audio track
          <select value={selectedTrack} onChange={(event) => setSelectedTrack(event.target.value)}>
            <option value={masterUrl}>Master (auto)</option>
            {publishedTracks.map((track) => (
              <option key={track.language} value={track.url}>
                {track.language.toUpperCase()}
              </option>
            ))}
          </select>
        </label>
      )}
      <HlsPlayer src={selectedTrack || masterUrl} />
      {publishedTracks.length > 0 && (
        <section>
          <h2>Available outputs</h2>
          <ul>
            {publishedTracks.map((track) => (
              <li key={track.language}>
                {track.language.toUpperCase()}: <code>{track.url}</code>
              </li>
            ))}
          </ul>
        </section>
      )}
    </main>
  );
}
