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
  EyeOff,
  Globe,
} from 'lucide-react';
import { Card, CardBody, CardHeader, Button, Badge, Input, Skeleton, Modal, useToast } from '../../components/ui';
import { adminRecipesApi, type AdminRecipe } from '../../api/admin';
import { format } from 'date-fns';
import { vi } from 'date-fns/locale';

type AdminRecipeWithDescription = AdminRecipe & { description?: string | null };

export default function AdminRecipes() {
  const toast = useToast();
  const queryClient = useQueryClient();

  // Filters
  const [search, setSearch] = useState('');
  const [filterVerified, setFilterVerified] = useState<boolean | undefined>(undefined);
  const [filterDifficulty, setFilterDifficulty] = useState<string>('');
  const [page, setPage] = useState(0);
  const [selectedRecipe, setSelectedRecipe] = useState<AdminRecipeWithDescription | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [confirmAction, setConfirmAction] = useState<{
    type: 'verify' | 'unverify' | 'public' | 'private' | 'delete';
    recipe: AdminRecipe;
  } | null>(null);

  const limit = 15;

  const { data, isLoading } = useQuery<{ total: number; recipes: AdminRecipe[] }>({
    queryKey: ['admin', 'recipes', page, search, filterVerified, filterDifficulty],
    queryFn: () =>
      adminRecipesApi.list({
        skip: page * limit,
        limit,
        search: search || undefined,
        is_verified: filterVerified,
        difficulty: filterDifficulty || undefined,
      }),
  });

  // Verify recipe mutation
  const verifyRecipeMutation = useMutation({
    mutationFn: ({ recipeId, isVerified }: { recipeId: string; isVerified: boolean }) =>
      adminRecipesApi.verify(recipeId, isVerified),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'recipes'] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'stats'] });
      toast.success('Cập nhật trạng thái thành công');
      setShowConfirmModal(false);
      setConfirmAction(null);
    },
    onError: () => {
      toast.error('Cập nhật thất bại');
    },
  });

  // Toggle visibility mutation
  const toggleVisibilityMutation = useMutation({
    mutationFn: ({ recipeId, isPublic }: { recipeId: string; isPublic: boolean }) =>
      adminRecipesApi.toggleVisibility(recipeId, isPublic),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'recipes'] });
      toast.success('Cập nhật trạng thái công khai thành công');
      setShowConfirmModal(false);
      setConfirmAction(null);
    },
    onError: () => {
      toast.error('Cập nhật thất bại');
    },
  });

  // Delete recipe mutation
  const deleteRecipeMutation = useMutation({
    mutationFn: (recipeId: string) => adminRecipesApi.delete(recipeId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'recipes'] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'stats'] });
      toast.success('Xóa công thức thành công');
      setShowConfirmModal(false);
      setConfirmAction(null);
    },
    onError: () => {
      toast.error('Xóa công thức thất bại');
    },
  });

  const handleConfirmAction = () => {
    if (!confirmAction) return;
    const { type, recipe } = confirmAction;
    if (type === 'delete') {
      deleteRecipeMutation.mutate(recipe.recipe_id);
    } else if (type === 'verify') {
      verifyRecipeMutation.mutate({ recipeId: recipe.recipe_id, isVerified: true });
    } else if (type === 'unverify') {
      verifyRecipeMutation.mutate({ recipeId: recipe.recipe_id, isVerified: false });
    } else if (type === 'public') {
      toggleVisibilityMutation.mutate({ recipeId: recipe.recipe_id, isPublic: true });
    } else if (type === 'private') {
      toggleVisibilityMutation.mutate({ recipeId: recipe.recipe_id, isPublic: false });
    }
  };

  const getConfirmMessage = () => {
    if (!confirmAction) return '';
    const { type, recipe } = confirmAction;
    switch (type) {
      case 'verify':
        return `Bạn có chắc muốn xác minh công thức "${recipe.name_vi}"?`;
      case 'unverify':
        return `Bạn có chắc muốn hủy xác minh công thức "${recipe.name_vi}"?`;
      case 'public':
        return `Bạn có chắc muốn công khai công thức "${recipe.name_vi}"?`;
      case 'private':
        return `Bạn có chắc muốn ẩn công thức "${recipe.name_vi}"?`;
      case 'delete':
        return `⚠️ Cảnh báo: Bạn có chắc muốn xóa công thức "${recipe.name_vi}"? Hành động này không thể hoàn tác.`;
      default:
        return '';
    }
  };

  const totalPages = data?.total ? Math.ceil(data.total / limit) : 0;

  const getDifficultyColor = (difficulty: string | null) => {
    switch (difficulty) {
      case 'easy':
        return 'success';
      case 'medium':
        return 'warning';
      case 'hard':
        return 'error';
      default:
        return 'default';
    }
  };

  const getDifficultyLabel = (difficulty: string | null) => {
    switch (difficulty) {
      case 'easy':
        return 'Dễ';
      case 'medium':
        return 'Trung bình';
      case 'hard':
        return 'Khó';
      default:
        return 'N/A';
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Quản lý công thức</h1>
        <p className="text-sm text-gray-500 mt-1">
          Quản lý công thức nấu ăn, xác minh và kiểm duyệt nội dung
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
                  placeholder="Tìm theo tên công thức..."
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
                value={filterDifficulty}
                onChange={(e) => {
                  setFilterDifficulty(e.target.value);
                  setPage(0);
                }}
                className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
              >
                <option value="">Tất cả độ khó</option>
                <option value="easy">Dễ</option>
                <option value="medium">Trung bình</option>
                <option value="hard">Khó</option>
              </select>
            </div>
          </div>

          {/* Active Filters */}
          {(filterVerified !== undefined || filterDifficulty || search) && (
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
              {filterDifficulty && (
                <Badge
                  variant="default"
                  className="cursor-pointer"
                  onClick={() => setFilterDifficulty('')}
                >
                  {getDifficultyLabel(filterDifficulty)} <X className="w-3 h-3 ml-1" />
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
                  setFilterDifficulty('');
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

      {/* Recipes List */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-gray-900">
              Danh sách công thức
              {data?.total !== undefined && (
                <span className="ml-2 text-sm font-normal text-gray-500">
                  ({data.total.toLocaleString()} công thức)
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
          ) : data?.recipes && data.recipes.length > 0 ? (
            <>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-100">
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Công thức</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Danh mục</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Dinh dưỡng</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Trạng thái</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Thống kê</th>
                      <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">Hành động</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.recipes.map((recipe) => (
                      <tr key={recipe.recipe_id} className="border-b border-gray-50 hover:bg-gray-50">
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-3">
                            {recipe.image_url ? (
                              <img
                                src={recipe.image_url}
                                alt={recipe.name_vi}
                                className="w-12 h-12 rounded-lg object-cover"
                              />
                            ) : (
                              <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                                <span className="text-gray-400 text-xs">No img</span>
                              </div>
                            )}
                            <div>
                              <p className="font-medium text-gray-900">{recipe.name_vi}</p>
                              <p className="text-xs text-gray-500">
                                {recipe.prep_time_minutes && recipe.cook_time_minutes
                                  ? `${recipe.prep_time_minutes + recipe.cook_time_minutes} phút`
                                  : recipe.prep_time_minutes
                                  ? `${recipe.prep_time_minutes} phút`
                                  : recipe.cook_time_minutes
                                  ? `${recipe.cook_time_minutes} phút`
                                  : 'N/A'}
                              </p>
                            </div>
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <Badge variant="default">{recipe.category}</Badge>
                          {recipe.difficulty_level && (
                            <Badge
                              variant={getDifficultyColor(recipe.difficulty_level) as any}
                              className="ml-1"
                            >
                              {getDifficultyLabel(recipe.difficulty_level)}
                            </Badge>
                          )}
                        </td>
                        <td className="py-3 px-4">
                          {recipe.calories_per_serving ? (
                            <div className="text-sm">
                              <span className="font-medium">{recipe.calories_per_serving} kcal</span>
                              <p className="text-xs text-gray-500">
                                P: {recipe.protein_per_serving || 0}g | C: {recipe.carbs_per_serving || 0}g
                              </p>
                            </div>
                          ) : (
                            <span className="text-sm text-gray-500">Chưa có</span>
                          )}
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex flex-col gap-1">
                            {recipe.is_verified ? (
                              <Badge variant="success" className="w-fit">
                                <CheckCircle className="w-3 h-3 mr-1" />
                                Đã xác minh
                              </Badge>
                            ) : (
                              <Badge variant="warning" className="w-fit">
                                <AlertCircle className="w-3 h-3 mr-1" />
                                Chưa xác minh
                              </Badge>
                            )}
                            {recipe.is_public ? (
                              <Badge variant="info" className="w-fit">
                                <Globe className="w-3 h-3 mr-1" />
                                Công khai
                              </Badge>
                            ) : (
                              <Badge variant="default" className="w-fit">
                                <EyeOff className="w-3 h-3 mr-1" />
                                Riêng tư
                              </Badge>
                            )}
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <div className="text-xs text-gray-500 space-y-1">
                            <div>
                              <span className="text-gray-600">Lượt xem:</span> {recipe.view_count}
                            </div>
                            <div>
                              <span className="text-gray-600">Yêu thích:</span> {recipe.favorite_count}
                            </div>
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex items-center justify-end gap-1">
                            {/* View Detail */}
                            <button
                              onClick={() => {
                                setSelectedRecipe(recipe);
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
                                  type: recipe.is_verified ? 'unverify' : 'verify',
                                  recipe,
                                });
                                setShowConfirmModal(true);
                              }}
                              className={`p-2 rounded-lg transition-colors ${
                                recipe.is_verified
                                  ? 'text-gray-400 hover:text-yellow-500 hover:bg-yellow-50'
                                  : 'text-gray-400 hover:text-green-500 hover:bg-green-50'
                              }`}
                              title={recipe.is_verified ? 'Hủy xác minh' : 'Xác minh'}
                            >
                              {recipe.is_verified ? (
                                <XCircle className="w-4 h-4" />
                              ) : (
                                <CheckCircle className="w-4 h-4" />
                              )}
                            </button>

                            {/* Public/Private */}
                            <button
                              onClick={() => {
                                setConfirmAction({
                                  type: recipe.is_public ? 'private' : 'public',
                                  recipe,
                                });
                                setShowConfirmModal(true);
                              }}
                              className="p-2 text-gray-400 hover:text-blue-500 hover:bg-blue-50 rounded-lg transition-colors"
                              title={recipe.is_public ? 'Ẩn công thức' : 'Công khai công thức'}
                            >
                              {recipe.is_public ? (
                                <EyeOff className="w-4 h-4" />
                              ) : (
                                <Globe className="w-4 h-4" />
                              )}
                            </button>

                            {/* Delete */}
                            <button
                              onClick={() => {
                                setConfirmAction({ type: 'delete', recipe });
                                setShowConfirmModal(true);
                              }}
                              className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                              title="Xóa công thức"
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
              <p className="text-gray-500">Không tìm thấy công thức nào</p>
            </div>
          )}
        </CardBody>
      </Card>

      {/* Recipe Detail Modal */}
      <Modal
        isOpen={showDetailModal}
        onClose={() => setShowDetailModal(false)}
        title="Chi tiết công thức"
      >
        {selectedRecipe && (
          <div className="space-y-4">
            {selectedRecipe.image_url && (
              <img
                src={selectedRecipe.image_url}
                alt={selectedRecipe.name_vi}
                className="w-full h-48 object-cover rounded-lg"
              />
            )}

            <div>
              <h3 className="text-lg font-semibold">{selectedRecipe.name_vi}</h3>
              {selectedRecipe.name_en && (
                <p className="text-gray-500">{selectedRecipe.name_en}</p>
              )}
              {selectedRecipe.description && (
                <p className="text-sm text-gray-600 mt-2">{selectedRecipe.description}</p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500">Danh mục</p>
                <Badge variant="default" className="mt-1">{selectedRecipe.category}</Badge>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500">Độ khó</p>
                <Badge variant={getDifficultyColor(selectedRecipe.difficulty_level) as any} className="mt-1">
                  {getDifficultyLabel(selectedRecipe.difficulty_level)}
                </Badge>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500">Thời gian</p>
                <p className="font-medium mt-1">
                  {selectedRecipe.prep_time_minutes && selectedRecipe.cook_time_minutes
                    ? `${selectedRecipe.prep_time_minutes + selectedRecipe.cook_time_minutes} phút`
                    : 'N/A'}
                </p>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500">Khẩu phần</p>
                <p className="font-medium mt-1">{selectedRecipe.servings} người</p>
              </div>
            </div>

            {/* Nutrition Info */}
            {selectedRecipe.calories_per_serving && (
              <div className="p-4 bg-gray-50 rounded-lg">
                <h4 className="font-medium mb-3">Thông tin dinh dưỡng (mỗi khẩu phần)</h4>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Năng lượng:</span>
                    <span className="font-medium">{selectedRecipe.calories_per_serving} kcal</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Protein:</span>
                    <span className="font-medium">{selectedRecipe.protein_per_serving || 0}g</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Carbohydrate:</span>
                    <span className="font-medium">{selectedRecipe.carbs_per_serving || 0}g</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Chất béo:</span>
                    <span className="font-medium">{selectedRecipe.fat_per_serving || 0}g</span>
                  </div>
                </div>
              </div>
            )}

            {/* Stats */}
            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500">Lượt xem</p>
                <p className="font-medium mt-1">{selectedRecipe.view_count}</p>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500">Yêu thích</p>
                <p className="font-medium mt-1">{selectedRecipe.favorite_count}</p>
              </div>
            </div>

            {selectedRecipe.creator_name && (
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500">Người tạo</p>
                <p className="font-medium mt-1">{selectedRecipe.creator_name}</p>
              </div>
            )}

            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-500">Ngày tạo</p>
              <p className="font-medium mt-1">
                {format(new Date(selectedRecipe.created_at), 'dd/MM/yyyy HH:mm', { locale: vi })}
              </p>
            </div>

            <div className="flex gap-2 pt-4">
              {selectedRecipe.is_verified ? (
                <Button
                  variant="outline"
                  className="flex-1"
                  onClick={() => {
                    setShowDetailModal(false);
                    setConfirmAction({ type: 'unverify', recipe: selectedRecipe });
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
                    setConfirmAction({ type: 'verify', recipe: selectedRecipe });
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
                  setConfirmAction({ type: 'delete', recipe: selectedRecipe });
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
            isLoading={
              verifyRecipeMutation.isPending ||
              toggleVisibilityMutation.isPending ||
              deleteRecipeMutation.isPending
            }
          >
            Xác nhận
          </Button>
        </div>
      </Modal>
    </div>
  );
}
