import { useEffect, useState } from "react";
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

  const masterUrl = asset.outputs.hls || asset.storageKeys.public;

  if (!masterUrl) {
    return <p>No published HLS manifest yet. Check back later.</p>;
  }

  return (
    <main>
      <h1>Playback</h1>
      <HlsPlayer src={masterUrl} />
    </main>
  );
}
