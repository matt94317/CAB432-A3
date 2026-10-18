import { Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute from "@/auth/ProtectedRoute";
import PublicOnlyRoute from "@/auth/PublicOnlyRoute";
import AppLayout from "@/components/layout/AppLayout";
import ConfirmSignUpPage from "@/features/auth/pages/ConfirmSignUpPage";
import LoginPage from "@/features/auth/pages/LoginPage";
import SignUpPage from "@/features/auth/pages/SignUpPage";
import CampaignListPage from "@/features/campaigns/pages/CampaignListPage";
import CreatorDetailPage from "@/features/creators/pages/CreatorDetailPage";
import CreatorListPage from "@/features/creators/pages/CreatorListPage";
import CampaignDashboardPage from "@/features/dashboard/pages/CampaignDashboardPage";
import OverviewPage from "@/features/overview/pages/OverviewPage";

export default function App() {
  return (
    <Routes>
      <Route element={<PublicOnlyRoute />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignUpPage />} />
        <Route path="/confirm" element={<ConfirmSignUpPage />} />
      </Route>
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route index element={<Navigate to="/overview" replace />} />
          <Route path="/overview" element={<OverviewPage />} />
          <Route path="/campaigns" element={<CampaignListPage />} />
          <Route path="/campaigns/:campaignId" element={<CampaignDashboardPage />} />
          <Route path="/creators" element={<CreatorListPage />} />
          <Route path="/creators/:creatorId" element={<CreatorDetailPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
