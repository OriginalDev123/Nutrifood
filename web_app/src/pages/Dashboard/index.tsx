import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Flame,
  Beef,
  Wheat,
  Droplets,
  Plus,
  TrendingUp,
  TrendingDown,
  Calendar,
  ArrowRight,
  UtensilsCrossed,
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardBody, CardHeader, Progress, CircularProgress, Button, Skeleton, EmptyState, Badge } from '../../components/ui';
import { PageContainer } from '../../components/layout';
import { foodApi } from '../../api/food';
import { userApi } from '../../api/user';
import { analyticsApi } from '../../api/analytics';
import { recommendApi } from '../../api/recommend';
import { useAuthStore } from '../../stores/authStore';
import type { DailySummary, FoodLog, UserGoal } from '../../api/types';
import type { WeeklySummary } from '../../api/extended';

export default function DashboardPage() {
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const today = new Date().toISOString().split('T')[0];
  const [selectedDate] = useState(today);

  // Fetch daily summary
  const { data: summary, isLoading: summaryLoading } = useQuery<DailySummary>({
    queryKey: ['dailySummary', selectedDate],
    queryFn: () => foodApi.getDailySummary(selectedDate),
  });

  // Fetch active goal
  const { data: activeGoal } = useQuery<UserGoal>({
    queryKey: ['activeGoal'],
    queryFn: () => userApi.getActiveGoal(),
    retry: false,
  });

  // Fetch weekly summary
  const { data: weeklySummary, isLoading: weeklyLoading } = useQuery<WeeklySummary>({
    queryKey: ['weeklySummary'],
    queryFn: () => analyticsApi.getWeeklySummary(),
  });

  // Fetch today's food logs
  const { data: foodLogs, isLoading: logsLoading } = useQuery<FoodLog[]>({
    queryKey: ['foodLogs', today],
    queryFn: () => foodApi.getFoodLogs(today),
  });

  const { data: mealTiming } = useQuery({
    queryKey: ['mealTiming', today],
    queryFn: () => recommendApi.getMealTiming(today),
    retry: false,
  });

  const { data: nextMealSuggestions } = useQuery({
    queryKey: ['nextMealSuggestions', today, mealTiming?.suggested_meal_type],
    queryFn: () => recommendApi.getNextMealSuggestions(mealTiming!.suggested_meal_type, today),
    enabled: !!mealTiming?.suggested_meal_type,
    retry: false,
  });

  const calorieTarget = activeGoal?.daily_calorie_target || 2000;
  const proteinTarget = activeGoal?.protein_target_g || 80;
  const carbsTarget = activeGoal?.carbs_target_g || 250;
  const fatTarget = activeGoal?.fat_target_g || 65;

  const caloriePercentage = summary ? (summary.total_calories / calorieTarget) * 100 : 0;
  const proteinPercentage = summary ? (summary.total_protein_g / proteinTarget) * 100 : 0;
  const carbsPercentage = summary ? (summary.total_carbs_g / carbsTarget) * 100 : 0;
  const fatPercentage = summary ? (summary.total_fat_g / fatTarget) * 100 : 0;

  return (
    <PageContainer
      title={`Xin chào, ${user?.full_name?.split(' ').pop() || user?.email?.split('@')[0] || 'bạn'}!`}
      subtitle="Đây là tổng quan dinh dưỡng hôm nay"
    >
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content - Left Column */}
        <div className="lg:col-span-2 space-y-6">
          {/* Calorie Summary Card */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-primary/10 rounded-lg">
                  <Flame className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <h2 className="font-semibold text-gray-900">Lượng calories hôm nay</h2>
                  <p className="text-sm text-gray-500">{selectedDate}</p>
                </div>
              </div>
              <Link to="/food-log">
                <Button size="sm" leftIcon={<Plus className="w-4 h-4" />}>
                  Thêm món
                </Button>
              </Link>
            </CardHeader>
            <CardBody>
              {summaryLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Skeleton className="w-32 h-32 rounded-full" />
                </div>
              ) : summary ? (
                <div className="flex flex-col md:flex-row items-center gap-8">
                  <div>
                    <CircularProgress
                      value={summary.total_calories}
                      max={calorieTarget}
                      size={160}
                      strokeWidth={12}
                      variant={caloriePercentage > 100 ? 'warning' : 'primary'}
                      label="Calories"
                    />
                  </div>
                  <div className="flex-1 grid grid-cols-2 gap-4 w-full">
                    <MacroCard
                      icon={<Beef className="w-5 h-5 text-purple-500" />}
                      label="Protein"
                      value={summary.total_protein_g}
                      target={proteinTarget}
                      unit="g"
                      color="purple"
                      percentage={proteinPercentage}
                    />
                    <MacroCard
                      icon={<Wheat className="w-5 h-5 text-yellow-500" />}
                      label="Carbs"
                      value={summary.total_carbs_g}
                      target={carbsTarget}
                      unit="g"
                      color="yellow"
                      percentage={carbsPercentage}
                    />
                    <MacroCard
                      icon={<Droplets className="w-5 h-5 text-orange-500" />}
                      label="Fat"
                      value={summary.total_fat_g}
                      target={fatTarget}
                      unit="g"
                      color="orange"
                      percentage={fatPercentage}
                    />
                    <div className="p-4 bg-gray-50 rounded-xl">
                      <p className="text-sm text-gray-500">Bữa ăn</p>
                      <p className="text-2xl font-bold text-gray-900">{summary.meal_count}</p>
                      <p className="text-xs text-gray-400">bữa</p>
                    </div>
                  </div>
                </div>
              ) : (
                <EmptyState
                  title="Chưa có dữ liệu dinh dưỡng hôm nay"
                  description="Anh thêm bữa ăn đầu tiên để xem tổng calories và macro."
                  action={{
                    label: 'Thêm món',
                    onClick: () => navigate('/food-log'),
                  }}
                />
              )}
            </CardBody>
          </Card>

          {/* Weekly Trend */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-50 rounded-lg">
                    <TrendingUp className="w-5 h-5 text-blue-500" />
                  </div>
                  <h2 className="font-semibold text-gray-900">Xu hướng tuần này</h2>
                </div>
                <Link to="/analytics" className="text-sm text-primary hover:underline flex items-center gap-1">
                  Xem chi tiết <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            </CardHeader>
            <CardBody>
              {weeklyLoading ? (
                <div className="space-y-3">
                  {[1, 2, 3, 4, 5, 6, 7].map((i) => (
                    <Skeleton key={i} className="h-12 w-full" />
                  ))}
                </div>
              ) : weeklySummary && weeklySummary.daily_nutrition.length > 0 ? (
                <div className="space-y-3">
                  {weeklySummary.daily_nutrition.map((day, index) => (
                    <div key={index} className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg">
                      <div className="w-16 text-sm text-gray-600">
                        {new Date(day.date).toLocaleDateString('vi-VN', { weekday: 'short' })}
                      </div>
                      <div className="flex-1">
                        <Progress
                          value={day.total_calories}
                          max={calorieTarget}
                          showPercentage={false}
                          size="sm"
                          variant={day.total_calories > calorieTarget ? 'warning' : 'primary'}
                        />
                      </div>
                      <div className="w-20 text-right text-sm font-medium text-gray-900">
                        {Math.round(day.total_calories)} kcal
                      </div>
                    </div>
                  ))}
                  {weeklySummary.summary.weight_change_kg !== 0 && (
                    <div className={`flex items-center gap-2 p-3 rounded-lg ${weeklySummary.summary.weight_change_kg < 0 ? 'bg-green-50 text-green-700' : 'bg-orange-50 text-orange-700'}`}>
                      {weeklySummary.summary.weight_change_kg < 0 ? (
                        <TrendingDown className="w-5 h-5" />
                      ) : (
                        <TrendingUp className="w-5 h-5" />
                      )}
                      <span className="text-sm font-medium">
                        {weeklySummary.summary.weight_change_kg > 0 ? '+' : ''}
                        {weeklySummary.summary.weight_change_kg.toFixed(1)} kg trong tuần này
                      </span>
                    </div>
                  )}
                </div>
              ) : (
                <EmptyState
                  title="Chưa có xu hướng tuần"
                  description="Cần thêm dữ liệu bữa ăn để hiển thị xu hướng dinh dưỡng tuần này."
                />
              )}
            </CardBody>
          </Card>
        </div>

        {/* Sidebar - Right Column */}
        <div className="space-y-6">
          {/* Recent Food Logs */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-orange-50 rounded-lg">
                  <UtensilsCrossed className="w-5 h-5 text-orange-500" />
                </div>
                <h2 className="font-semibold text-gray-900">Bữa ăn gần đây</h2>
              </div>
              <Link to="/food-log" className="text-sm text-primary hover:underline">
                Xem tất cả
              </Link>
            </CardHeader>
            <CardBody className="p-0">
              {logsLoading ? (
                <div className="p-4 space-y-3">
                  {[1, 2, 3, 4].map((i) => (
                    <Skeleton key={i} className="h-16 w-full" />
                  ))}
                </div>
              ) : foodLogs && foodLogs.length > 0 ? (
                <div className="divide-y divide-gray-100">
                  {foodLogs.slice(0, 5).map((log) => (
                    <div key={log.log_id} className="flex items-center justify-between p-4 hover:bg-gray-50">
                      <div>
                        <p className="font-medium text-gray-900">{log.food_name}</p>
                        <p className="text-xs text-gray-500">
                          {log.meal_type === 'breakfast' ? 'Sáng' : log.meal_type === 'lunch' ? 'Trưa' : log.meal_type === 'dinner' ? 'Tối' : 'Snack'}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="font-medium text-gray-900">{Math.round(log.calories)} kcal</p>
                        <p className="text-xs text-gray-500">{log.quantity}x</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState
                  className="py-8"
                  title="Chưa có bữa ăn nào"
                  description="Anh thêm món ở Nhật ký ăn để hiện danh sách gần đây."
                  action={{
                    label: 'Thêm món',
                    onClick: () => navigate('/food-log'),
                  }}
                />
              )}
            </CardBody>
          </Card>

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <h2 className="font-semibold text-gray-900">Thao tác nhanh</h2>
            </CardHeader>
            <CardBody className="space-y-3">
              <Link to="/food-log" className="block">
                <Button variant="outline" className="w-full justify-start" leftIcon={<Plus className="w-4 h-4" />}>
                  Thêm bữa ăn
                </Button>
              </Link>
              <Link to="/foods" className="block">
                <Button variant="outline" className="w-full justify-start" leftIcon={<Calendar className="w-4 h-4" />}>
                  Tìm thực phẩm
                </Button>
              </Link>
              <Link to="/meal-plans/new" className="block">
                <Button variant="outline" className="w-full justify-start" leftIcon={<UtensilsCrossed className="w-4 h-4" />}>
                  Tạo kế hoạch ăn
                </Button>
              </Link>
            </CardBody>
          </Card>

          {mealTiming && nextMealSuggestions?.suggestions?.length ? (
            <Card>
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-emerald-50 rounded-lg">
                    <UtensilsCrossed className="w-5 h-5 text-emerald-500" />
                  </div>
                  <div>
                    <h2 className="font-semibold text-gray-900">Gợi ý bữa tiếp theo</h2>
                    <p className="text-sm text-gray-500">{mealTiming.reason}</p>
                  </div>
                </div>
              </CardHeader>
              <CardBody className="space-y-3">
                <div className="text-sm text-gray-600">
                  Nên ăn bữa <span className="font-medium text-gray-900">
                    {mealTiming.suggested_meal_type === 'breakfast' ? 'sáng' :
                     mealTiming.suggested_meal_type === 'lunch' ? 'trưa' :
                     mealTiming.suggested_meal_type === 'dinner' ? 'tối' : 'phụ'}
                  </span>
                </div>
                {nextMealSuggestions.suggestions.slice(0, 3).map((item) => (
                  <div key={item.food_id} className="p-3 bg-gray-50 rounded-xl">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="font-medium text-gray-900">{item.name_vi}</p>
                        <p className="text-xs text-gray-500 mt-1">{item.reason}</p>
                      </div>
                      <Badge variant="success">{Math.round(item.confidence * 100)}%</Badge>
                    </div>
                    <div className="mt-2 text-xs text-gray-500">
                      {item.serving_suggestion} • {Math.round(item.nutrition_per_100g.calories)} kcal / 100g
                    </div>
                  </div>
                ))}
              </CardBody>
            </Card>
          ) : null}

          {/* Goal Progress */}
          {activeGoal && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-green-50 rounded-lg">
                      <TrendingUp className="w-5 h-5 text-green-500" />
                    </div>
                    <h2 className="font-semibold text-gray-900">Mục tiêu</h2>
                  </div>
                  <Link to="/goals" className="text-sm text-primary hover:underline">
                    Chi tiết
                  </Link>
                </div>
              </CardHeader>
              <CardBody>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-600">
                        {activeGoal.goal_type === 'weight_loss' ? 'Giảm cân' :
                         activeGoal.goal_type === 'weight_gain' ? 'Tăng cân' :
                         activeGoal.goal_type === 'maintain' ? 'Duy trì cân nặng' : 'Sống khỏe'}
                      </span>
                      <span className="font-medium text-gray-900">{activeGoal.daily_calorie_target} kcal</span>
                    </div>
                    <Progress value={caloriePercentage} max={100} size="sm" />
                  </div>
                  {activeGoal.target_weight_kg && (
                    <p className="text-sm text-gray-500">
                      Mục tiêu: <span className="font-medium text-gray-900">{activeGoal.target_weight_kg} kg</span>
                    </p>
                  )}
                </div>
              </CardBody>
            </Card>
          )}
        </div>
      </div>
    </PageContainer>
  );
}

interface MacroCardProps {
  icon: React.ReactNode;
  label: string;
  value: number;
  target: number;
  unit: string;
  color: string;
  percentage: number;
}

function MacroCard({ icon, label, value, target, unit, color, percentage }: MacroCardProps) {
  const colorClasses: Record<string, string> = {
    purple: 'bg-purple-100 text-purple-700',
    yellow: 'bg-yellow-100 text-yellow-700',
    orange: 'bg-orange-100 text-orange-700',
  };

  return (
    <div className="p-3 bg-gray-50 rounded-xl">
      <div className="flex items-center gap-2 mb-1">
        <div className={`p-1.5 rounded-lg ${colorClasses[color]}`}>
          {icon}
        </div>
        <span className="text-sm text-gray-600">{label}</span>
      </div>
      <p className="text-lg font-bold text-gray-900">
        {Math.round(value)}<span className="text-sm font-normal text-gray-500">/{target}{unit}</span>
      </p>
      <Progress value={percentage} max={100} size="sm" showPercentage={false} variant={percentage > 100 ? 'warning' : 'primary'} />
    </div>
  );
}