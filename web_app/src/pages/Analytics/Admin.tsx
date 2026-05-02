import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Users, UserCheck, Shield, CheckCircle } from 'lucide-react';
import { Card, CardBody, CardHeader, Badge, Skeleton, useToast } from '../../components/ui';
import { PageContainer } from '../../components/layout';
import { adminAnalyticsApi, adminUsersApi } from '../../api/admin';

interface AdminStats {
  total_users: number;
  active_users: number;
  admin_users: number;
  verified_users: number;
  new_users_today: number;
  new_users_this_week: number;
  new_users_this_month: number;
}

export default function AdminPage() {
  const toast = useToast();
  const queryClient = useQueryClient();

  // Fetch admin stats
  const { data: stats, isLoading: statsLoading } = useQuery<AdminStats>({
    queryKey: ['adminStats'],
    queryFn: () => adminAnalyticsApi.getStats(),
  });

  // Fetch users list
  const { data: usersData, isLoading: usersLoading } = useQuery({
    queryKey: ['adminUsers'],
    queryFn: () => adminUsersApi.list({ limit: 50 }),
  });

  // Update user status mutation
  const updateStatusMutation = useMutation({
    mutationFn: ({ userId, isActive, isAdmin }: { userId: string; isActive?: boolean; isAdmin?: boolean }) =>
      adminUsersApi.updateStatus(userId, {
        is_active: isActive,
        is_admin: isAdmin,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['adminUsers'] });
      queryClient.invalidateQueries({ queryKey: ['adminStats'] });
      toast.success('Cập nhật thành công');
    },
    onError: () => {
      toast.error('Cập nhật thất bại');
    },
  });

  return (
    <PageContainer
      title="Quản trị hệ thống"
      subtitle="Quản lý người dùng và nội dung"
    >
      {/* Stats Cards */}
      {statsLoading ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-24 w-full rounded-xl" />)}
        </div>
      ) : stats ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <StatCard icon={<Users className="w-6 h-6 text-blue-500" />} label="Tổng người dùng" value={stats.total_users} />
          <StatCard icon={<UserCheck className="w-6 h-6 text-green-500" />} label="Đang hoạt động" value={stats.active_users} />
          <StatCard icon={<Shield className="w-6 h-6 text-purple-500" />} label="Quản trị viên" value={stats.admin_users} />
          <StatCard icon={<CheckCircle className="w-6 h-6 text-orange-500" />} label="Đã xác minh" value={stats.verified_users} />
        </div>
      ) : null}

      {/* New Users */}
      {stats && (
        <Card className="mb-6">
          <CardBody>
            <h3 className="font-semibold text-gray-900 mb-4">Người dùng mới</h3>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-4 bg-gray-50 rounded-xl">
                <p className="text-2xl font-bold text-primary">{stats.new_users_today}</p>
                <p className="text-sm text-gray-500">Hôm nay</p>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-xl">
                <p className="text-2xl font-bold text-primary">{stats.new_users_this_week}</p>
                <p className="text-sm text-gray-500">Tuần này</p>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-xl">
                <p className="text-2xl font-bold text-primary">{stats.new_users_this_month}</p>
                <p className="text-sm text-gray-500">Tháng này</p>
              </div>
            </div>
          </CardBody>
        </Card>
      )}

      {/* Users List */}
      <Card>
        <CardHeader>
          <h2 className="font-semibold text-gray-900">Danh sách người dùng</h2>
        </CardHeader>
        <CardBody>
          {usersLoading ? (
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map(i => <Skeleton key={i} className="h-16 w-full rounded-xl" />)}
            </div>
          ) : usersData?.users && usersData.users.length > 0 ? (
            <div className="space-y-3">
              {usersData.users.map((user: any) => (
                <div key={user.user_id} className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center">
                      <span className="text-primary font-medium">
                        {user.full_name?.charAt(0) || user.email.charAt(0).toUpperCase()}
                      </span>
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{user.full_name || 'Chưa có tên'}</p>
                      <p className="text-sm text-gray-500">{user.email}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={user.is_active ? 'success' : 'error'}>
                      {user.is_active ? 'Hoạt động' : 'Tắt'}
                    </Badge>
                    {user.is_admin && <Badge variant="info">Admin</Badge>}
                    {user.email_verified && <Badge variant="success">Đã xác minh</Badge>}
                    <div className="flex gap-1 ml-2">
                      <button
                        onClick={() => updateStatusMutation.mutate({ userId: user.user_id, isActive: !user.is_active })}
                        className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded"
                        title={user.is_active ? 'Tắt tài khoản' : 'Bật tài khoản'}
                      >
                        {user.is_active ? '🔒' : '🔓'}
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-center text-gray-500 py-8">Chưa có người dùng nào</p>
          )}
        </CardBody>
      </Card>
    </PageContainer>
  );
}

function StatCard({ icon, label, value }: { icon: React.ReactNode; label: string; value: number }) {
  return (
    <div className="p-4 bg-white rounded-xl border border-gray-200">
      <div className="flex items-center gap-3 mb-2">
        {icon}
        <span className="text-sm text-gray-500">{label}</span>
      </div>
      <p className="text-3xl font-bold text-gray-900">{value}</p>
    </div>
  );
}