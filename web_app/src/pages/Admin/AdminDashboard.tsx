import { useQuery } from '@tanstack/react-query';
import {
  Users,
  UserCheck,
  Shield,
  CheckCircle,
  Apple,
  ChefHat,
  Calendar,
  UtensilsCrossed,
  TrendingUp,
  Activity,
} from 'lucide-react';
import { Card, CardBody, Skeleton } from '../../components/ui';
import { adminAnalyticsApi, type SystemStats } from '../../api/admin';

export default function AdminDashboard() {
  const { data: stats, isLoading } = useQuery<SystemStats>({
    queryKey: ['admin', 'stats'],
    queryFn: () => adminAnalyticsApi.getOverview(),
  });

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Tổng quan hệ thống</h1>
        <p className="text-sm text-gray-500 mt-1">
          Chào mừng bạn đến với trang quản trị NutriAI
        </p>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
            <Skeleton key={i} className="h-32 rounded-xl" />
          ))}
        </div>
      ) : stats ? (
        <>
          {/* User Stats */}
          <div>
            <h2 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
              <Users className="w-5 h-5 text-primary" />
              Người dùng
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard
                icon={<Users className="w-6 h-6 text-blue-500" />}
                label="Tổng người dùng"
                value={stats.total_users}
                color="blue"
              />
              <StatCard
                icon={<UserCheck className="w-6 h-6 text-green-500" />}
                label="Đang hoạt động"
                value={stats.active_users}
                color="green"
              />
              <StatCard
                icon={<Shield className="w-6 h-6 text-purple-500" />}
                label="Quản trị viên"
                value={stats.admin_users}
                color="purple"
              />
              <StatCard
                icon={<CheckCircle className="w-6 h-6 text-orange-500" />}
                label="Đã xác minh"
                value={stats.verified_users}
                color="orange"
              />
            </div>
          </div>

          {/* New Users */}
          <Card>
            <CardBody>
              <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-green-500" />
                Người dùng mới
              </h3>
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center p-4 bg-green-50 rounded-xl">
                  <p className="text-3xl font-bold text-green-600">{stats.new_users_today}</p>
                  <p className="text-sm text-gray-500 mt-1">Hôm nay</p>
                </div>
                <div className="text-center p-4 bg-blue-50 rounded-xl">
                  <p className="text-3xl font-bold text-blue-600">{stats.new_users_this_week}</p>
                  <p className="text-sm text-gray-500 mt-1">Tuần này</p>
                </div>
                <div className="text-center p-4 bg-purple-50 rounded-xl">
                  <p className="text-3xl font-bold text-purple-600">{stats.new_users_this_month}</p>
                  <p className="text-sm text-gray-500 mt-1">Tháng này</p>
                </div>
              </div>
            </CardBody>
          </Card>

          {/* Food Stats */}
          <div>
            <h2 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
              <Apple className="w-5 h-5 text-red-500" />
              Thực phẩm
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <StatCard
                icon={<Apple className="w-6 h-6 text-red-500" />}
                label="Tổng thực phẩm"
                value={stats.total_foods}
                color="red"
              />
              <StatCard
                icon={<CheckCircle className="w-6 h-6 text-green-500" />}
                label="Đã xác minh"
                value={stats.verified_foods}
                color="green"
              />
              <StatCard
                icon={<Activity className="w-6 h-6 text-yellow-500" />}
                label="Chưa xác minh"
                value={stats.unverified_foods}
                color="yellow"
              />
            </div>
          </div>

          {/* Recipe Stats */}
          <div>
            <h2 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
              <ChefHat className="w-5 h-5 text-orange-500" />
              Công thức nấu ăn
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <StatCard
                icon={<ChefHat className="w-6 h-6 text-orange-500" />}
                label="Tổng công thức"
                value={stats.total_recipes}
                color="orange"
              />
              <StatCard
                icon={<CheckCircle className="w-6 h-6 text-green-500" />}
                label="Đã xác minh"
                value={stats.verified_recipes}
                color="green"
              />
              <StatCard
                icon={<Activity className="w-6 h-6 text-yellow-500" />}
                label="Chưa xác minh"
                value={stats.unverified_recipes}
                color="yellow"
              />
            </div>
          </div>

          {/* Meal Plans & Engagement */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardBody>
                <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <Calendar className="w-5 h-5 text-indigo-500" />
                  Kế hoạch ăn uống
                </h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <span className="text-gray-600">Tổng kế hoạch</span>
                    <span className="font-bold text-gray-900">{stats.total_meal_plans}</span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                    <span className="text-gray-600">Đang hoạt động</span>
                    <span className="font-bold text-green-600">{stats.active_meal_plans}</span>
                  </div>
                </div>
              </CardBody>
            </Card>

            <Card>
              <CardBody>
                <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <UtensilsCrossed className="w-5 h-5 text-teal-500" />
                  Nhật ký ăn uống
                </h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <span className="text-gray-600">Tổng nhật ký</span>
                    <span className="font-bold text-gray-900">{stats.total_food_logs.toLocaleString()}</span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                    <span className="text-gray-600">Tuần này</span>
                    <span className="font-bold text-blue-600">{stats.logs_this_week.toLocaleString()}</span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-purple-50 rounded-lg">
                    <span className="text-gray-600">Tháng này</span>
                    <span className="font-bold text-purple-600">{stats.logs_this_month.toLocaleString()}</span>
                  </div>
                </div>
              </CardBody>
            </Card>
          </div>
        </>
      ) : null}
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
  color: 'blue' | 'green' | 'purple' | 'orange' | 'red' | 'yellow';
}) {
  const colorClasses: Record<string, string> = {
    blue: 'bg-blue-50 border-blue-100',
    green: 'bg-green-50 border-green-100',
    purple: 'bg-purple-50 border-purple-100',
    orange: 'bg-orange-50 border-orange-100',
    red: 'bg-red-50 border-red-100',
    yellow: 'bg-yellow-50 border-yellow-100',
  };

  return (
    <div className={`p-4 rounded-xl border ${colorClasses[color]}`}>
      <div className="flex items-center gap-3 mb-2">
        {icon}
        <span className="text-sm text-gray-500">{label}</span>
      </div>
      <p className="text-3xl font-bold text-gray-900">{value.toLocaleString()}</p>
    </div>
  );
}
