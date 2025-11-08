import { useEffect, useRef } from "react";
import videojs, { VideoJsPlayer } from "video.js";
import "video.js/dist/video-js.css";

interface Props {
  src: string;
}

export default function HlsPlayer({ src }: Props) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const playerRef = useRef<VideoJsPlayer | null>(null);

  useEffect(() => {
    if (videoRef.current && !playerRef.current) {
      playerRef.current = videojs(videoRef.current, {
        controls: true,
        preload: "auto",
        sources: [
          {
            src,
            type: "application/x-mpegURL"
          }
        ]
      });
    } else if (playerRef.current) {
      playerRef.current.src({ src, type: "application/x-mpegURL" });
    }

    return () => {
      playerRef.current?.dispose();
      playerRef.current = null;
    };
  }, [src]);

  return <video ref={videoRef} className="video-js vjs-default-skin" />;
}
