import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Search,
  X,
  Eye,
  Trash2,
  Calendar,
  User,
  UtensilsCrossed,
} from 'lucide-react';
import { Card, CardBody, CardHeader, Button, Badge, Input, Skeleton, Modal, useToast } from '../../components/ui';
import { adminMealPlansApi, type AdminMealPlan } from '../../api/admin';
import { format } from 'date-fns';
import { vi } from 'date-fns/locale';

export default function AdminMealPlans() {
  const toast = useToast();
  const queryClient = useQueryClient();

  // Filters
  const [search, setSearch] = useState('');
  const [filterActive, setFilterActive] = useState<boolean | undefined>(undefined);
  const [page, setPage] = useState(0);
  const [selectedPlan, setSelectedPlan] = useState<(AdminMealPlan & { items?: any[] }) | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [confirmAction, setConfirmAction] = useState<{
    type: 'delete';
    plan: AdminMealPlan;
  } | null>(null);

  const limit = 15;

  const { data, isLoading } = useQuery<{ total: number; meal_plans: AdminMealPlan[] }>({
    queryKey: ['admin', 'meal-plans', page, search, filterActive],
    queryFn: () =>
      adminMealPlansApi.list({
        skip: page * limit,
        limit,
        search: search || undefined,
        is_active: filterActive,
      }),
  });

  // Delete meal plan mutation
  const deletePlanMutation = useMutation({
    mutationFn: (planId: string) => adminMealPlansApi.delete(planId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'meal-plans'] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'stats'] });
      toast.success('Xóa kế hoạch thành công');
      setShowConfirmModal(false);
      setConfirmAction(null);
    },
    onError: () => {
      toast.error('Xóa kế hoạch thất bại');
    },
  });

  // View detail mutation
  const viewDetailMutation = useMutation({
    mutationFn: (planId: string) => adminMealPlansApi.getDetail(planId),
    onSuccess: (data) => {
      setSelectedPlan(data);
    },
    onError: () => {
      toast.error('Không thể lấy chi tiết kế hoạch');
    },
  });

  const handleConfirmAction = () => {
    if (!confirmAction) return;
    const { type, plan } = confirmAction;
    if (type === 'delete') {
      deletePlanMutation.mutate(plan.plan_id);
    }
  };

  const getConfirmMessage = () => {
    if (!confirmAction) return '';
    const { type, plan } = confirmAction;
    switch (type) {
      case 'delete':
        return `⚠️ Cảnh báo: Bạn có chắc muốn xóa kế hoạch "${plan.plan_name}" của "${plan.user_email}"? Hành động này không thể hoàn tác.`;
      default:
        return '';
    }
  };

  const totalPages = data?.total ? Math.ceil(data.total / limit) : 0;

  const openDetailModal = (plan: AdminMealPlan) => {
    setSelectedPlan(null);
    viewDetailMutation.mutate(plan.plan_id);
    setShowDetailModal(true);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Quản lý kế hoạch ăn uống</h1>
        <p className="text-sm text-gray-500 mt-1">
          Xem và quản lý kế hoạch ăn uống của người dùng
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
                  placeholder="Tìm theo tên kế hoạch..."
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
                value={filterActive === undefined ? '' : filterActive ? 'active' : 'inactive'}
                onChange={(e) => {
                  setFilterActive(e.target.value === '' ? undefined : e.target.value === 'active');
                  setPage(0);
                }}
                className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
              >
                <option value="">Tất cả</option>
                <option value="active">Đang hoạt động</option>
                <option value="inactive">Đã hoàn thành</option>
              </select>
            </div>
          </div>

          {/* Active Filters */}
          {(filterActive !== undefined || search) && (
            <div className="flex items-center gap-2 mt-3 flex-wrap">
              <span className="text-sm text-gray-500">Bộ lọc:</span>
              {filterActive !== undefined && (
                <Badge
                  variant={filterActive ? 'success' : 'default'}
                  className="cursor-pointer"
                  onClick={() => setFilterActive(undefined)}
                >
                  {filterActive ? 'Đang hoạt động' : 'Đã hoàn thành'} <X className="w-3 h-3 ml-1" />
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

      {/* Meal Plans List */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-gray-900">
              Danh sách kế hoạch
              {data?.total !== undefined && (
                <span className="ml-2 text-sm font-normal text-gray-500">
                  ({data.total.toLocaleString()} kế hoạch)
                </span>
              )}
            </h2>
          </div>
        </CardHeader>
        <CardBody>
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <Skeleton key={i} className="h-24 w-full rounded-xl" />
              ))}
            </div>
          ) : data?.meal_plans && data.meal_plans.length > 0 ? (
            <>
              <div className="space-y-3">
                {data.meal_plans.map((plan) => (
                  <div
                    key={plan.plan_id}
                    className="p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                            <Calendar className="w-5 h-5 text-primary" />
                          </div>
                          <div>
                            <h3 className="font-medium text-gray-900">{plan.plan_name}</h3>
                            <div className="flex items-center gap-2 text-sm text-gray-500">
                              <User className="w-4 h-4" />
                              <span>{plan.user_name || plan.user_email}</span>
                            </div>
                          </div>
                        </div>

                        <div className="flex flex-wrap gap-2 mt-3">
                          <Badge variant={plan.is_active ? 'success' : 'default'}>
                            {plan.is_active ? 'Đang hoạt động' : 'Đã hoàn thành'}
                          </Badge>
                          <Badge variant="info">
                            <Calendar className="w-3 h-3 mr-1" />
                            {plan.duration_days} ngày
                          </Badge>
                          <Badge variant="default">
                            <UtensilsCrossed className="w-3 h-3 mr-1" />
                            {plan.total_meals} bữa
                          </Badge>
                        </div>

                        <div className="flex items-center gap-4 mt-3 text-sm text-gray-500">
                          <span>
                            {format(new Date(plan.start_date), 'dd/MM/yyyy')} -{' '}
                            {format(new Date(plan.end_date), 'dd/MM/yyyy')}
                          </span>
                          <span>Tổng: {Math.round(plan.total_calories).toLocaleString()} kcal</span>
                          <span>
                            {format(new Date(plan.created_at), 'dd/MM/yyyy', { locale: vi })}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 ml-4">
                        <button
                          onClick={() => openDetailModal(plan)}
                          className="p-2 text-gray-400 hover:text-primary hover:bg-primary/5 rounded-lg transition-colors"
                          title="Xem chi tiết"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => {
                            setConfirmAction({ type: 'delete', plan });
                            setShowConfirmModal(true);
                          }}
                          className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                          title="Xóa kế hoạch"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
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
                      ←
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
                      →
                    </Button>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="text-center py-12">
              <Calendar className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500">Không tìm thấy kế hoạch nào</p>
            </div>
          )}
        </CardBody>
      </Card>

      {/* Plan Detail Modal */}
      <Modal
        isOpen={showDetailModal}
        onClose={() => {
          setShowDetailModal(false);
          setSelectedPlan(null);
        }}
        title="Chi tiết kế hoạch ăn uống"
      >
        {viewDetailMutation.isPending ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-4 border-primary border-t-transparent" />
          </div>
        ) : selectedPlan ? (
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center">
                <Calendar className="w-6 h-6 text-primary" />
              </div>
              <div>
                <h3 className="text-lg font-semibold">{selectedPlan.plan_name}</h3>
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <User className="w-4 h-4" />
                  <span>{selectedPlan.user_name || selectedPlan.user_email}</span>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500">Thời gian</p>
                <p className="font-medium mt-1">
                  {format(new Date(selectedPlan.start_date), 'dd/MM/yyyy')} -{' '}
                  {format(new Date(selectedPlan.end_date), 'dd/MM/yyyy')}
                </p>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500">Số ngày</p>
                <p className="font-medium mt-1">{selectedPlan.duration_days} ngày</p>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500">Trạng thái</p>
                <Badge variant={selectedPlan.is_active ? 'success' : 'default'} className="mt-1">
                  {selectedPlan.is_active ? 'Đang hoạt động' : 'Đã hoàn thành'}
                </Badge>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500">Tổng bữa ăn</p>
                <p className="font-medium mt-1">{selectedPlan.total_meals} bữa</p>
              </div>
            </div>

            {/* Summary */}
            <div className="p-4 bg-primary/5 rounded-lg">
              <h4 className="font-medium mb-2">Tổng quan dinh dưỡng</h4>
              <p className="text-2xl font-bold text-primary">
                {Math.round(selectedPlan.total_calories).toLocaleString()} kcal
              </p>
              <p className="text-sm text-gray-500">
                Trung bình: {selectedPlan.total_meals > 0
                  ? Math.round(selectedPlan.total_calories / selectedPlan.total_meals).toLocaleString()
                  : 0} kcal/bữa
              </p>
            </div>

            {/* Items by day */}
            {selectedPlan.items && selectedPlan.items.length > 0 && (
              <div>
                <h4 className="font-medium mb-3">Các bữa ăn</h4>
                <div className="space-y-3 max-h-64 overflow-y-auto">
                  {Object.entries(
                    selectedPlan.items.reduce<Record<string, any[]>>((acc, item) => {
                      const date = item.day_date;
                      if (!acc[date]) acc[date] = [];
                      acc[date].push(item);
                      return acc;
                    }, {})
                  ).map(([date, items]) => (
                    <div key={date} className="p-3 bg-gray-50 rounded-lg">
                      <p className="font-medium text-sm text-gray-700 mb-2">
                        {format(new Date(date), 'EEEE, dd/MM/yyyy', { locale: vi })}
                      </p>
                      <div className="space-y-2">
                        {items.map((item: any) => (
                          <div key={item.item_id} className="flex items-center justify-between text-sm">
                            <div className="flex items-center gap-2">
                              <Badge variant="default" className="text-xs">
                                {item.meal_type === 'breakfast'
                                  ? 'Sáng'
                                  : item.meal_type === 'lunch'
                                  ? 'Trưa'
                                  : item.meal_type === 'dinner'
                                  ? 'Tối'
                                  : 'Snack'}
                              </Badge>
                              <span className="text-gray-700">
                                {item.notes || 'Không có ghi chú'}
                              </span>
                            </div>
                            <span className="font-medium text-gray-600">
                              {item.calories ? `${Math.round(item.calories)} kcal` : 'N/A'}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="flex gap-2 pt-4">
              <Button
                variant="danger"
                className="flex-1"
                onClick={() => {
                  setShowDetailModal(false);
                  setConfirmAction({
                    type: 'delete',
                    plan: data?.meal_plans.find((p) => p.plan_id === selectedPlan.plan_id) || selectedPlan,
                  });
                  setShowConfirmModal(true);
                }}
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Xóa kế hoạch
              </Button>
            </div>
          </div>
        ) : null}
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
            variant="danger"
            className="flex-1"
            onClick={handleConfirmAction}
            isLoading={deletePlanMutation.isPending}
          >
            Xác nhận
          </Button>
        </div>
      </Modal>
    </div>
  );
}
