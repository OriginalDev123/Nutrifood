import { useQuery, useMutation } from '@tanstack/react-query';
import { Plus, Calendar, Trash2, Eye } from 'lucide-react';
import { Card, CardBody, CardHeader, Button, Badge, EmptyState, Skeleton, useToast } from '../../components/ui';
import { PageContainer } from '../../components/layout';
import { mealPlanApi } from '../../api/mealPlan';
import { useNavigate } from 'react-router-dom';

export default function MealPlanListPage() {
  const navigate = useNavigate();
  const toast = useToast();

  const { data: mealPlans, isLoading } = useQuery({
    queryKey: ['mealPlans'],
    queryFn: () => mealPlanApi.getMyPlans(),
  });

  const deleteMutation = useMutation({
    mutationFn: (planId: string) => mealPlanApi.deletePlan(planId),
    onSuccess: () => {
      toast.success('Đã xóa kế hoạch');
    },
    onError: () => {
      toast.error('Xóa thất bại');
    },
  });

  const getPlanStatus = (plan: any) => {
    if (plan?.status) return plan.status;
    if (plan?.is_completed) return 'completed';
    if (plan?.is_active) return 'active';
    return 'archived';
  };

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
      title="Kế hoạch ăn uống"
      subtitle="Quản lý các kế hoạch ăn uống của bạn"
      action={
        <Button onClick={() => navigate('/meal-plans/new')} leftIcon={<Plus className="w-4 h-4" />}>
          Tạo kế hoạch mới
        </Button>
      }
    >
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map(i => <Skeleton key={i} className="h-48 w-full rounded-xl" />)}
        </div>
      ) : mealPlans && mealPlans.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {mealPlans.map(plan => (
            <Card key={plan.plan_id}>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <h3 className="font-semibold text-gray-900">{plan.plan_name}</h3>
                  <p className="text-sm text-gray-500">{plan.total_days ?? '-'} ngày</p>
                </div>
                <Badge variant={getStatusColor(getPlanStatus(plan)) as any}>
                  {getStatusLabel(getPlanStatus(plan))}
                </Badge>
              </CardHeader>
              <CardBody className="space-y-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-500">Tổng calories:</span>
                  <span className="font-medium text-primary">{Math.round(plan.total_calories ?? 0)} kcal</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-500">Thời gian:</span>
                  <span className="text-gray-700">
                    {new Date(plan.start_date).toLocaleDateString('vi-VN')} - {new Date(plan.end_date).toLocaleDateString('vi-VN')}
                  </span>
                </div>
                <div className="flex gap-2 pt-2">
                  <Button
                    size="sm"
                    variant="outline"
                    className="flex-1"
                    onClick={() => navigate(`/meal-plans/${plan.plan_id}`)}
                    leftIcon={<Eye className="w-4 h-4" />}
                  >
                    Xem
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => deleteMutation.mutate(plan.plan_id)}
                  >
                    <Trash2 className="w-4 h-4 text-red-500" />
                  </Button>
                </div>
              </CardBody>
            </Card>
          ))}
        </div>
      ) : (
        <EmptyState
          icon={<Calendar className="w-8 h-8" />}
          title="Chưa có kế hoạch nào"
          description="Tạo kế hoạch ăn uống để bắt đầu"
          action={{ label: 'Tạo kế hoạch', onClick: () => navigate('/meal-plans/new') }}
        />
      )}
    </PageContainer>
  );
}