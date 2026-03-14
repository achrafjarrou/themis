import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import UploadPage   from "./pages/UploadPage"
import AnalysisPage from "./pages/AnalysisPage"
import ReportPage   from "./pages/ReportPage"

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/"              element={<UploadPage />} />
        <Route path="/analysis/:sid" element={<AnalysisPage />} />
        <Route path="/report/:sid"   element={<ReportPage />} />
        <Route path="*"              element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}