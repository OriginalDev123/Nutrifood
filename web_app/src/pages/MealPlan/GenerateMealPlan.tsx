import { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, Sparkles, Calendar, Clock, UtensilsCrossed, Heart, AlertTriangle } from 'lucide-react';
import { Card, CardBody, CardHeader, Button, Input, Badge, useToast, Modal } from '../../components/ui';
import { PageContainer } from '../../components/layout';
import { mealPlanApi } from '../../api/mealPlan';
import { healthProfileApi, type HealthProfileData } from '../../api/healthProfile';
import { HealthProfileModal, HealthProfileDisplay } from '../../components/health';
import type { MealPlanItem, MealPlanWithItems } from '../../api/extended';
import { useDeleteMealPlan } from '../../hooks/useDeleteMealPlan';

const MEAL_TYPE_VI: Record<MealPlanItem['meal_type'], string> = {
  breakfast: 'Sáng',
  lunch: 'Trưa',
  dinner: 'Tối',
  snack: 'Phụ',
};

function mealItemLabel(item: MealPlanItem): string {
  if (item.recipe_name) return item.recipe_name;
  if (item.food_name) return item.food_name;
  // Handle both "Recipe: " (from database) and "Custom: " (from AI)
  if (item.notes) {
    if (item.notes.startsWith('Recipe: ')) {
      return item.notes.replace('Recipe: ', '');
    }
    if (item.notes.startsWith('Custom: ')) {
      // Extract food name from "Custom: {name} | Nguyên liệu: ..."
      const customPart = item.notes.replace('Custom: ', '');
      const pipeIndex = customPart.indexOf(' | ');
      if (pipeIndex > 0) {
        return customPart.substring(0, pipeIndex);
      }
      return customPart;
    }
  }
  return 'Món ăn';
}

function MealPlanPreviewSummary({ plan }: { plan: MealPlanWithItems }) {
  const dayCount = plan.days?.length ?? 0;
  const avgDaily =
    dayCount > 0 ? Math.round((plan.total_calories || 0) / dayCount) : 0;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-sm">
        <div className="p-3 bg-gray-50 rounded-lg">
          <p className="text-gray-500 text-xs mb-0.5">Thời gian</p>
          <p className="font-medium text-gray-900">
            {new Date(plan.start_date).toLocaleDateString('vi-VN')} —{' '}
            {new Date(plan.end_date).toLocaleDateString('vi-VN')}
          </p>
        </div>
        <div className="p-3 bg-gray-50 rounded-lg">
          <p className="text-gray-500 text-xs mb-0.5">Số ngày</p>
          <p className="font-medium text-gray-900">{dayCount} ngày</p>
        </div>
        <div className="p-3 bg-gray-50 rounded-lg col-span-2 sm:col-span-1">
          <p className="text-gray-500 text-xs mb-0.5">Tổng / TB ngày</p>
          <p className="font-medium text-gray-900">
            {Math.round(plan.total_calories || 0)} kcal · ~{avgDaily} kcal/ngày
          </p>
        </div>
      </div>

      <div>
        <p className="text-sm font-medium text-gray-700 mb-2">Tóm tắt theo ngày</p>
        <div className="space-y-2 max-h-[min(50vh,420px)] overflow-y-auto pr-1 border border-gray-100 rounded-lg p-3 bg-white">
          {(plan.days ?? []).map((day) => (
            <div
              key={`${day.day_number}-${day.date}`}
              className="text-sm border-b border-gray-100 last:border-0 pb-2 last:pb-0"
            >
              <p className="font-medium text-gray-900">
                Ngày {day.day_number} · {new Date(day.date).toLocaleDateString('vi-VN')}
                <span className="text-gray-500 font-normal ml-2">
                  ({Math.round(day.total_calories || 0)} kcal)
                </span>
              </p>
              <ul className="mt-1 text-gray-600 space-y-0.5 pl-0 list-none">
                {(day.items ?? []).map((item) => (
                  <li key={item.item_id} className="flex gap-2">
                    <span className="text-primary shrink-0 w-12">
                      {MEAL_TYPE_VI[item.meal_type]}:
                    </span>
                    <span className="truncate">{mealItemLabel(item)}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function GenerateMealPlanPage() {
  const navigate = useNavigate();
  const toast = useToast();
  const queryClient = useQueryClient();

  const [formData, setFormData] = useState({
    plan_name: '',
    days: 7,
    categories: '',
    tags: '',
    max_cook_time: '',
  });

  // Health profile state
  const [healthProfile, setHealthProfile] = useState<HealthProfileData | null>(null);
  const [isHealthProfileModalOpen, setIsHealthProfileModalOpen] = useState(false);

  const [previewPlan, setPreviewPlan] = useState<MealPlanWithItems | null>(null);

  // Load saved health profile
  const { data: savedHealthProfile, refetch: refetchHealthProfile } = useQuery({
    queryKey: ['healthProfile'],
    queryFn: () => healthProfileApi.getMyProfile(),
    retry: false,
    onSuccess: (data) => {
      setHealthProfile(data);
    },
  });

  const closePreview = useCallback(() => {
    setPreviewPlan(null);
  }, []);

  const generateMutation = useMutation({
    mutationFn: () =>
      mealPlanApi.generateMealPlan({
        plan_name: formData.plan_name || `Kế hoạch ăn ${new Date().toLocaleDateString('vi-VN')}`,
        days: formData.days,
        categories: formData.categories || undefined,
        tags: formData.tags || undefined,
        max_cook_time: formData.max_cook_time ? parseInt(formData.max_cook_time, 10) : undefined,
        health_profile: healthProfile || undefined,
      }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['mealPlans'] });
      toast.success('Đã tạo kế hoạch ăn uống!');
      setPreviewPlan(data);
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Tạo kế hoạch thất bại');
    },
  });

  const deletePreviewMutation = useDeleteMealPlan({
    onSuccess: () => {
      toast.success('Đã hủy kế hoạch');
      closePreview();
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Không thể hủy kế hoạch');
    },
  });

  // Save health profile mutation
  const saveHealthProfileMutation = useMutation({
    mutationFn: (data: HealthProfileData) => healthProfileApi.updateMyProfile(data),
    onSuccess: (data) => {
      setHealthProfile(data);
      setIsHealthProfileModalOpen(false);
      toast.success('Đã lưu thông tin thể trạng!');
      refetchHealthProfile();
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Lưu thể trạng thất bại');
    },
  });

  const handleSubmit = () => {
    if (!formData.plan_name.trim()) {
      toast.error('Vui lòng nhập tên kế hoạch');
      return;
    }
    generateMutation.mutate();
  };

  const handleUsePlan = () => {
    if (!previewPlan) return;
    const id = previewPlan.plan_id;
    closePreview();
    queryClient.invalidateQueries({ queryKey: ['mealPlan', id] });
    navigate(`/meal-plans/${id}`);
  };

  const handleCancelPlan = () => {
    if (!previewPlan || deletePreviewMutation.isPending) return;
    deletePreviewMutation.mutate(previewPlan.plan_id);
  };

  const handleSaveHealthProfile = (data: HealthProfileData) => {
    saveHealthProfileMutation.mutate(data);
  };

  const hasHealthProfileData = healthProfile && (
    (healthProfile.health_conditions && healthProfile.health_conditions.length > 0) ||
    (healthProfile.food_allergies && healthProfile.food_allergies.length > 0) ||
    (healthProfile.dietary_preferences && healthProfile.dietary_preferences.length > 0)
  );

  return (
    <PageContainer
      title="Tạo kế hoạch ăn uống"
      subtitle="Sử dụng AI để tạo kế hoạch ăn uống phù hợp với mục tiêu và thể trạng của bạn"
      action={
        <Button variant="outline" onClick={() => navigate('/meal-plans')}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Quay lại
        </Button>
      }
    >
      <div className="max-w-2xl mx-auto space-y-6">
        {/* Info Card */}
        <Card className="bg-gradient-to-r from-primary/5 to-emerald-50 border border-primary/20">
          <CardBody className="flex items-start gap-4">
            <div className="p-3 bg-primary/10 rounded-xl">
              <Sparkles className="w-8 h-8 text-primary" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-1">Kế hoạch cá nhân hóa</h3>
              <p className="text-sm text-gray-600">
                AI sẽ tạo kế hoạch ăn uống dựa trên mục tiêu dinh dưỡng, sở thích và thể trạng của bạn.
                Đảm bảo bạn đã thiết lập mục tiêu trước khi tạo kế hoạch.
              </p>
            </div>
          </CardBody>
        </Card>

        {/* Form */}
        <Card>
          <CardHeader>
            <h2 className="font-semibold text-gray-900">Cấu hình kế hoạch</h2>
          </CardHeader>
          <CardBody className="space-y-4">
            <Input
              label="Tên kế hoạch"
              value={formData.plan_name}
              onChange={(e) => setFormData({ ...formData, plan_name: e.target.value })}
              placeholder="Ví dụ: Kế hoạch giảm cân tuần này"
              leftIcon={<Calendar className="w-5 h-5" />}
            />

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Số ngày</label>
                <select
                  value={formData.days}
                  onChange={(e) => setFormData({ ...formData, days: parseInt(e.target.value, 10) })}
                  className="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:border-primary focus:ring-2 focus:ring-primary/20"
                >
                  <option value={1}>1 ngày</option>
                  <option value={3}>3 ngày</option>
                  <option value={5}>5 ngày</option>
                  <option value={7}>7 ngày</option>
                  <option value={14}>14 ngày</option>
                  <option value={21}>21 ngày</option>
                  <option value={30}>30 ngày</option>
                </select>
              </div>

              <Input
                label="Thời gian nấu tối đa (phút)"
                type="number"
                value={formData.max_cook_time}
                onChange={(e) => setFormData({ ...formData, max_cook_time: e.target.value })}
                placeholder="60"
                leftIcon={<Clock className="w-5 h-5" />}
              />
            </div>

            <Input
              label="Danh mục (tùy chọn)"
              value={formData.categories}
              onChange={(e) => setFormData({ ...formData, categories: e.target.value })}
              placeholder="Soup, Main Course, Salad (phân cách bằng dấu phẩy)"
              helperText="Để trống nếu muốn chọn tất cả danh mục"
            />

            <Input
              label="Tags (tùy chọn)"
              value={formData.tags}
              onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
              placeholder="healthy, quick, vegetarian (phân cách bằng dấu phẩy)"
              helperText="Lọc công thức theo tags"
            />

            {/* Health Profile Section */}
            <div className="p-4 bg-gray-50 rounded-xl space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <UtensilsCrossed className="w-5 h-5 text-gray-500" />
                  <span className="font-medium text-gray-700">Thể trạng của bạn</span>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setIsHealthProfileModalOpen(true)}
                >
                  {hasHealthProfileData ? 'Cập nhật thể trạng' : 'Nhập thể trạng'}
                </Button>
              </div>

              {/* Display saved health profile */}
              {hasHealthProfileData && healthProfile && (
                <div className="bg-white rounded-lg p-3 border border-gray-100">
                  <HealthProfileDisplay data={healthProfile} compact />
                </div>
              )}

              {!hasHealthProfileData && (
                <p className="text-sm text-gray-500 italic">
                  Nhập thông tin thể trạng để AI đề xuất thực đơn phù hợp với bạn.
                </p>
              )}
            </div>

            {/* Preferences Preview */}
            <div className="p-4 bg-gray-50 rounded-xl">
              <div className="flex items-center gap-2 mb-3">
                <span className="font-medium text-gray-700">Tùy chọn đã chọn:</span>
              </div>
              <div className="flex flex-wrap gap-2">
                <Badge>{formData.days} ngày</Badge>
                {formData.tags &&
                  formData.tags.split(',').map((tag) => (
                    <Badge key={tag.trim()} variant="info">
                      {tag.trim()}
                    </Badge>
                  ))}
                {formData.max_cook_time && (
                  <Badge variant="warning">Nấu &lt; {formData.max_cook_time} phút</Badge>
                )}
                {hasHealthProfileData && (
                  <>
                    {healthProfile?.food_allergies && healthProfile.food_allergies.length > 0 && (
                      <Badge variant="danger">
                        <AlertTriangle className="w-3 h-3 mr-1" />
                        {healthProfile.food_allergies.length} dị ứng
                      </Badge>
                    )}
                    {healthProfile?.dietary_preferences && healthProfile.dietary_preferences.length > 0 && (
                      <Badge variant="success">
                        <Heart className="w-3 h-3 mr-1" />
                        {healthProfile.dietary_preferences.length} chế độ ăn
                      </Badge>
                    )}
                  </>
                )}
              </div>
            </div>
          </CardBody>
        </Card>

        {/* Submit */}
        <Button
          onClick={handleSubmit}
          isLoading={generateMutation.isPending}
          className="w-full"
          size="lg"
          leftIcon={<Sparkles className="w-5 h-5" />}
        >
          Tạo kế hoạch với AI
        </Button>
      </div>

      {/* Health Profile Modal */}
      <HealthProfileModal
        isOpen={isHealthProfileModalOpen}
        onClose={() => setIsHealthProfileModalOpen(false)}
        onSave={handleSaveHealthProfile}
        initialData={healthProfile || undefined}
        isLoading={saveHealthProfileMutation.isPending}
      />

      {/* Preview Modal */}
      <Modal
        isOpen={!!previewPlan}
        onClose={closePreview}
        title={previewPlan ? `Xem trước: ${previewPlan.plan_name}` : 'Xem trước kế hoạch'}
        size="full"
        footer={
          previewPlan ? (
            <div className="flex flex-col-reverse sm:flex-row gap-2 sm:justify-end">
              <Button
                variant="danger"
                onClick={handleCancelPlan}
                isLoading={deletePreviewMutation.isPending}
                disabled={deletePreviewMutation.isPending}
              >
                Hủy kế hoạch
              </Button>
              <Button
                variant="primary"
                onClick={handleUsePlan}
                disabled={deletePreviewMutation.isPending}
              >
                Sử dụng kế hoạch
              </Button>
            </div>
          ) : null
        }
      >
        {previewPlan ? <MealPlanPreviewSummary plan={previewPlan} /> : null}
      </Modal>
    </PageContainer>
  );
}
