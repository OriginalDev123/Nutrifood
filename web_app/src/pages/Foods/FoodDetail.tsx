import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, Plus, CheckCircle, Flame, Beef, Wheat, Droplets } from 'lucide-react';
import { Card, CardBody, CardHeader, Button, Badge, Skeleton, useToast } from '../../components/ui';
import { PageContainer } from '../../components/layout';
import { foodApi } from '../../api/food';
import type { Food } from '../../api/types';
import type { FoodPortionPreset } from '../../api/food';

export default function FoodDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const toast = useToast();
  const queryClient = useQueryClient();
  const [selectedServing, setSelectedServing] = useState<string>('');
  const [selectedPortionId, setSelectedPortionId] = useState<string>('');
  const [quantity, setQuantity] = useState(1);

  // Fetch food detail
  const { data: food, isLoading, error } = useQuery<Food>({
    queryKey: ['food', id],
    queryFn: () => foodApi.getFoodDetail(id!),
    enabled: !!id,
  });

  const { data: portions = [] } = useQuery<FoodPortionPreset[]>({
    queryKey: ['foodPortions', id],
    queryFn: () => foodApi.getPortions(id!),
    enabled: !!id,
    retry: false,
  });

  if (isLoading) {
    return (
      <PageContainer title="Chi tiết thực phẩm">
        <div className="max-w-2xl mx-auto">
          <Skeleton className="h-64 w-full mb-6" />
          <Skeleton className="h-8 w-1/2 mb-4" />
          <Skeleton className="h-32 w-full" />
        </div>
      </PageContainer>
    );
  }

  if (error || !food) {
    return (
      <PageContainer title="Chi tiết thực phẩm">
        <div className="text-center py-12">
          <p className="text-gray-500 mb-4">Không tìm thấy thực phẩm này</p>
          <Button variant="outline" onClick={() => navigate('/foods')}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Quay lại danh sách
          </Button>
        </div>
      </PageContainer>
    );
  }

  const logFoodMutation = useMutation({
    mutationFn: () => {
      const selectedServingData = food.servings?.find((s) => s.serving_id === selectedServing);
      const selectedPortion = portions.find((portion) => portion.preset_id === selectedPortionId);

      return foodApi.logMeal({
        food_id: food.food_id,
        serving_id: selectedServing || undefined,
        meal_type: 'snack',
        meal_date: new Date().toISOString().split('T')[0],
        quantity,
        serving_size_g: selectedPortion?.grams ?? selectedServingData?.serving_size_g,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['foodLogs'] });
      queryClient.invalidateQueries({ queryKey: ['dailySummary'] });
      toast.success('Đã thêm vào nhật ký ăn');
      navigate('/food-log');
    },
    onError: () => {
      toast.error('Thêm món thất bại');
    },
  });

  const handleLogFood = () => {
    const hasPortions = portions.length > 0;
    const hasServings = !!food.servings?.length;

    if (!hasPortions && !hasServings) {
      toast.error('Món này chưa có khẩu phần để ghi log');
      return;
    }

    if (hasPortions && !selectedPortionId) {
      toast.error('Anh chọn khẩu phần trước nhé');
      return;
    }

    if (!hasPortions && !selectedServing) {
      toast.error('Anh chọn khẩu phần trước nhé');
      return;
    }

    logFoodMutation.mutate();
  };

  return (
    <PageContainer
      title={food.name_vi}
      subtitle={food.category}
      action={
        <Button variant="outline" onClick={() => navigate('/foods')}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Quay lại
        </Button>
      }
    >
      <div className="max-w-3xl mx-auto">
        {/* Food Header Card */}
        <Card className="mb-6">
          <CardBody>
            <div className="flex items-start gap-6">
              <div className="w-32 h-32 bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl flex items-center justify-center">
                <span className="text-6xl">🍎</span>
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <Badge variant={food.is_verified ? 'success' : 'default'}>
                    {food.is_verified ? 'Đã xác minh' : 'Chưa xác minh'}
                  </Badge>
                  {food.barcode && (
                    <Badge variant="info">Barcode: {food.barcode}</Badge>
                  )}
                </div>
                <h2 className="text-2xl font-bold text-gray-900 mb-1">{food.name_vi}</h2>
                {food.name_en && (
                  <p className="text-gray-500 mb-4">{food.name_en}</p>
                )}
                <div className="flex items-center gap-4 text-sm text-gray-500">
                  <span className="px-3 py-1 bg-gray-100 rounded-full">{food.category}</span>
                  {food.brand && <span>Thương hiệu: {food.brand}</span>}
                </div>
              </div>
            </div>
          </CardBody>
        </Card>

        {/* Nutrition Facts */}
        <Card className="mb-6">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-orange-50 rounded-lg">
                <Flame className="w-5 h-5 text-orange-500" />
              </div>
              <h2 className="font-semibold text-gray-900">Thông tin dinh dưỡng</h2>
              <span className="text-sm text-gray-500">(trên 100g)</span>
            </div>
          </CardHeader>
          <CardBody>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <NutritionItem
                icon={<Flame className="w-5 h-5 text-orange-500" />}
                label="Calories"
                value={food.calories_per_100g}
                unit="kcal"
                color="orange"
              />
              <NutritionItem
                icon={<Beef className="w-5 h-5 text-purple-500" />}
                label="Protein"
                value={food.protein_per_100g}
                unit="g"
                color="purple"
              />
              <NutritionItem
                icon={<Wheat className="w-5 h-5 text-yellow-500" />}
                label="Carbs"
                value={food.carbs_per_100g}
                unit="g"
                color="yellow"
              />
              <NutritionItem
                icon={<Droplets className="w-5 h-5 text-blue-500" />}
                label="Fat"
                value={food.fat_per_100g}
                unit="g"
                color="blue"
              />
            </div>

            {food.fiber_per_100g && (
              <div className="mt-4 pt-4 border-t border-gray-100">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Chất xơ</span>
                  <span className="font-medium">{food.fiber_per_100g}g</span>
                </div>
              </div>
            )}

            {food.sugar_per_100g && (
              <div className="mt-2">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Đường</span>
                  <span className="font-medium">{food.sugar_per_100g}g</span>
                </div>
              </div>
            )}

            {food.sodium_per_100g && (
              <div className="mt-2">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Natri</span>
                  <span className="font-medium">{food.sodium_per_100g}mg</span>
                </div>
              </div>
            )}
          </CardBody>
        </Card>

        {/* Serving Sizes */}
        {(food.servings && food.servings.length > 0) || portions.length > 0 ? (
          <Card className="mb-6">
            <CardHeader>
              <h2 className="font-semibold text-gray-900">Kích thước phần ăn</h2>
            </CardHeader>
            <CardBody>
              <div className="space-y-3">
                {portions.length > 0 ? (
                  portions.map((portion) => (
                    <div
                      key={portion.preset_id}
                      className={`flex items-center justify-between p-4 rounded-xl cursor-pointer transition-colors ${
                        selectedPortionId === portion.preset_id
                          ? 'bg-primary/10 border-2 border-primary'
                          : 'bg-gray-50 hover:bg-gray-100'
                      }`}
                      onClick={() => setSelectedPortionId(portion.preset_id)}
                    >
                      <div className="flex items-center gap-3">
                        <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                          selectedPortionId === portion.preset_id
                            ? 'border-primary bg-primary'
                            : 'border-gray-300'
                        }`}>
                          {selectedPortionId === portion.preset_id && (
                            <CheckCircle className="w-3 h-3 text-white" />
                          )}
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">{portion.display_name_vi}</p>
                          <p className="text-sm text-gray-500">{portion.size_label}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-medium">{portion.grams}g</p>
                        <p className="text-sm text-gray-500">
                          ~{Math.round(food.calories_per_100g * portion.grams / 100)} kcal
                        </p>
                      </div>
                    </div>
                  ))
                ) : (
                  food.servings?.map((serving) => (
                    <div
                      key={serving.serving_id}
                      className={`flex items-center justify-between p-4 rounded-xl cursor-pointer transition-colors ${
                        selectedServing === serving.serving_id
                          ? 'bg-primary/10 border-2 border-primary'
                          : 'bg-gray-50 hover:bg-gray-100'
                      }`}
                      onClick={() => setSelectedServing(serving.serving_id)}
                    >
                      <div className="flex items-center gap-3">
                        <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                          selectedServing === serving.serving_id
                            ? 'border-primary bg-primary'
                            : 'border-gray-300'
                        }`}>
                          {selectedServing === serving.serving_id && (
                            <CheckCircle className="w-3 h-3 text-white" />
                          )}
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">{serving.serving_unit}</p>
                          <p className="text-sm text-gray-500">{serving.description}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-medium">{serving.serving_size_g}g</p>
                        <p className="text-sm text-gray-500">
                          ~{Math.round(food.calories_per_100g * serving.serving_size_g / 100)} kcal
                        </p>
                      </div>
                    </div>
                  ))
                )}
              </div>

              {/* Quick Add */}
              <div className="mt-6 pt-6 border-t border-gray-100">
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <label className="text-sm text-gray-600">Số lượng:</label>
                    <input
                      type="number"
                      min="0.5"
                      step="0.5"
                      value={quantity}
                      onChange={(e) => setQuantity(parseFloat(e.target.value) || 1)}
                      className="w-20 px-3 py-2 border border-gray-200 rounded-lg text-center"
                    />
                  </div>
                  <Button
                    onClick={handleLogFood}
                    isLoading={logFoodMutation.isPending}
                    leftIcon={<Plus className="w-4 h-4" />}
                  >
                    Thêm vào nhật ký ăn
                  </Button>
                </div>
              </div>
            </CardBody>
          </Card>
        ) : null}

        {/* Additional Info */}
        {(food.description || food.notes) && (
          <Card>
            <CardHeader>
              <h2 className="font-semibold text-gray-900">Ghi chú</h2>
            </CardHeader>
            <CardBody>
              <p className="text-gray-600">{food.description || food.notes}</p>
            </CardBody>
          </Card>
        )}
      </div>
    </PageContainer>
  );
}

function NutritionItem({ icon, label, value, unit, color }: {
  icon: React.ReactNode;
  label: string;
  value: number;
  unit: string;
  color: string;
}) {
  const colorMap: Record<string, { bg: string; text: string }> = {
    orange: { bg: 'bg-orange-50', text: 'text-orange-600' },
    purple: { bg: 'bg-purple-50', text: 'text-purple-600' },
    yellow: { bg: 'bg-yellow-50', text: 'text-yellow-600' },
    blue: { bg: 'bg-blue-50', text: 'text-blue-600' },
  };

  return (
    <div className={`p-4 rounded-xl ${colorMap[color].bg}`}>
      <div className="flex items-center gap-2 mb-1">
        {icon}
        <span className="text-sm text-gray-500">{label}</span>
      </div>
      <p className={`text-2xl font-bold ${colorMap[color].text}`}>
        {value}
        <span className="text-sm font-normal text-gray-500 ml-1">{unit}</span>
      </p>
    </div>
  );
}