import { Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute from "@/auth/ProtectedRoute";
import AppLayout from "@/components/layout/AppLayout";
import LoginPage from "@/features/auth/pages/LoginPage";
import SignUpPage from "@/features/auth/pages/SignUpPage";
import CampaignListPage from "@/features/campaigns/pages/CampaignListPage";
import CreatorDetailPage from "@/features/creators/pages/CreatorDetailPage";
import CreatorListPage from "@/features/creators/pages/CreatorListPage";
import CampaignDashboardPage from "@/features/dashboard/pages/CampaignDashboardPage";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignUpPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route index element={<Navigate to="/campaigns" replace />} />
          <Route path="/campaigns" element={<CampaignListPage />} />
          <Route path="/campaigns/:campaignId" element={<CampaignDashboardPage />} />
          <Route path="/creators" element={<CreatorListPage />} />
          <Route path="/creators/:creatorId" element={<CreatorDetailPage />} />
        </Route>
      </Route>
    </Routes>
  );
}
