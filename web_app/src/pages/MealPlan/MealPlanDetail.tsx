import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, ShoppingCart, BarChart3, RefreshCw, Calendar, Flame, Beef, Wheat, ChefHat } from 'lucide-react';
import { Card, CardBody, Button, Badge, TabList, Skeleton, useToast } from '../../components/ui';
import { PageContainer } from '../../components/layout';
import { mealPlanApi } from '../../api/mealPlan';
import { useDeleteMealPlan } from '../../hooks/useDeleteMealPlan';

export default function MealPlanDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const toast = useToast();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('meals');

  // Fetch meal plan detail
  const { data: plan, isLoading, error } = useQuery({
    queryKey: ['mealPlan', id],
    queryFn: () => mealPlanApi.getPlanDetail(id!),
    enabled: !!id,
  });

  // Fetch shopping list
  const { data: shoppingList } = useQuery({
    queryKey: ['shoppingList', id],
    queryFn: () => mealPlanApi.getShoppingList(id!),
    enabled: !!id && activeTab === 'shopping',
  });

  // Fetch analysis
  const { data: analysis } = useQuery({
    queryKey: ['mealPlanAnalysis', id],
    queryFn: () => mealPlanApi.analyzeMealPlan(id!),
    enabled: !!id && activeTab === 'analysis',
  });

  const deleteMutation = useDeleteMealPlan({
    onSuccess: () => {
      toast.success('Đã xóa kế hoạch');
      navigate('/meal-plans');
    },
  });

  const regenerateMutation = useMutation({
    mutationFn: async () => {
      if (!id || !plan?.days?.length) {
        throw new Error('Không thể tạo lại kế hoạch');
      }

      await Promise.all(
        plan.days.map((day: any) => mealPlanApi.regenerateDay(id, day.date))
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mealPlan', id] });
      queryClient.invalidateQueries({ queryKey: ['shoppingList', id] });
      queryClient.invalidateQueries({ queryKey: ['mealPlanAnalysis', id] });
      toast.success('Đã tạo lại kế hoạch');
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || error?.message || 'Tạo lại kế hoạch thất bại');
    },
  });

  if (isLoading) {
    return (
      <PageContainer title="Chi tiết kế hoạch">
        <div className="max-w-4xl mx-auto">
          <Skeleton className="h-48 w-full mb-6" />
          <Skeleton className="h-64 w-full" />
        </div>
      </PageContainer>
    );
  }

  if (error || !plan) {
    return (
      <PageContainer title="Chi tiết kế hoạch">
        <div className="text-center py-12">
          <p className="text-gray-500 mb-4">Không tìm thấy kế hoạch này</p>
          <Button variant="outline" onClick={() => navigate('/meal-plans')}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Quay lại danh sách
          </Button>
        </div>
      </PageContainer>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'success';
      case 'completed': return 'info';
      case 'archived': return 'default';
      default: return 'default';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'active': return 'Đang hoạt động';
      case 'completed': return 'Hoàn thành';
      case 'archived': return 'Đã lưu trữ';
      default: return status;
    }
  };

  return (
    <PageContainer
      title={plan.plan_name}
      action={
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => navigate('/meal-plans')}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Quay lại
          </Button>
          <Button
            variant="outline"
            onClick={() => id && deleteMutation.mutate(id)}
            className="text-red-500 hover:bg-red-50"
          >
            Xóa kế hoạch
          </Button>
        </div>
      }
    >
      <div className="max-w-5xl mx-auto">
        {/* Plan Header */}
        <Card className="mb-6">
          <CardBody>
            <div className="flex items-start justify-between mb-4">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <Badge variant={getStatusColor(plan.status || (plan.is_active ? 'active' : 'archived')) as any}>
                    {getStatusLabel(plan.status || (plan.is_active ? 'active' : 'archived'))}
                  </Badge>
                  <span className="text-sm text-gray-500">
                    {new Date(plan.start_date).toLocaleDateString('vi-VN')} - {new Date(plan.end_date).toLocaleDateString('vi-VN')}
                  </span>
                </div>
                <p className="text-gray-600">
                  {plan.days?.length || 0} ngày với {plan.total_calories || 0} kcal tổng cộng
                </p>
              </div>
              <Button
                leftIcon={<RefreshCw className={`w-4 h-4 ${regenerateMutation.isPending ? 'animate-spin' : ''}`} />}
                variant="outline"
                onClick={() => regenerateMutation.mutate()}
                isLoading={regenerateMutation.isPending}
              >
                Tạo lại
              </Button>
            </div>

            {/* Summary Stats */}
            <div className="grid grid-cols-4 gap-4 p-4 bg-gray-50 rounded-xl">
              <div className="text-center">
                <Calendar className="w-5 h-5 mx-auto text-gray-500 mb-1" />
                <p className="text-2xl font-bold text-gray-900">{plan.days?.length || 0}</p>
                <p className="text-xs text-gray-500">ngày</p>
              </div>
              <div className="text-center">
                <Flame className="w-5 h-5 mx-auto text-orange-500 mb-1" />
                <p className="text-2xl font-bold text-orange-600">{Math.round((plan.total_calories || 0) / (plan.days?.length || 1))}</p>
                <p className="text-xs text-gray-500">kcal/ngày TB</p>
              </div>
              <div className="text-center">
                <Beef className="w-5 h-5 mx-auto text-purple-500 mb-1" />
                <p className="text-2xl font-bold text-purple-600">{plan.total_protein || 0}g</p>
                <p className="text-xs text-gray-500">protein TB</p>
              </div>
              <div className="text-center">
                <ChefHat className="w-5 h-5 mx-auto text-green-500 mb-1" />
                <p className="text-2xl font-bold text-green-600">{plan.total_recipes || plan.days?.reduce((sum: number, d: any) => sum + (d.items?.length || 0), 0) || 0}</p>
                <p className="text-xs text-gray-500">món ăn</p>
              </div>
            </div>
          </CardBody>
        </Card>

        {/* Tabs */}
        <Card>
          <TabList className="px-4 border-b border-gray-200">
            <button
              onClick={() => setActiveTab('meals')}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'meals' ? 'border-primary text-primary' : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Các bữa ăn
            </button>
            <button
              onClick={() => setActiveTab('shopping')}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
                activeTab === 'shopping' ? 'border-primary text-primary' : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <ShoppingCart className="w-4 h-4" />
              Danh sách mua sắm
            </button>
            <button
              onClick={() => setActiveTab('analysis')}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
                activeTab === 'analysis' ? 'border-primary text-primary' : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <BarChart3 className="w-4 h-4" />
              Phân tích
            </button>
          </TabList>

          <CardBody className="p-6">
            {activeTab === 'meals' && (
              <div className="space-y-6">
                {plan.days?.map((day: any, dayIndex: number) => (
                  <div key={dayIndex} className="border border-gray-200 rounded-xl overflow-hidden">
                    <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
                      <h3 className="font-semibold text-gray-900">
                        Ngày {day.day_number}: {new Date(day.date).toLocaleDateString('vi-VN', { weekday: 'long', day: 'numeric', month: 'numeric' })}
                      </h3>
                      <p className="text-sm text-gray-500">Tổng: {Math.round(day.total_calories || 0)} kcal</p>
                    </div>
                    <div className="divide-y divide-gray-100">
                      {day.items?.map((item: any, itemIndex: number) => (
                        <div key={itemIndex} className="flex items-center justify-between p-4 hover:bg-gray-50">
                          <div className="flex items-center gap-3">
                            <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold ${
                              item.meal_type === 'breakfast' ? 'bg-yellow-100 text-yellow-700' :
                              item.meal_type === 'lunch' ? 'bg-orange-100 text-orange-700' :
                              item.meal_type === 'dinner' ? 'bg-blue-100 text-blue-700' :
                              'bg-gray-100 text-gray-700'
                            }`}>
                              {item.meal_type === 'breakfast' ? 'S' : item.meal_type === 'lunch' ? 'T' : item.meal_type === 'dinner' ? 'C' : 'Sn'}
                            </div>
                            <div>
                              <p className="font-medium text-gray-900">{item.recipe_name || item.food_name || 'Món ăn'}</p>
                              <p className="text-sm text-gray-500">{item.serving_size_g}g × {item.quantity}</p>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="font-medium text-primary">{Math.round(item.calories || 0)} kcal</p>
                            <p className="text-xs text-gray-500">P: {Math.round(item.protein || 0)}g</p>
                          </div>
                        </div>
                      ))}
                      {(!day.items || day.items.length === 0) && (
                        <div className="p-6 text-center text-gray-500">
                          Không có món ăn trong ngày này
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {activeTab === 'shopping' && (
              <div className="space-y-4">
                <h3 className="font-semibold text-gray-900 mb-4">Danh sách mua sắm</h3>
                {(shoppingList?.shopping_list?.length ?? 0) > 0 ? (
                  <div className="space-y-2">
                    {shoppingList?.shopping_list?.map((item: any, index: number) => (
                      <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div className="flex items-center gap-3">
                          <div className="w-6 h-6 rounded-full border-2 border-gray-300" />
                          <span className="text-gray-900">{item.ingredient_name}</span>
                        </div>
                        <div className="text-right">
                          <span className="font-medium">{item.total_quantity} {item.unit}</span>
                          {item.recipes && item.recipes.length > 0 && (
                            <p className="text-xs text-gray-500">cho {item.recipes.length} công thức</p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-center text-gray-500 py-8">Không có danh sách mua sắm</p>
                )}
              </div>
            )}

            {activeTab === 'analysis' && (
              <div className="space-y-6">
                <h3 className="font-semibold text-gray-900 mb-4">Phân tích kế hoạch</h3>
                {analysis ? (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-4 bg-orange-50 rounded-xl text-center">
                      <Flame className="w-6 h-6 mx-auto text-orange-500 mb-2" />
                      <p className="text-2xl font-bold text-orange-600">{Math.round(analysis.avg_daily_calories || 0)}</p>
                      <p className="text-sm text-gray-500">kcal/ngày TB</p>
                    </div>
                    <div className="p-4 bg-purple-50 rounded-xl text-center">
                      <Beef className="w-6 h-6 mx-auto text-purple-500 mb-2" />
                      <p className="text-2xl font-bold text-purple-600">{Math.round(analysis.avg_daily_protein || 0)}g</p>
                      <p className="text-sm text-gray-500">protein/ngày TB</p>
                    </div>
                    <div className="p-4 bg-yellow-50 rounded-xl text-center">
                      <Wheat className="w-6 h-6 mx-auto text-yellow-500 mb-2" />
                      <p className="text-2xl font-bold text-yellow-600">{Math.round(analysis.avg_daily_carbs || 0)}g</p>
                      <p className="text-sm text-gray-500">carbs/ngày TB</p>
                    </div>
                    <div className="p-4 bg-blue-50 rounded-xl text-center">
                      <p className="text-2xl font-bold text-blue-600">{Math.round(analysis.goal_adherence || 0)}%</p>
                      <p className="text-sm text-gray-500">phù hợp mục tiêu</p>
                    </div>
                  </div>
                ) : (
                  <p className="text-center text-gray-500 py-8">Đang tải phân tích...</p>
                )}
              </div>
            )}
          </CardBody>
        </Card>
      </div>
    </PageContainer>
  );
}