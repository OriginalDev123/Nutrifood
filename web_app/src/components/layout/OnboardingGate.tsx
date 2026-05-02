import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import { isOnboardingPending } from '../../lib/onboardingStorage';

/** Chặn truy cập app chính khi vừa đăng ký và chưa hoàn tất onboarding. */
export function OnboardingGate() {
  const { user } = useAuthStore();

  if (user && !user.is_admin && isOnboardingPending()) {
    return <Navigate to="/onboarding" replace />;
  }

  return <Outlet />;
}
