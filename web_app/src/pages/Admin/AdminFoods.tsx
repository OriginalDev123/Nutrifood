import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Search,
  X,
  Eye,
  Trash2,
  CheckCircle,
  XCircle,
  AlertCircle,
} from 'lucide-react';
import { Card, CardBody, CardHeader, Button, Badge, Input, Skeleton, Modal, useToast } from '../../components/ui';
import { adminFoodsApi, type AdminFood } from '../../api/admin';
import { format } from 'date-fns';
import { vi } from 'date-fns/locale';

export default function AdminFoods() {
  const toast = useToast();
  const queryClient = useQueryClient();

  // Filters
  const [search, setSearch] = useState('');
  const [filterVerified, setFilterVerified] = useState<boolean | undefined>(undefined);
  const [filterSource, setFilterSource] = useState<string>('');
  const [page, setPage] = useState(0);
  const [selectedFood, setSelectedFood] = useState<AdminFood | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [confirmAction, setConfirmAction] = useState<{
    type: 'verify' | 'unverify' | 'delete';
    food: AdminFood;
  } | null>(null);

  const limit = 15;

  const { data, isLoading } = useQuery<{ total: number; foods: AdminFood[] }>({
    queryKey: ['admin', 'foods', page, search, filterVerified, filterSource],
    queryFn: () =>
      adminFoodsApi.list({
        skip: page * limit,
        limit,
        search: search || undefined,
        is_verified: filterVerified,
        source: filterSource || undefined,
      }),
  });

  // Verify food mutation
  const verifyFoodMutation = useMutation({
    mutationFn: ({ foodId, isVerified }: { foodId: string; isVerified: boolean }) =>
      adminFoodsApi.verify(foodId, isVerified),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'foods'] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'stats'] });
      toast.success('Cập nhật trạng thái thành công');
      setShowConfirmModal(false);
      setConfirmAction(null);
    },
    onError: () => {
      toast.error('Cập nhật thất bại');
    },
  });

  // Delete food mutation
  const deleteFoodMutation = useMutation({
    mutationFn: (foodId: string) => adminFoodsApi.delete(foodId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'foods'] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'stats'] });
      toast.success('Xóa thực phẩm thành công');
      setShowConfirmModal(false);
      setConfirmAction(null);
    },
    onError: () => {
      toast.error('Xóa thực phẩm thất bại');
    },
  });

  const handleConfirmAction = () => {
    if (!confirmAction) return;
    const { type, food } = confirmAction;
    if (type === 'delete') {
      deleteFoodMutation.mutate(food.food_id);
    } else if (type === 'verify') {
      verifyFoodMutation.mutate({ foodId: food.food_id, isVerified: true });
    } else if (type === 'unverify') {
      verifyFoodMutation.mutate({ foodId: food.food_id, isVerified: false });
    }
  };

  const getConfirmMessage = () => {
    if (!confirmAction) return '';
    const { type, food } = confirmAction;
    switch (type) {
      case 'verify':
        return `Bạn có chắc muốn xác minh thực phẩm "${food.name_vi}"?`;
      case 'unverify':
        return `Bạn có chắc muốn hủy xác minh thực phẩm "${food.name_vi}"?`;
      case 'delete':
        return `⚠️ Cảnh báo: Bạn có chắc muốn xóa thực phẩm "${food.name_vi}"? Hành động này không thể hoàn tác.`;
      default:
        return '';
    }
  };

  const totalPages = data?.total ? Math.ceil(data.total / limit) : 0;

  const getSourceLabel = (source: string | null) => {
    switch (source) {
      case 'admin':
        return 'Quản trị';
      case 'usda':
        return 'USDA';
      case 'user_submitted':
        return 'Người dùng';
      default:
        return source || 'N/A';
    }
  };

  const getSourceColor = (source: string | null) => {
    switch (source) {
      case 'admin':
        return 'info';
      case 'usda':
        return 'success';
      case 'user_submitted':
        return 'warning';
      default:
        return 'default';
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Quản lý thực phẩm</h1>
        <p className="text-sm text-gray-500 mt-1">
          Quản lý cơ sở dữ liệu thực phẩm, xác minh và duyệt nội dung
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
                  placeholder="Tìm theo tên thực phẩm..."
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
                value={filterVerified === undefined ? '' : filterVerified ? 'verified' : 'unverified'}
                onChange={(e) => {
                  setFilterVerified(e.target.value === '' ? undefined : e.target.value === 'verified');
                  setPage(0);
                }}
                className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
              >
                <option value="">Tất cả</option>
                <option value="verified">Đã xác minh</option>
                <option value="unverified">Chưa xác minh</option>
              </select>

              <select
                value={filterSource}
                onChange={(e) => {
                  setFilterSource(e.target.value);
                  setPage(0);
                }}
                className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
              >
                <option value="">Tất cả nguồn</option>
                <option value="admin">Quản trị</option>
                <option value="usda">USDA</option>
                <option value="user_submitted">Người dùng</option>
              </select>
            </div>
          </div>

          {/* Active Filters */}
          {(filterVerified !== undefined || filterSource || search) && (
            <div className="flex items-center gap-2 mt-3 flex-wrap">
              <span className="text-sm text-gray-500">Bộ lọc:</span>
              {filterVerified !== undefined && (
                <Badge
                  variant={filterVerified ? 'success' : 'warning'}
                  className="cursor-pointer"
                  onClick={() => setFilterVerified(undefined)}
                >
                  {filterVerified ? 'Đã xác minh' : 'Chưa xác minh'} <X className="w-3 h-3 ml-1" />
                </Badge>
              )}
              {filterSource && (
                <Badge
                  variant="default"
                  className="cursor-pointer"
                  onClick={() => setFilterSource('')}
                >
                  Nguồn: {getSourceLabel(filterSource)} <X className="w-3 h-3 ml-1" />
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
                  setFilterVerified(undefined);
                  setFilterSource('');
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

      {/* Foods List */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-gray-900">
              Danh sách thực phẩm
              {data?.total !== undefined && (
                <span className="ml-2 text-sm font-normal text-gray-500">
                  ({data.total.toLocaleString()} thực phẩm)
                </span>
              )}
            </h2>
          </div>
        </CardHeader>
        <CardBody>
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <Skeleton key={i} className="h-20 w-full rounded-xl" />
              ))}
            </div>
          ) : data?.foods && data.foods.length > 0 ? (
            <>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-100">
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Thực phẩm</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Danh mục</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Năng lượng/100g</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Trạng thái</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Nguồn</th>
                      <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">Hành động</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.foods.map((food) => (
                      <tr key={food.food_id} className="border-b border-gray-50 hover:bg-gray-50">
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-3">
                            {food.image_url ? (
                              <img
                                src={food.image_url}
                                alt={food.name_vi}
                                className="w-10 h-10 rounded-lg object-cover"
                              />
                            ) : (
                              <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                                <span className="text-gray-400 text-xs">No img</span>
                              </div>
                            )}
                            <div>
                              <p className="font-medium text-gray-900">{food.name_vi}</p>
                              {food.name_en && (
                                <p className="text-sm text-gray-500">{food.name_en}</p>
                              )}
                            </div>
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <Badge variant="default">{food.category}</Badge>
                        </td>
                        <td className="py-3 px-4">
                          <span className="text-sm font-medium">{food.calories_per_100g} kcal</span>
                          <p className="text-xs text-gray-500">
                            P: {food.protein_per_100g}g | C: {food.carbs_per_100g}g | F: {food.fat_per_100g}g
                          </p>
                        </td>
                        <td className="py-3 px-4">
                          {food.is_verified ? (
                            <Badge variant="success">
                              <CheckCircle className="w-3 h-3 mr-1" />
                              Đã xác minh
                            </Badge>
                          ) : (
                            <Badge variant="warning">
                              <AlertCircle className="w-3 h-3 mr-1" />
                              Chưa xác minh
                            </Badge>
                          )}
                        </td>
                        <td className="py-3 px-4">
                          <Badge variant={getSourceColor(food.source) as any}>
                            {getSourceLabel(food.source)}
                          </Badge>
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex items-center justify-end gap-1">
                            {/* View Detail */}
                            <button
                              onClick={() => {
                                setSelectedFood(food);
                                setShowDetailModal(true);
                              }}
                              className="p-2 text-gray-400 hover:text-primary hover:bg-primary/5 rounded-lg transition-colors"
                              title="Xem chi tiết"
                            >
                              <Eye className="w-4 h-4" />
                            </button>

                            {/* Verify/Unverify */}
                            <button
                              onClick={() => {
                                setConfirmAction({
                                  type: food.is_verified ? 'unverify' : 'verify',
                                  food,
                                });
                                setShowConfirmModal(true);
                              }}
                              className={`p-2 rounded-lg transition-colors ${
                                food.is_verified
                                  ? 'text-gray-400 hover:text-yellow-500 hover:bg-yellow-50'
                                  : 'text-gray-400 hover:text-green-500 hover:bg-green-50'
                              }`}
                              title={food.is_verified ? 'Hủy xác minh' : 'Xác minh'}
                            >
                              {food.is_verified ? (
                                <XCircle className="w-4 h-4" />
                              ) : (
                                <CheckCircle className="w-4 h-4" />
                              )}
                            </button>

                            {/* Delete */}
                            <button
                              onClick={() => {
                                setConfirmAction({ type: 'delete', food });
                                setShowConfirmModal(true);
                              }}
                              className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                              title="Xóa thực phẩm"
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
              <AlertCircle className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500">Không tìm thấy thực phẩm nào</p>
            </div>
          )}
        </CardBody>
      </Card>

      {/* Food Detail Modal */}
      <Modal
        isOpen={showDetailModal}
        onClose={() => setShowDetailModal(false)}
        title="Chi tiết thực phẩm"
      >
        {selectedFood && (
          <div className="space-y-4">
            {selectedFood.image_url && (
              <img
                src={selectedFood.image_url}
                alt={selectedFood.name_vi}
                className="w-full h-48 object-cover rounded-lg"
              />
            )}

            <div>
              <h3 className="text-lg font-semibold">{selectedFood.name_vi}</h3>
              {selectedFood.name_en && (
                <p className="text-gray-500">{selectedFood.name_en}</p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500">Danh mục</p>
                <Badge variant="default" className="mt-1">{selectedFood.category}</Badge>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500">Nguồn</p>
                <Badge variant={getSourceColor(selectedFood.source) as any} className="mt-1">
                  {getSourceLabel(selectedFood.source)}
                </Badge>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500">Xác minh</p>
                <Badge variant={selectedFood.is_verified ? 'success' : 'warning'} className="mt-1">
                  {selectedFood.is_verified ? 'Đã xác minh' : 'Chưa xác minh'}
                </Badge>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500">Barcode</p>
                <p className="font-medium mt-1">{selectedFood.barcode || 'N/A'}</p>
              </div>
            </div>

            {/* Nutrition Info */}
            <div className="p-4 bg-gray-50 rounded-lg">
              <h4 className="font-medium mb-3">Thông tin dinh dưỡng (cho 100g)</h4>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Năng lượng:</span>
                  <span className="font-medium">{selectedFood.calories_per_100g} kcal</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Protein:</span>
                  <span className="font-medium">{selectedFood.protein_per_100g}g</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Carbohydrate:</span>
                  <span className="font-medium">{selectedFood.carbs_per_100g}g</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Chất béo:</span>
                  <span className="font-medium">{selectedFood.fat_per_100g}g</span>
                </div>
              </div>
            </div>

            {selectedFood.creator_name && (
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500">Người tạo</p>
                <p className="font-medium mt-1">{selectedFood.creator_name}</p>
              </div>
            )}

            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-500">Ngày tạo</p>
              <p className="font-medium mt-1">
                {format(new Date(selectedFood.created_at), 'dd/MM/yyyy HH:mm', { locale: vi })}
              </p>
            </div>

            <div className="flex gap-2 pt-4">
              {selectedFood.is_verified ? (
                <Button
                  variant="outline"
                  className="flex-1"
                  onClick={() => {
                    setShowDetailModal(false);
                    setConfirmAction({ type: 'unverify', food: selectedFood });
                    setShowConfirmModal(true);
                  }}
                >
                  <XCircle className="w-4 h-4 mr-2" />
                  Hủy xác minh
                </Button>
              ) : (
                <Button
                  variant="outline"
                  className="flex-1"
                  onClick={() => {
                    setShowDetailModal(false);
                    setConfirmAction({ type: 'verify', food: selectedFood });
                    setShowConfirmModal(true);
                  }}
                >
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Xác minh
                </Button>
              )}
              <Button
                variant="danger"
                onClick={() => {
                  setShowDetailModal(false);
                  setConfirmAction({ type: 'delete', food: selectedFood });
                  setShowConfirmModal(true);
                }}
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Xóa
              </Button>
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
            isLoading={verifyFoodMutation.isPending || deleteFoodMutation.isPending}
          >
            Xác nhận
          </Button>
        </div>
      </Modal>
    </div>
  );
}
