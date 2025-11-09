# Mobile App Workflow

## Upload
- Tap “Select File” to choose a video/audio asset via the native document picker. Files upload directly to the `/upload/init` presigned URL using `expo-file-system`.
- Choose one or more target languages and a default voice preset before submitting. Errors surface inline (missing file or languages).
- After the job is created the app navigates back to the Jobs tab so you can monitor progress.

## Jobs
- The Jobs screen polls `/jobs` and shows stage/status/progress for each job. Failed jobs can be retried via the “Retry” button (uses `/jobs/{id}/retry`).
- Pull-to-refresh is available to sync status updates manually.

## Playback
- The Player screen fetches asset metadata and lists any published audio tracks (`public_<lang>`). Users can switch between tracks or the master manifest before watching in `react-native-video`.

## TODOs
- Add chunked uploads for very large files (current flow pushes the full binary via `FileSystem.uploadAsync`).
- Surface logs/stage history details similar to the web app once the API exposes them via mobile-friendly endpoints.
