# Mobile Prompt (React Native)

## Objective
Build a minimal RN app to list assets, show job status, and play HLS with audio/subtitle selection.

## Features
- Upload via presigned URL (basic screen).
- Jobs list/detail (poll `/jobs/{id}`).
- Player screen using `react-native-video` with HLS source and track selection UI.

## Deliverables
- `mobile/` app with screens: `UploadScreen`, `JobsScreen`, `PlayerScreen`.
- Simple state management (Zustand/Redux) and typed API client.

## Acceptance
- Plays HLS and lets users switch audio tracks and captions.
