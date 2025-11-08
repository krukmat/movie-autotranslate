import { BrowserRouter, Route, Routes } from "react-router-dom";
import UploadPage from "./pages/UploadPage";
import JobDetailPage from "./pages/JobDetailPage";
import WatchPage from "./pages/WatchPage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<UploadPage />} />
        <Route path="/jobs/:jobId" element={<JobDetailPage />} />
        <Route path="/watch/:assetId" element={<WatchPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
