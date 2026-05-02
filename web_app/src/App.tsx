import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAuthStore } from './stores/authStore';
import { ToastProvider } from './components/ui/Toast';
import { AppLayout, ProtectedRoute, OnboardingGate } from './components/layout';
import OnboardingPage from './pages/Onboarding';
import { isOnboardingPending } from './lib/onboardingStorage';

// Pages - Auth
import { LoginPage, RegisterPage } from './pages/Auth';

// Pages - Main
import DashboardPage from './pages/Dashboard';
import FoodLogPage from './pages/FoodLog';
import FoodsPage from './pages/Foods';
import FoodDetailPage from './pages/Foods/FoodDetail';
import RecipesPage from './pages/Recipes';
import RecipeDetailPage from './pages/Recipes/RecipeDetail';
import CreateRecipePage from './pages/Recipes/CreateRecipe';
import MealPlanListPage from './pages/MealPlan';
import GenerateMealPlanPage from './pages/MealPlan/GenerateMealPlan';
import MealPlanDetailPage from './pages/MealPlan/MealPlanDetail';
import AnalyticsPage from './pages/Analytics';
import GoalsPage from './pages/Goals';
import ProfilePage from './pages/Profile';
import SettingsPage from './pages/Profile/Settings';

// Pages - Admin (separate layout)
import {
  AdminLayout,
  AdminDashboard,
  AdminUsers,
  AdminFoods,
  AdminRecipes,
  AdminMealPlans,
} from './pages/Admin';

const queryClient = new QueryClient();

// Helper component to redirect based on user type
function HomeRedirect() {
  const { isAuthenticated, user } = useAuthStore();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Admin users go to admin dashboard
  if (user?.is_admin) {
    return <Navigate to="/admin/dashboard" replace />;
  }

  // Regular users go to user dashboard
  return <Navigate to="/dashboard" replace />;
}

function App() {
  const { isAuthenticated, fetchUser, isInitializing, user } = useAuthStore();

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  if (isInitializing) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="flex flex-col items-center gap-4">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary border-t-transparent" />
          <p className="text-gray-500">Đang tải...</p>
        </div>
      </div>
    );
  }

  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <BrowserRouter>
          <Routes>
            {/* Public Routes */}
            <Route
              path="/login"
              element={
                isAuthenticated ? (
                  user?.is_admin ? (
                    <Navigate to="/admin/dashboard" replace />
                  ) : (
                    <Navigate to={isOnboardingPending() ? '/onboarding' : '/dashboard'} replace />
                  )
                ) : (
                  <LoginPage />
                )
              }
            />
            <Route
              path="/register"
              element={
                isAuthenticated ? (
                  <Navigate to={isOnboardingPending() ? '/onboarding' : '/dashboard'} replace />
                ) : (
                  <RegisterPage />
                )
              }
            />

            <Route
              path="/onboarding"
              element={
                <ProtectedRoute>
                  <OnboardingPage />
                </ProtectedRoute>
              }
            />

            {/* Protected Routes - User Dashboard */}
            <Route
              element={
                <ProtectedRoute>
                  <OnboardingGate />
                </ProtectedRoute>
              }
            >
              <Route element={<AppLayout isAdmin={false} />}>
              {/* Home */}
              <Route path="/" element={<HomeRedirect />} />
              <Route path="/dashboard" element={<DashboardPage />} />

              {/* Food Log */}
              <Route path="/food-log" element={<FoodLogPage />} />

              {/* Foods */}
              <Route path="/foods" element={<FoodsPage />} />
              <Route path="/foods/:id" element={<FoodDetailPage />} />

              {/* Recipes */}
              <Route path="/recipes" element={<RecipesPage />} />
              <Route path="/recipes/new" element={<CreateRecipePage />} />
              <Route path="/recipes/:id" element={<RecipeDetailPage />} />

              {/* Meal Plans */}
              <Route path="/meal-plans" element={<MealPlanListPage />} />
              <Route path="/meal-plans/new" element={<GenerateMealPlanPage />} />
              <Route path="/meal-plans/:id" element={<MealPlanDetailPage />} />

              {/* Analytics */}
              <Route path="/analytics" element={<AnalyticsPage />} />

              {/* Goals */}
              <Route path="/goals" element={<GoalsPage />} />

              {/* Profile */}
              <Route path="/profile" element={<ProfilePage />} />
              <Route path="/settings" element={<SettingsPage />} />
              </Route>
            </Route>

            {/* Admin Routes - Separate Layout */}
            <Route
              element={
                <ProtectedRoute requiredAdmin>
                  <AdminLayout />
                </ProtectedRoute>
              }
            >
              <Route path="/admin/dashboard" element={<AdminDashboard />} />
              <Route path="/admin/users" element={<AdminUsers />} />
              <Route path="/admin/foods" element={<AdminFoods />} />
              <Route path="/admin/recipes" element={<AdminRecipes />} />
              <Route path="/admin/meal-plans" element={<AdminMealPlans />} />
            </Route>

            {/* Catch all */}
            <Route
              path="*"
              element={
                isAuthenticated ? (
                  user?.is_admin ? (
                    <Navigate to="/admin/dashboard" replace />
                  ) : (
                    <Navigate to={isOnboardingPending() ? '/onboarding' : '/dashboard'} replace />
                  )
                ) : (
                  <Navigate to="/login" replace />
                )
              }
            />
          </Routes>
        </BrowserRouter>
      </ToastProvider>
    </QueryClientProvider>
  );
}

export default App;