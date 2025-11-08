# Audio Engineering Prompt — Assembly, Mix, Packaging

## Objective
Assemble per-segment WAVs into a single dubbed track; optionally preserve music/FX; package outputs.

## Steps
1. **Concatenate** TTS segments in order (insert padding to match [t0,t1]).
2. **(Optional)** Music/FX preservation:
   - Run Demucs on original audio to split `vocals` vs `accompaniment`.
   - Mix: `accompaniment + dubbed_voice` with target loudness.
3. **Replace or Add Track**:
   - Simple replace: mux video + dubbed track (AAC 48k mono/stereo).
   - Multi-audio: generate **HLS** with `variant video` + `AUDIO` groups for each language.
4. **Subtitles**: Emit VTT/SRT per language; attach to HLS master.

## FFmpeg Hints (pseudo)
- Demux: `ffmpeg -i in.mp4 -map 0:a:0 audio.wav`
- Concat: `ffmpeg -f concat -safe 0 -i list.txt -af loudnorm=I=-16:LRA=11:TP=-1.5 out.wav`
- Replace: `ffmpeg -i in.mp4 -i out.wav -map 0:v -map 1:a -c:v copy -c:a aac -shortest out_es.mp4`
- HLS (alt audio): produce master.m3u8 with `#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="es"...`

## Acceptance
- No perceivable desync; switching audio tracks works in Video.js and RN.
