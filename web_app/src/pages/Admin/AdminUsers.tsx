import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Search,
  UserCheck,
  UserX,
  Shield,
  ShieldOff,
  Trash2,
  Eye,
  X,
  ChevronLeft,
  ChevronRight,
  CheckCircle,
} from 'lucide-react';
import { Card, CardBody, CardHeader, Button, Badge, Input, Skeleton, Modal, useToast } from '../../components/ui';
import { adminUsersApi, type AdminUser } from '../../api/admin';
import { format } from 'date-fns';
import { vi } from 'date-fns/locale';

export default function AdminUsers() {
  const toast = useToast();
  const queryClient = useQueryClient();

  // Filters
  const [search, setSearch] = useState('');
  const [filterActive, setFilterActive] = useState<boolean | undefined>(undefined);
  const [filterAdmin, setFilterAdmin] = useState<boolean | undefined>(undefined);
  const [page, setPage] = useState(0);
  const [selectedUser, setSelectedUser] = useState<AdminUser | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [confirmAction, setConfirmAction] = useState<{
    type: 'block' | 'unblock' | 'grant_admin' | 'revoke_admin' | 'delete';
    user: AdminUser;
  } | null>(null);

  const limit = 15;

  const { data, isLoading } = useQuery<{ total: number; users: AdminUser[] }>({
    queryKey: ['admin', 'users', page, search, filterActive, filterAdmin],
    queryFn: () =>
      adminUsersApi.list({
        skip: page * limit,
        limit,
        search: search || undefined,
        is_active: filterActive,
        is_admin: filterAdmin,
      }),
  });

  // Update status mutation
  const updateStatusMutation = useMutation({
    mutationFn: ({
      userId,
      data,
    }: {
      userId: string;
      data: { is_active?: boolean; is_admin?: boolean; email_verified?: boolean };
    }) => adminUsersApi.updateStatus(userId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'stats'] });
      toast.success('Cập nhật thành công');
      setShowConfirmModal(false);
      setConfirmAction(null);
    },
    onError: () => {
      toast.error('Cập nhật thất bại');
    },
  });

  // Delete user mutation
  const deleteUserMutation = useMutation({
    mutationFn: (userId: string) => adminUsersApi.delete(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'stats'] });
      toast.success('Xóa người dùng thành công');
      setShowConfirmModal(false);
      setConfirmAction(null);
    },
    onError: () => {
      toast.error('Xóa người dùng thất bại');
    },
  });

  const handleConfirmAction = () => {
    if (!confirmAction) return;

    const { type, user } = confirmAction;
    if (type === 'delete') {
      deleteUserMutation.mutate(user.user_id);
    } else if (type === 'block') {
      updateStatusMutation.mutate({ userId: user.user_id, data: { is_active: false } });
    } else if (type === 'unblock') {
      updateStatusMutation.mutate({ userId: user.user_id, data: { is_active: true } });
    } else if (type === 'grant_admin') {
      updateStatusMutation.mutate({ userId: user.user_id, data: { is_admin: true } });
    } else if (type === 'revoke_admin') {
      updateStatusMutation.mutate({ userId: user.user_id, data: { is_admin: false } });
    }
  };

  const getConfirmMessage = () => {
    if (!confirmAction) return '';
    const { type, user } = confirmAction;
    const name = user.full_name || user.email;

    switch (type) {
      case 'block':
        return `Bạn có chắc muốn khóa tài khoản của "${name}"? Họ sẽ không thể đăng nhập.`;
      case 'unblock':
        return `Bạn có chắc muốn mở khóa tài khoản của "${name}"?`;
      case 'grant_admin':
        return `Bạn có chắc muốn cấp quyền quản trị cho "${name}"?`;
      case 'revoke_admin':
        return `Bạn có chắc muốn thu hồi quyền quản trị của "${name}"?`;
      case 'delete':
        return `⚠️ Cảnh báo: Bạn có chắc muốn xóa vĩnh viễn tài khoản của "${name}"? Hành động này không thể hoàn tác và sẽ xóa tất cả dữ liệu liên quan.`;
      default:
        return '';
    }
  };

  const totalPages = data?.total ? Math.ceil(data.total / limit) : 0;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Quản lý người dùng</h1>
        <p className="text-sm text-gray-500 mt-1">
          Quản lý tài khoản, quyền truy cập và trạng thái người dùng
        </p>
      </div>

      {/* Filters */}
      <Card>
        <CardBody>
          <div className="flex flex-col lg:flex-row gap-4">
            {/* Search */}
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <Input
                  placeholder="Tìm theo email hoặc tên..."
                  value={search}
                  onChange={(e) => {
                    setSearch(e.target.value);
                    setPage(0);
                  }}
                  className="pl-10"
                />
                {search && (
                  <button
                    onClick={() => setSearch('')}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>

            {/* Filter Buttons */}
            <div className="flex flex-wrap gap-2">
              <select
                value={
                  filterActive === undefined
                    ? ''
                    : filterActive
                    ? 'active'
                    : 'inactive'
                }
                onChange={(e) => {
                  setFilterActive(e.target.value === '' ? undefined : e.target.value === 'active');
                  setPage(0);
                }}
                className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
              >
                <option value="">Tất cả trạng thái</option>
                <option value="active">Đang hoạt động</option>
                <option value="inactive">Đã khóa</option>
              </select>

              <select
                value={filterAdmin === undefined ? '' : filterAdmin ? 'admin' : 'user'}
                onChange={(e) => {
                  setFilterAdmin(e.target.value === '' ? undefined : e.target.value === 'admin');
                  setPage(0);
                }}
                className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
              >
                <option value="">Tất cả quyền</option>
                <option value="admin">Quản trị viên</option>
                <option value="user">Người dùng</option>
              </select>
            </div>
          </div>

          {/* Active Filters */}
          {(filterActive !== undefined || filterAdmin !== undefined || search) && (
            <div className="flex items-center gap-2 mt-3 flex-wrap">
              <span className="text-sm text-gray-500">Bộ lọc:</span>
              {filterActive !== undefined && (
                <Badge
                  variant={filterActive ? 'success' : 'error'}
                  className="cursor-pointer"
                  onClick={() => setFilterActive(undefined)}
                >
                  {filterActive ? 'Đang hoạt động' : 'Đã khóa'} <X className="w-3 h-3 ml-1" />
                </Badge>
              )}
              {filterAdmin !== undefined && (
                <Badge
                  variant={filterAdmin ? 'info' : 'default'}
                  className="cursor-pointer"
                  onClick={() => setFilterAdmin(undefined)}
                >
                  {filterAdmin ? 'Quản trị' : 'Người dùng'} <X className="w-3 h-3 ml-1" />
                </Badge>
              )}
              {search && (
                <Badge variant="default" className="cursor-pointer" onClick={() => setSearch('')}>
                  Tìm: {search} <X className="w-3 h-3 ml-1" />
                </Badge>
              )}
              <button
                onClick={() => {
                  setSearch('');
                  setFilterActive(undefined);
                  setFilterAdmin(undefined);
                  setPage(0);
                }}
                className="text-sm text-primary hover:underline"
              >
                Xóa tất cả
              </button>
            </div>
          )}
        </CardBody>
      </Card>

      {/* Users List */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-gray-900">
              Danh sách người dùng
              {data?.total !== undefined && (
                <span className="ml-2 text-sm font-normal text-gray-500">
                  ({data.total.toLocaleString()} người dùng)
                </span>
              )}
            </h2>
          </div>
        </CardHeader>
        <CardBody>
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <Skeleton key={i} className="h-16 w-full rounded-xl" />
              ))}
            </div>
          ) : data?.users && data.users.length > 0 ? (
            <>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-100">
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Người dùng</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Trạng thái</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Quyền</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Ngày tạo</th>
                      <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">Hành động</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.users.map((user) => (
                      <tr key={user.user_id} className="border-b border-gray-50 hover:bg-gray-50">
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center">
                              <span className="text-primary font-medium">
                                {user.full_name?.charAt(0) || user.email.charAt(0).toUpperCase()}
                              </span>
                            </div>
                            <div>
                              <p className="font-medium text-gray-900">
                                {user.full_name || 'Chưa có tên'}
                              </p>
                              <p className="text-sm text-gray-500">{user.email}</p>
                            </div>
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <Badge variant={user.is_active ? 'success' : 'error'}>
                            {user.is_active ? 'Hoạt động' : 'Đã khóa'}
                          </Badge>
                          {user.email_verified && (
                            <Badge variant="success" className="ml-1">
                              <CheckCircle className="w-3 h-3 mr-1" />
                              Đã xác minh
                            </Badge>
                          )}
                        </td>
                        <td className="py-3 px-4">
                          {user.is_admin ? (
                            <Badge variant="info">
                              <Shield className="w-3 h-3 mr-1" />
                              Quản trị
                            </Badge>
                          ) : (
                            <span className="text-sm text-gray-500">Người dùng</span>
                          )}
                        </td>
                        <td className="py-3 px-4">
                          <span className="text-sm text-gray-500">
                            {format(new Date(user.created_at), 'dd/MM/yyyy', { locale: vi })}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex items-center justify-end gap-1">
                            {/* View Detail */}
                            <button
                              onClick={() => {
                                setSelectedUser(user);
                                setShowDetailModal(true);
                              }}
                              className="p-2 text-gray-400 hover:text-primary hover:bg-primary/5 rounded-lg transition-colors"
                              title="Xem chi tiết"
                            >
                              <Eye className="w-4 h-4" />
                            </button>

                            {/* Block/Unblock */}
                            <button
                              onClick={() => {
                                setConfirmAction({
                                  type: user.is_active ? 'block' : 'unblock',
                                  user,
                                });
                                setShowConfirmModal(true);
                              }}
                              className={`p-2 rounded-lg transition-colors ${
                                user.is_active
                                  ? 'text-gray-400 hover:text-red-500 hover:bg-red-50'
                                  : 'text-gray-400 hover:text-green-500 hover:bg-green-50'
                              }`}
                              title={user.is_active ? 'Khóa tài khoản' : 'Mở khóa'}
                            >
                              {user.is_active ? (
                                <UserX className="w-4 h-4" />
                              ) : (
                                <UserCheck className="w-4 h-4" />
                              )}
                            </button>

                            {/* Grant/Revoke Admin */}
                            <button
                              onClick={() => {
                                setConfirmAction({
                                  type: user.is_admin ? 'revoke_admin' : 'grant_admin',
                                  user,
                                });
                                setShowConfirmModal(true);
                              }}
                              className="p-2 text-gray-400 hover:text-purple-500 hover:bg-purple-50 rounded-lg transition-colors"
                              title={user.is_admin ? 'Thu hồi quyền admin' : 'Cấp quyền admin'}
                            >
                              {user.is_admin ? (
                                <ShieldOff className="w-4 h-4" />
                              ) : (
                                <Shield className="w-4 h-4" />
                              )}
                            </button>

                            {/* Delete */}
                            <button
                              onClick={() => {
                                setConfirmAction({ type: 'delete', user });
                                setShowConfirmModal(true);
                              }}
                              className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                              title="Xóa tài khoản"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-100">
                  <p className="text-sm text-gray-500">
                    Hiển thị {page * limit + 1} - {Math.min((page + 1) * limit, data.total)} của{' '}
                    {data.total}
                  </p>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage((p) => Math.max(0, p - 1))}
                      disabled={page === 0}
                    >
                      <ChevronLeft className="w-4 h-4" />
                    </Button>
                    <span className="text-sm text-gray-600">
                      Trang {page + 1} / {totalPages}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                      disabled={page >= totalPages - 1}
                    >
                      <ChevronRight className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="text-center py-12">
              <Users className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500">Không tìm thấy người dùng nào</p>
            </div>
          )}
        </CardBody>
      </Card>

      {/* User Detail Modal */}
      <Modal
        isOpen={showDetailModal}
        onClose={() => setShowDetailModal(false)}
        title="Chi tiết người dùng"
      >
        {selectedUser && (
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center">
                <span className="text-primary text-2xl font-bold">
                  {selectedUser.full_name?.charAt(0) ||
                    selectedUser.email.charAt(0).toUpperCase()}
                </span>
              </div>
              <div>
                <h3 className="text-lg font-semibold">
                  {selectedUser.full_name || 'Chưa có tên'}
                </h3>
                <p className="text-gray-500">{selectedUser.email}</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500">Trạng thái</p>
                <Badge variant={selectedUser.is_active ? 'success' : 'error'} className="mt-1">
                  {selectedUser.is_active ? 'Hoạt động' : 'Đã khóa'}
                </Badge>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500">Quyền</p>
                <Badge variant={selectedUser.is_admin ? 'info' : 'default'} className="mt-1">
                  {selectedUser.is_admin ? 'Quản trị' : 'Người dùng'}
                </Badge>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500">Xác minh email</p>
                <Badge
                  variant={selectedUser.email_verified ? 'success' : 'warning'}
                  className="mt-1"
                >
                  {selectedUser.email_verified ? 'Đã xác minh' : 'Chưa xác minh'}
                </Badge>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500">Ngày tạo</p>
                <p className="font-medium mt-1">
                  {format(new Date(selectedUser.created_at), 'dd/MM/yyyy HH:mm', { locale: vi })}
                </p>
              </div>
              {selectedUser.last_login && (
                <div className="p-3 bg-gray-50 rounded-lg col-span-2">
                  <p className="text-sm text-gray-500">Đăng nhập cuối</p>
                  <p className="font-medium mt-1">
                    {format(new Date(selectedUser.last_login), 'dd/MM/yyyy HH:mm', { locale: vi })}
                  </p>
                </div>
              )}
            </div>

            <div className="flex gap-2 pt-4">
              {selectedUser.is_active ? (
                <Button
                  variant="outline"
                  className="flex-1"
                  onClick={() => {
                    setShowDetailModal(false);
                    setConfirmAction({ type: 'block', user: selectedUser });
                    setShowConfirmModal(true);
                  }}
                >
                  <UserX className="w-4 h-4 mr-2" />
                  Khóa tài khoản
                </Button>
              ) : (
                <Button
                  variant="outline"
                  className="flex-1"
                  onClick={() => {
                    setShowDetailModal(false);
                    setConfirmAction({ type: 'unblock', user: selectedUser });
                    setShowConfirmModal(true);
                  }}
                >
                  <UserCheck className="w-4 h-4 mr-2" />
                  Mở khóa
                </Button>
              )}
              {selectedUser.is_admin ? (
                <Button
                  variant="outline"
                  className="flex-1"
                  onClick={() => {
                    setShowDetailModal(false);
                    setConfirmAction({ type: 'revoke_admin', user: selectedUser });
                    setShowConfirmModal(true);
                  }}
                >
                  <ShieldOff className="w-4 h-4 mr-2" />
                  Thu hồi admin
                </Button>
              ) : (
                <Button
                  variant="outline"
                  className="flex-1"
                  onClick={() => {
                    setShowDetailModal(false);
                    setConfirmAction({ type: 'grant_admin', user: selectedUser });
                    setShowConfirmModal(true);
                  }}
                >
                  <Shield className="w-4 h-4 mr-2" />
                  Cấp quyền admin
                </Button>
              )}
            </div>
          </div>
        )}
      </Modal>

      {/* Confirm Modal */}
      <Modal
        isOpen={showConfirmModal}
        onClose={() => {
          setShowConfirmModal(false);
          setConfirmAction(null);
        }}
        title="Xác nhận hành động"
      >
        <p className="text-gray-600">{getConfirmMessage()}</p>
        <div className="flex gap-3 mt-6">
          <Button
            variant="outline"
            className="flex-1"
            onClick={() => {
              setShowConfirmModal(false);
              setConfirmAction(null);
            }}
          >
            Hủy
          </Button>
          <Button
            variant={confirmAction?.type === 'delete' ? 'danger' : 'primary'}
            className="flex-1"
            onClick={handleConfirmAction}
            isLoading={
              updateStatusMutation.isPending || deleteUserMutation.isPending
            }
          >
            Xác nhận
          </Button>
        </div>
      </Modal>
    </div>
  );
}

function Users(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  );
}
