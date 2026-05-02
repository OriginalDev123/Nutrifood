import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Calendar, TrendingUp, Beef, Wheat, Droplets, Plus, Sparkles, CheckCircle, AlertCircle, BarChart2, Target, UtensilsCrossed } from 'lucide-react';
import { Card, CardBody, Tabs, TabList, TabPanel, Skeleton, EmptyState, Button, useToast } from '../../components/ui';
import { PageContainer } from '../../components/layout';
import { analyticsApi } from '../../api/analytics';
import { CircularProgress } from '../../components/ui/CircularProgress';
import { LineChart, AreaChart } from '../../components/charts';
import type { WeightProgressItem, AIWeeklyInsightsResponse, NutritionAdviceResponse, QuickAdviceResponse, ProgressReportResponse } from '../../api/extended';
import { AIAdviceFullPage } from '../../components/ai';

const MEAL_TYPE_LABELS: Record<string, string> = {
  breakfast: 'Bữa sáng',
  lunch: 'Bữa trưa',
  dinner: 'Bữa tối',
  snack: 'Ăn vặt',
};

export default function AnalyticsPage() {
  const [selectedPeriod, setSelectedPeriod] = useState<'7' | '30' | '90'>('7');
  const [selectedAdvicePeriod, setSelectedAdvicePeriod] = useState<'day' | 'week' | 'month'>('week');
  const [showWeightInput, setShowWeightInput] = useState(false);
  const [currentWeight, setCurrentWeight] = useState('');
  const today = new Date().toISOString().split('T')[0];
  const periodNum = parseInt(selectedPeriod, 10);
  const queryClient = useQueryClient();
  const toast = useToast();

  const { data: nutritionTrends, isLoading: trendsLoading } = useQuery({
    queryKey: ['nutritionTrends', selectedPeriod],
    queryFn: () => {
      const endDate = new Date().toISOString().split('T')[0];
      const startDate = new Date(Date.now() - periodNum * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
      return analyticsApi.getNutritionTrends(startDate, endDate, 'day');
    },
  });

  const { data: macroDistribution, isLoading: macroLoading } = useQuery({
    queryKey: ['macroDistribution', today],
    queryFn: () => analyticsApi.getMacroDistribution(today),
  });

  const { data: weightProgress, isLoading: weightLoading } = useQuery({
    queryKey: ['weightProgress', selectedPeriod],
    queryFn: () => analyticsApi.getWeightProgress(periodNum),
  });

  const { data: mealPatterns, isLoading: mealsLoading } = useQuery({
    queryKey: ['mealPatterns', selectedPeriod],
    queryFn: () => analyticsApi.getMealPatterns(periodNum),
  });

  const { data: aiInsights, isLoading: aiLoading } = useQuery<AIWeeklyInsightsResponse>({
    queryKey: ['aiWeeklyInsights'],
    queryFn: () => analyticsApi.getAIWeeklyInsights(),
    retry: false,
  });

  // Nutrition Advice - AI-powered personalized advice
  const { data: nutritionAdvice, isLoading: adviceLoading } = useQuery<NutritionAdviceResponse>({
    queryKey: ['nutritionAdvice', selectedAdvicePeriod],
    queryFn: () => analyticsApi.getNutritionAdvice(7, selectedAdvicePeriod, 'vi'),
    retry: false,
    enabled: false, // Disable auto-fetch, only fetch on demand or when tab is active
  });

  // Quick Advice - Fast tip for next meal
  const { data: quickAdvice, isLoading: quickAdviceLoading } = useQuery<QuickAdviceResponse>({
    queryKey: ['quickAdvice'],
    queryFn: () => analyticsApi.getQuickAdvice(undefined, 'vi'),
    retry: false,
    enabled: false,
  });

  // Progress Report - Weekly/Monthly summary
  const { data: progressReport, isLoading: progressLoading } = useQuery<ProgressReportResponse>({
    queryKey: ['progressReport'],
    queryFn: () => analyticsApi.getProgressReport('week', 'vi'),
    retry: false,
    enabled: false,
  });

  const logWeightMutation = useMutation({
    mutationFn: (weight: number) => analyticsApi.logWeight(weight, today),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['weightProgress'] });
      toast.success('Đã cập nhật cân nặng hôm nay!');
      setShowWeightInput(false);
      setCurrentWeight('');
    },
    onError: () => {
      toast.error('Không thể cập nhật cân nặng');
    },
  });

  // Default daily target ~2000 kcal, can be extended to read from user profile
  const dailyTarget = 2000;
  const remainingCalorie = dailyTarget - (macroDistribution?.total_calories ?? 0);

  const getCalorieTrend = () => {
    if (!nutritionTrends?.trends || nutritionTrends.trends.length < 3) {
      return { label: 'Chưa đủ dữ liệu', color: 'text-gray-500', icon: '➡️' };
    }
    const data = nutritionTrends.trends.slice(-7);
    const first = data[0]?.total_calories || 0;
    const last = data[data.length - 1]?.total_calories || 0;
    const diff = last - first;
    if (diff > 100) return { label: `Tăng ${Math.round(diff)} kcal`, color: 'text-red-500', icon: '📈' };
    if (diff < -100) return { label: `Giảm ${Math.round(Math.abs(diff))} kcal`, color: 'text-green-500', icon: '📉' };
    return { label: 'Ổn định', color: 'text-gray-500', icon: '➡️' };
  };

  const calorieTrend = getCalorieTrend();

  const tabs = [
    { id: 'overview', label: 'Tổng quan' },
    { id: 'weight', label: 'Cân nặng' },
    { id: 'meals', label: 'Bữa ăn' },
    { id: 'advice', label: 'Lời khuyên AI' },
  ];

  // Fetch AI advice when advice tab is active
  const fetchAdvice = async () => {
    await queryClient.fetchQuery({
      queryKey: ['nutritionAdvice', selectedAdvicePeriod],
      queryFn: () => analyticsApi.getNutritionAdvice(7, selectedAdvicePeriod, 'vi'),
    });
    await queryClient.fetchQuery({
      queryKey: ['quickAdvice'],
      queryFn: () => analyticsApi.getQuickAdvice(undefined, 'vi'),
    });
    await queryClient.fetchQuery({
      queryKey: ['progressReport'],
      queryFn: () => analyticsApi.getProgressReport('week', 'vi'),
    });
  };

  const renderWeightInput = () => {
    if (!showWeightInput) {
      return (
        <Button variant="outline" onClick={() => setShowWeightInput(true)} className="mb-4">
          <Plus className="w-4 h-4 mr-2" />
          Nhập cân nặng hôm nay
        </Button>
      );
    }
    return (
      <div className="mb-4 p-4 bg-gray-50 rounded-xl border border-gray-200">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Cân nặng hôm nay ({new Date().toLocaleDateString('vi-VN')})
        </label>
        <div className="flex gap-2 items-center">
          <input
            type="number"
            step="0.1"
            min="30"
            max="300"
            value={currentWeight}
            onChange={(e) => setCurrentWeight(e.target.value)}
            placeholder="VD: 65.5"
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:border-primary focus:ring-2 focus:ring-primary/20"
          />
          <span className="text-gray-500">kg</span>
          <Button
            onClick={() => {
              const w = parseFloat(currentWeight);
              if (w >= 30 && w <= 300) {
                logWeightMutation.mutate(w);
              } else {
                toast.error('Cân nặng không hợp lệ');
              }
            }}
            isLoading={logWeightMutation.isPending}
          >
            Lưu
          </Button>
          <Button variant="ghost" onClick={() => setShowWeightInput(false)}>
            Hủy
          </Button>
        </div>
      </div>
    );
  };

  const renderAIInsights = () => {
    if (aiLoading) {
      return (
        <Card className="mb-6 bg-gradient-to-r from-primary/5 to-purple-50 border border-primary/20">
          <CardBody>
            <div className="flex items-center gap-2 mb-4">
              <Sparkles className="w-5 h-5 text-primary animate-pulse" />
              <span className="font-semibold text-gray-900">AI Insights</span>
            </div>
            <Skeleton className="h-24 w-full" />
          </CardBody>
        </Card>
      );
    }
    if (!aiInsights) return null;
    return (
      <Card className="mb-6 bg-gradient-to-r from-primary/5 to-purple-50 border border-primary/20">
        <CardBody>
          <div className="flex items-center gap-2 mb-4">
            <Sparkles className="w-5 h-5 text-primary" />
            <span className="font-semibold text-gray-900">AI Insights</span>
          </div>
          <p className="text-gray-700 mb-4">{aiInsights.summary}</p>
          {aiInsights.highlights && aiInsights.highlights.length > 0 && (
            <div className="mb-3">
              <p className="text-sm font-medium text-green-700 mb-2 flex items-center gap-1">
                <CheckCircle className="w-4 h-4" /> Điểm tích cực:
              </p>
              <ul className="space-y-1">
                {aiInsights.highlights.map((h: string, i: number) => (
                  <li key={i} className="text-sm text-green-600 flex items-start gap-2">
                    <span className="text-green-500">•</span>
                    {h}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {aiInsights.concerns && aiInsights.concerns.length > 0 && (
            <div className="mb-3">
              <p className="text-sm font-medium text-yellow-700 mb-2 flex items-center gap-1">
                <AlertCircle className="w-4 h-4" /> Cần cải thiện:
              </p>
              <ul className="space-y-1">
                {aiInsights.concerns.map((c: string, i: number) => (
                  <li key={i} className="text-sm text-yellow-600 flex items-start gap-2">
                    <span className="text-yellow-500">•</span>
                    {c}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {aiInsights.recommendations && aiInsights.recommendations.length > 0 && (
            <div className="p-3 bg-blue-50 rounded-lg">
              <p className="text-sm font-medium text-blue-700 mb-2 flex items-center gap-1">
                <BarChart2 className="w-4 h-4" /> Lời khuyên:
              </p>
              <ul className="space-y-1">
                {aiInsights.recommendations.map((r: string, i: number) => (
                  <li key={i} className="text-sm text-blue-600 flex items-start gap-2">
                    <span className="text-blue-500">→</span>
                    {r}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </CardBody>
      </Card>
    );
  };

  return (
    <PageContainer
      title="Phân tích dinh dưỡng"
      subtitle="Theo dõi tiến trình và xu hướng dinh dưỡng của bạn"
    >
      {renderWeightInput()}
      {renderAIInsights()}

      <div className="mb-6 flex gap-2">
        {['7', '30', '90'].map(period => (
          <button
            key={period}
            onClick={() => setSelectedPeriod(period as '7' | '30' | '90')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              selectedPeriod === period
                ? 'bg-primary text-white'
                : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'
            }`}
          >
            {period} ngày
          </button>
        ))}
      </div>

      <Tabs defaultTab="overview">
        <Card>
          <TabList tabs={tabs} className="px-4" />

          <TabPanel tabId="overview">
            <CardBody>
              {trendsLoading || macroLoading ? (
                <div className="space-y-6">
                  <Skeleton className="h-64 w-full" />
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-24 w-full" />)}
                  </div>
                  <Skeleton className="h-48 w-full" />
                </div>
              ) : nutritionTrends?.trends && nutritionTrends.trends.length > 0 ? (
                <div className="space-y-6">

                  {/* === CALORIE RING + TARGET CARD === */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* Calorie Ring - Today's Summary */}
                    <div className="md:col-span-2 p-5 bg-gradient-to-br from-emerald-50 to-teal-50 rounded-2xl border border-emerald-100">
                      <div className="flex flex-col sm:flex-row items-center gap-6">
                        {/* Ring */}
                        <div className="relative flex-shrink-0">
                          <CircularProgress
                            value={macroDistribution?.total_calories ?? 0}
                            max={dailyTarget}
                            size={140}
                            strokeWidth={12}
                            variant={
                              (macroDistribution?.total_calories ?? 0) > dailyTarget ? 'danger' :
                              (macroDistribution?.total_calories ?? 0) > dailyTarget * 0.9 ? 'warning' : 'primary'
                            }
                            showValue={false}
                          />
                          <div className="absolute inset-0 flex flex-col items-center justify-center">
                            <span className="text-2xl font-bold text-gray-900">
                              {Math.round(macroDistribution?.total_calories ?? 0)}
                            </span>
                            <span className="text-xs text-gray-500">kcal hôm nay</span>
                          </div>
                        </div>

                        {/* Stats */}
                        <div className="flex-1 w-full space-y-3">
                          <div className="flex items-center justify-between py-2 border-b border-emerald-100">
                            <span className="text-sm text-gray-500">Mục tiêu</span>
                            <span className="font-semibold text-gray-900">{dailyTarget} kcal</span>
                          </div>
                          <div className="flex items-center justify-between py-2 border-b border-emerald-100">
                            <span className="text-sm text-gray-500">Đã nạp</span>
                            <span className="font-semibold text-emerald-600">
                              {Math.round(macroDistribution?.total_calories ?? 0)} kcal
                            </span>
                          </div>
                          <div className="flex items-center justify-between py-2">
                            <span className="text-sm text-gray-500">Còn lại</span>
                            <span className={`font-bold text-base ${
                              remainingCalorie < 0 ? 'text-red-500' : 'text-emerald-600'
                            }`}>
                              {remainingCalorie < 0
                                ? `+${Math.abs(remainingCalorie)} kcal`
                                : `${remainingCalorie} kcal`
                              }
                            </span>
                          </div>

                          {/* Quick macros */}
                          {macroDistribution && (
                            <div className="flex gap-2 pt-1">
                              <div className="flex-1 bg-white/70 rounded-lg px-3 py-2 text-center">
                                <p className="text-xs text-purple-500 font-medium">Protein</p>
                                <p className="text-sm font-bold text-gray-900">{Math.round(macroDistribution.protein_grams)}g</p>
                              </div>
                              <div className="flex-1 bg-white/70 rounded-lg px-3 py-2 text-center">
                                <p className="text-xs text-yellow-500 font-medium">Carbs</p>
                                <p className="text-sm font-bold text-gray-900">{Math.round(macroDistribution.carbs_grams)}g</p>
                              </div>
                              <div className="flex-1 bg-white/70 rounded-lg px-3 py-2 text-center">
                                <p className="text-xs text-orange-500 font-medium">Fat</p>
                                <p className="text-sm font-bold text-gray-900">{Math.round(macroDistribution.fat_grams)}g</p>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Target + Trend Card */}
                    <div className="space-y-4">
                      <div className="p-5 bg-gray-50 rounded-2xl border border-gray-100">
                        <div className="flex items-center gap-2 mb-3">
                          <Target className="w-4 h-4 text-blue-500" />
                          <span className="text-sm font-medium text-gray-700">Mục tiêu hàng ngày</span>
                        </div>
                        <p className="text-3xl font-bold text-gray-900">{dailyTarget}</p>
                        <p className="text-sm text-gray-500">kcal / ngày</p>
                      </div>

                      <div className="p-5 bg-gray-50 rounded-2xl border border-gray-100">
                        <div className="flex items-center gap-2 mb-3">
                          <UtensilsCrossed className="w-4 h-4 text-orange-500" />
                          <span className="text-sm font-medium text-gray-700">Bữa ăn hôm nay</span>
                        </div>
                        <p className="text-3xl font-bold text-gray-900">
                          {nutritionTrends.trends.length > 0
                            ? nutritionTrends.trends[nutritionTrends.trends.length - 1].meal_count
                            : 0}
                        </p>
                        <p className="text-sm text-gray-500">bữa đã ghi nhận</p>
                      </div>

                      <div className="p-5 bg-gray-50 rounded-2xl border border-gray-100">
                        <div className="flex items-center gap-2 mb-3">
                          <Calendar className="w-4 h-4 text-blue-500" />
                          <span className="text-sm font-medium text-gray-700">Ngày theo dõi</span>
                        </div>
                        <p className="text-3xl font-bold text-gray-900">{nutritionTrends.trends.length}</p>
                        <p className="text-sm text-gray-500">ngày có dữ liệu</p>
                      </div>
                    </div>
                  </div>

                  {/* === CALORIE TREND CHART === */}
                  {(() => {
                    const slice = nutritionTrends.trends.slice(-14);
                    const chartData = slice.map(t => ({
                      label: new Date(t.date).toLocaleDateString('vi-VN', { day: 'numeric', month: 'short' }),
                      value: t.total_calories,
                    }));
                    const targetLine = slice.map(() => dailyTarget);

                    return (
                      <div className="p-5 bg-gray-50 rounded-2xl border border-gray-100">
                        <div className="flex items-center justify-between mb-4">
                          <div className="flex items-center gap-2">
                            <TrendingUp className="w-5 h-5 text-primary" />
                            <h3 className="font-semibold text-gray-900">Xu hướng Calories</h3>
                          </div>
                          <div className={`flex items-center gap-2 text-sm font-semibold px-3 py-1 rounded-full ${
                            calorieTrend.color === 'text-red-500' ? 'bg-red-50 text-red-600' :
                            calorieTrend.color === 'text-green-500' ? 'bg-green-50 text-green-600' :
                            'bg-gray-100 text-gray-600'
                          }`}>
                            <span>{calorieTrend.icon}</span>
                            <span>{calorieTrend.label}</span>
                          </div>
                        </div>
                        <div className="h-52">
                          <AreaChart
                            data={chartData}
                            secondaryData={targetLine.map((v, i) => ({ label: chartData[i]?.label ?? '', value: v }))}
                            secondaryColor="#3B82F6"
                            color="#22C55E"
                          />
                        </div>
                        <div className="flex items-center justify-center gap-6 mt-3 text-xs text-gray-600">
                          <span className="flex items-center gap-1.5">
                            <span className="w-3 h-1.5 rounded-sm bg-green-500" />
                            Calories thực tế
                          </span>
                          <span className="flex items-center gap-1.5">
                            <span className="w-3 h-1.5 rounded-sm bg-blue-400" style={{ opacity: 0.7 }} />
                            Mục tiêu ({dailyTarget} kcal)
                          </span>
                        </div>
                      </div>
                    );
                  })()}

                  {/* === MACRO BREAKDOWN CARDS === */}
                  {macroDistribution ? (
                    <div className="space-y-3">
                      <h3 className="font-semibold text-gray-900 px-1">Phân bổ Dinh dưỡng</h3>
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                        <MacroNutritionCard
                          icon={<Beef className="w-6 h-6 text-purple-500" />}
                          label="Protein"
                          grams={macroDistribution.protein_grams}
                          calories={macroDistribution.protein_calories}
                          percentage={macroDistribution.protein_percentage}
                          color="purple"
                        />
                        <MacroNutritionCard
                          icon={<Wheat className="w-6 h-6 text-yellow-500" />}
                          label="Carbs"
                          grams={macroDistribution.carbs_grams}
                          calories={macroDistribution.carbs_calories}
                          percentage={macroDistribution.carbs_percentage}
                          color="yellow"
                        />
                        <MacroNutritionCard
                          icon={<Droplets className="w-6 h-6 text-orange-500" />}
                          label="Fat"
                          grams={macroDistribution.fat_grams}
                          calories={macroDistribution.fat_calories}
                          percentage={macroDistribution.fat_percentage}
                          color="orange"
                        />
                      </div>
                    </div>
                  ) : null}

                  {/* === WEEKLY MACRO TREND CHART === */}
                  {(() => {
                    const slice21 = nutritionTrends.trends.slice(-21);
                    if (slice21.length === 0) return null;
                    const proteinData = slice21.map(t => ({ label: `${new Date(t.date).getDate()}`, value: t.protein }));
                    const carbsData = slice21.map(t => ({ label: `${new Date(t.date).getDate()}`, value: t.carbs }));
                    const fatData = slice21.map(t => ({ label: `${new Date(t.date).getDate()}`, value: t.fat }));

                    return (
                      <div className="p-5 bg-gray-50 rounded-2xl border border-gray-100">
                        <div className="flex items-center gap-2 mb-4">
                          <BarChart2 className="w-5 h-5 text-primary" />
                          <h3 className="font-semibold text-gray-900">Xu hướng Macro (21 ngày)</h3>
                        </div>
                        <div className="space-y-3">
                          <div>
                            <div className="flex justify-between text-xs mb-1">
                              <span className="flex items-center gap-1.5 text-purple-600 font-medium">
                                <span className="w-2 h-2 rounded-full bg-purple-500" /> Protein
                              </span>
                              <span className="text-gray-500">TB: {Math.round(proteinData.reduce((s, d) => s + d.value, 0) / proteinData.length)}g</span>
                            </div>
                            <div className="h-16">
                              <LineChart data={proteinData} color="#A855F7" showDot={false} fill />
                            </div>
                          </div>
                          <div>
                            <div className="flex justify-between text-xs mb-1">
                              <span className="flex items-center gap-1.5 text-yellow-600 font-medium">
                                <span className="w-2 h-2 rounded-full bg-yellow-500" /> Carbs
                              </span>
                              <span className="text-gray-500">TB: {Math.round(carbsData.reduce((s, d) => s + d.value, 0) / carbsData.length)}g</span>
                            </div>
                            <div className="h-16">
                              <LineChart data={carbsData} color="#EAB308" showDot={false} fill />
                            </div>
                          </div>
                          <div>
                            <div className="flex justify-between text-xs mb-1">
                              <span className="flex items-center gap-1.5 text-orange-600 font-medium">
                                <span className="w-2 h-2 rounded-full bg-orange-500" /> Fat
                              </span>
                              <span className="text-gray-500">TB: {Math.round(fatData.reduce((s, d) => s + d.value, 0) / fatData.length)}g</span>
                            </div>
                            <div className="h-16">
                              <LineChart data={fatData} color="#F97316" showDot={false} fill />
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center justify-center gap-6 mt-3 text-xs text-gray-600">
                          <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-purple-500" /> Protein</span>
                          <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-yellow-500" /> Carbs</span>
                          <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-orange-500" /> Fat</span>
                        </div>
                      </div>
                    );
                  })()}

                </div>
              ) : (
                <EmptyState title="Chưa có dữ liệu phân tích" description="Anh thêm bữa ăn trước, rồi quay lại đây để xem xu hướng." />
              )}
            </CardBody>
          </TabPanel>

          <TabPanel tabId="weight">
            <CardBody>
              {weightLoading ? (
                <Skeleton className="h-64 w-full" />
              ) : weightProgress?.history && weightProgress.history.length > 0 ? (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div className="p-4 bg-gray-50 rounded-xl text-center">
                      <p className="text-sm text-gray-500">Cân nặng ban đầu</p>
                      <p className="text-2xl font-bold text-gray-900">{weightProgress.starting_weight} kg</p>
                    </div>
                    <div className="p-4 bg-gray-50 rounded-xl text-center">
                      <p className="text-sm text-gray-500">Cân nặng hiện tại</p>
                      <p className="text-2xl font-bold text-primary">{weightProgress.current_weight} kg</p>
                    </div>
                    <div className="p-4 bg-gray-50 rounded-xl text-center">
                      <p className="text-sm text-gray-500">Thay đổi</p>
                      <p className={`text-2xl font-bold ${weightProgress.change_kg < 0 ? 'text-green-500' : 'text-red-500'}`}>
                        {weightProgress.change_kg > 0 ? '+' : ''}{weightProgress.change_kg} kg
                      </p>
                    </div>
                  </div>
                  {weightProgress.target_weight != null && (
                    <div className="p-4 bg-primary/5 border border-primary/20 rounded-xl text-center">
                      <p className="text-sm text-gray-600">Mục tiêu cân nặng</p>
                      <p className="text-xl font-semibold text-primary">{weightProgress.target_weight} kg</p>
                    </div>
                  )}
                  <div className={`text-center py-4 px-6 rounded-xl ${
                    weightProgress.trend === 'losing' ? 'bg-green-50 text-green-700' :
                    weightProgress.trend === 'gaining' ? 'bg-red-50 text-red-700' :
                    'bg-gray-50 text-gray-700'
                  }`}>
                    Xu hướng: {weightProgress.trend === 'losing' ? 'Giảm cân' : weightProgress.trend === 'gaining' ? 'Tăng cân' : weightProgress.trend === 'no_data' ? 'Chưa đủ dữ liệu' : 'Ổn định'}
                  </div>
                  <div className="p-4 bg-gray-50 rounded-xl">
                    <h3 className="font-semibold text-gray-900 mb-2">Biểu đồ cân nặng & mục tiêu</h3>
                    <p className="text-xs text-gray-500 mb-4">Đường màu primary: cân thực tế; đường nét đứt: mục tiêu (nếu có).</p>
                    <WeightSparkline history={weightProgress.history} targetKg={weightProgress.target_weight} />
                  </div>
                </div>
              ) : (
                <EmptyState title="Chưa có dữ liệu cân nặng" description="Anh log cân nặng để theo dõi tiến trình ở tab này." />
              )}
            </CardBody>
          </TabPanel>

          <TabPanel tabId="meals">
            <CardBody>
              {mealsLoading ? (
                <div className="space-y-4">
                  {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-16 w-full" />)}
                </div>
              ) : mealPatterns?.patterns && Object.keys(mealPatterns.patterns).length > 0 ? (
                <div className="space-y-4">
                  <p className="text-sm text-gray-600">
                    Trong {mealPatterns.days_analyzed} ngày: tổng <strong>{mealPatterns.total_meals}</strong> bữa đã ghi nhận.
                  </p>
                  {Object.entries(mealPatterns.patterns).map(([type, data]) => (
                    <div key={type} className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
                      <div>
                        <p className="font-medium text-gray-900">{MEAL_TYPE_LABELS[type] ?? type}</p>
                        <p className="text-sm text-gray-500">{data.count} bữa</p>
                      </div>
                      <div className="text-right">
                        <p className="font-medium text-primary">{Math.round(data.avg_calories)} kcal</p>
                        <p className="text-sm text-gray-500">TB/bữa</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState title="Chưa có thống kê bữa ăn" description="Chưa đủ dữ liệu để phân tích meal pattern." />
              )}
            </CardBody>
          </TabPanel>

          <TabPanel tabId="advice">
            <CardBody>
              <AIAdviceFullPage
                advice={nutritionAdvice || null}
                quickAdvice={quickAdvice || null}
                progressReport={progressReport || null}
                isLoadingAdvice={adviceLoading}
                isLoadingQuick={quickAdviceLoading}
                isLoadingProgress={progressLoading}
                selectedPeriod={selectedAdvicePeriod}
                onPeriodChange={setSelectedAdvicePeriod}
                onRefresh={fetchAdvice}
              />
            </CardBody>
          </TabPanel>
        </Card>
      </Tabs>
    </PageContainer>
  );
}

function WeightSparkline({ history, targetKg }: { history: WeightProgressItem[]; targetKg: number | null }) {
  if (!history || history.length === 0) return null;
  const weights = history.map(h => h.weight_kg);
  const minW = Math.min(...weights, ...(targetKg != null ? [targetKg] : [])) - 0.6;
  const maxW = Math.max(...weights, ...(targetKg != null ? [targetKg] : [])) + 0.6;
  const span = maxW - minW || 1;
  const w = Math.min(720, Math.max(280, history.length * 10));
  const h = 128;
  const pad = 10;
  const n = history.length;
  const xAt = (i: number) => pad + (n <= 1 ? (w - 2 * pad) / 2 : (i / (n - 1)) * (w - 2 * pad));
  const yAt = (kg: number) => pad + (1 - (kg - minW) / span) * (h - 2 * pad);
  const points = history.map((pt, i) => `${xAt(i)},${yAt(pt.weight_kg)}`).join(' ');
  const targetY = targetKg != null ? yAt(targetKg) : null;

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-36" role="img" aria-label="Biểu đồ cân nặng">
      {targetY != null && (
        <line x1={pad} y1={targetY} x2={w - pad} y2={targetY} stroke="#9ca3af" strokeWidth="1.5" strokeDasharray="5 5" />
      )}
      <polyline fill="none" stroke="#22C55E" strokeWidth="2.5" points={points} />
      {history.map((pt, i) => (
        <circle key={pt.date} cx={xAt(i)} cy={yAt(pt.weight_kg)} r="3.5" fill="#22C55E" />
      ))}
    </svg>
  );
}

function MacroNutritionCard({ icon, label, grams, calories, percentage, color }: {
  icon: React.ReactNode;
  label: string;
  grams: number;
  calories: number;
  percentage: number;
  color: string;
}) {
  const colorMap: Record<string, { bg: string; bar: string; text: string; label: string }> = {
    purple: { bg: 'bg-purple-50 border-purple-100', bar: 'bg-purple-500', text: 'text-purple-700', label: 'text-purple-600' },
    yellow: { bg: 'bg-yellow-50 border-yellow-100', bar: 'bg-yellow-500', text: 'text-yellow-700', label: 'text-yellow-600' },
    orange: { bg: 'bg-orange-50 border-orange-100', bar: 'bg-orange-500', text: 'text-orange-700', label: 'text-orange-600' },
  };
  const c = colorMap[color] ?? colorMap.purple;

  return (
    <div className={`p-5 rounded-2xl border ${c.bg} transition-shadow`}>
      <div className="flex items-center gap-3 mb-3">
        <div className={`p-2.5 rounded-xl ${c.bg}`}>
          {icon}
        </div>
        <div>
          <p className={`text-sm font-medium ${c.label}`}>{label}</p>
          <p className="text-2xl font-bold text-gray-900">{Math.round(grams)}g</p>
        </div>
      </div>
      {/* Progress bar */}
      <div className="w-full bg-white/60 rounded-full h-2 mb-2 overflow-hidden">
        <div
          className={`h-2 rounded-full transition-all duration-500 ${c.bar}`}
          style={{ width: `${Math.round(percentage)}%` }}
        />
      </div>
      <div className="flex justify-between">
        <span className={`text-xs font-medium ${c.text}`}>{Math.round(percentage)}%</span>
        <span className="text-xs text-gray-500">{Math.round(calories)} kcal</span>
      </div>
    </div>
  );
}
