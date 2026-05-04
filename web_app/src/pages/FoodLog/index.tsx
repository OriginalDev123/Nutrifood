import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Search, Trash2, ChevronLeft, ChevronRight, UtensilsCrossed, History, Camera, AlertCircle, CheckCircle, TrendingUp, Calendar } from 'lucide-react';
import { Card, CardBody, Button, Modal, EmptyState, Skeleton, Badge, useToast, Tabs, TabList, TabPanel } from '../../components/ui';
import { PageContainer } from '../../components/layout';
import { foodApi } from '../../api/food';
import { analyticsApi } from '../../api/analytics';
import type { Food, FoodLog, FoodSearchResponse, DailySummary } from '../../api/types';
import type { FoodPortionPreset } from '../../api/food';
import type { CalorieNotification } from '../../api/extended';
import { ApplyPlanModal } from '../../components/meal-plan/ApplyPlanModal';
import { AIVisionTab } from './AIVisionTab';

type MealType = 'breakfast' | 'lunch' | 'dinner' | 'snack';

const MEAL_TYPES: Array<{ id: MealType; label: string; icon: string }> = [
  { id: 'breakfast', label: 'Sáng', icon: '🌅' },
  { id: 'lunch', label: 'Trưa', icon: '☀️' },
  { id: 'dinner', label: 'Tối', icon: '🌙' },
  { id: 'snack', label: 'Snack', icon: '🍪' },
];

export default function FoodLogPage() {
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [isHistoryMode, setIsHistoryMode] = useState(false);
  const [historyStartDate, setHistoryStartDate] = useState(() => {
    const date = new Date();
    date.setDate(date.getDate() - 6);
    return date.toISOString().split('T')[0];
  });
  const [historyEndDate, setHistoryEndDate] = useState(new Date().toISOString().split('T')[0]);
  const [historyMealType, setHistoryMealType] = useState('');
  const [isAddFoodModalOpen, setIsAddFoodModalOpen] = useState(false);
  const [selectedMealType, setSelectedMealType] = useState<MealType>('breakfast');
  const [isApplyPlanModalOpen, setIsApplyPlanModalOpen] = useState(false);
  const queryClient = useQueryClient();
  const toast = useToast();

  // Calorie notification state
  const [calorieNotification, setCalorieNotification] = useState<CalorieNotification | null>(null);

  // Fetch user's daily calorie target from goal
  const { data: goalProgress } = useQuery({
    queryKey: ['goalProgress'],
    queryFn: () => analyticsApi.getGoalProgress(),
    retry: false,
  });

  const userCalorieTarget = goalProgress?.daily_calorie_target || 2000;

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('vi-VN', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const goToPreviousDay = () => {
    const date = new Date(selectedDate);
    date.setDate(date.getDate() - 1);
    setSelectedDate(date.toISOString().split('T')[0]);
  };

  const goToNextDay = () => {
    const date = new Date(selectedDate);
    date.setDate(date.getDate() + 1);
    setSelectedDate(date.toISOString().split('T')[0]);
  };

  const { data: foodLogs = [], isLoading: logsLoading } = useQuery<FoodLog[]>({
    queryKey: ['foodLogs', selectedDate],
    queryFn: () => foodApi.getFoodLogs(selectedDate),
  });

  const { data: summary, isLoading: summaryLoading } = useQuery<DailySummary>({
    queryKey: ['dailySummary', selectedDate],
    queryFn: () => foodApi.getDailySummary(selectedDate),
  });

  // Calculate calorie notification when summary changes
  useEffect(() => {
    if (!summary || !userCalorieTarget) {
      setCalorieNotification(null);
      return;
    }

    const { total_calories } = summary;
    const percentage = (total_calories / userCalorieTarget) * 100;
    const remaining = userCalorieTarget - total_calories;

    if (percentage > 110) {
      setCalorieNotification({
        type: 'danger',
        message: `Bạn đã ăn quá ${Math.round(percentage - 100)}% calo mục tiêu!`,
        suggestion: 'Nên giảm bớt bữa ăn hoặc tăng vận động để cân bằng.'
      });
    } else if (percentage > 100) {
      setCalorieNotification({
        type: 'warning',
        message: `Calo hơi vượt mục tiêu một chút (+${Math.round(total_calories - userCalorieTarget)} kcal)`,
        suggestion: 'Cân nhắc giảm khẩu phần ở bữa tiếp theo.'
      });
    } else if (percentage < 50 && total_calories > 0) {
      setCalorieNotification({
        type: 'warning',
        message: `Bạn mới ăn được ${Math.round(percentage)}% calo mục tiêu.`,
        suggestion: `Cần thêm khoảng ${Math.round(remaining)} kcal nữa để đạt mục tiêu.`
      });
    } else if (percentage >= 50 && percentage < 80 && total_calories > 0) {
      setCalorieNotification({
        type: 'warning',
        message: `Cần thêm ${Math.round(remaining)} kcal nữa để đạt mục tiêu.`,
        suggestion: 'Bổ sung thêm bữa phụ hoặc tăng khẩu phần các bữa chính.'
      });
    } else if (percentage >= 80 && percentage <= 100) {
      setCalorieNotification({
        type: 'success',
        message: `Khá tốt! Đã đạt ${Math.round(percentage)}% mục tiêu.`,
        suggestion: `Còn ${Math.round(remaining)} kcal để hoàn thành mục tiêu hôm nay.`
      });
    } else {
      setCalorieNotification(null);
    }
  }, [summary, userCalorieTarget]);

  const { data: historyData, isLoading: historyLoading } = useQuery({
    queryKey: ['foodLogHistory', historyStartDate, historyEndDate, historyMealType],
    queryFn: () => foodApi.getFoodLogHistory(
      historyStartDate,
      historyEndDate,
      historyMealType ? (historyMealType as MealType) : undefined
    ),
    enabled: isHistoryMode,
  });

  const deleteMutation = useMutation({
    mutationFn: (logId: string) => foodApi.deleteFoodLog(logId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['foodLogs', selectedDate] });
      queryClient.invalidateQueries({ queryKey: ['dailySummary', selectedDate] });
      queryClient.invalidateQueries({ queryKey: ['foodLogHistory'] });
      toast.success('Đã xóa bữa ăn');
    },
    onError: () => {
      toast.error('Xóa thất bại');
    },
  });

  const logsByMealType = MEAL_TYPES.reduce((acc, meal) => {
    acc[meal.id] = foodLogs.filter((log) => log.meal_type === meal.id);
    return acc;
  }, {} as Record<MealType, FoodLog[]>);

  const getMealTotal = (logs: FoodLog[]) => ({
    calories: logs.reduce((sum, log) => sum + log.calories, 0),
    protein: logs.reduce((sum, log) => sum + log.protein_g, 0),
    carbs: logs.reduce((sum, log) => sum + log.carbs_g, 0),
    fat: logs.reduce((sum, log) => sum + log.fat_g, 0),
  });

  // Calculate calorie progress
  const getCalorieProgress = () => {
    if (!summary) return { percentage: 0, remaining: userCalorieTarget, color: 'bg-gray-200' };
    const percentage = Math.min((summary.total_calories / userCalorieTarget) * 100, 150);
    const remaining = userCalorieTarget - summary.total_calories;
    let color = 'bg-primary';
    if (percentage > 110) color = 'bg-red-500';
    else if (percentage > 100) color = 'bg-yellow-500';
    else if (percentage < 50) color = 'bg-orange-400';
    return { percentage, remaining, color };
  };

  const progress = getCalorieProgress();

  return (
    <PageContainer
      title="Nhật ký ăn"
      subtitle={formatDate(selectedDate)}
      action={
        <div className="flex items-center gap-2">
          <div className="flex items-center rounded-2xl border border-gray-200 bg-white shadow-sm">
            <button onClick={goToPreviousDay} className="rounded-l-2xl p-2.5 hover:bg-gray-50">
              <ChevronLeft className="h-5 w-5 text-gray-600" />
            </button>
            <span className="px-4 text-sm font-medium text-gray-700">
              {selectedDate === new Date().toISOString().split('T')[0] ? 'Hôm nay' : selectedDate}
            </span>
            <button onClick={goToNextDay} className="rounded-r-2xl p-2.5 hover:bg-gray-50">
              <ChevronRight className="h-5 w-5 text-gray-600" />
            </button>
          </div>
          <Button
            variant={isHistoryMode ? 'outline' : 'ghost'}
            onClick={() => setIsHistoryMode((prev) => !prev)}
            leftIcon={<History className="h-4 w-4" />}
          >
            {isHistoryMode ? 'Xem theo ngày' : 'Lịch sử'}
          </Button>
          <Button
            variant="outline"
            onClick={() => setIsApplyPlanModalOpen(true)}
            leftIcon={<Calendar className="h-4 w-4" />}
          >
            Áp dụng kế hoạch
          </Button>
          <Button onClick={() => setIsAddFoodModalOpen(true)} leftIcon={<Plus className="h-4 w-4" />}>
            Thêm món
          </Button>
        </div>
      }
    >
      <Card className="mb-6 border-gray-200/80 bg-white/95">
        <CardBody>
          {summaryLoading ? (
            <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
              {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-20 w-full rounded-2xl" />)}
            </div>
          ) : summary ? (
            <>
              {/* Calorie Progress Bar */}
              <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">Tiến trình Calories</span>
                  <span className="text-sm text-gray-500">
                    {summary.total_calories} / {userCalorieTarget} kcal
                  </span>
                </div>
                <div className="h-3 w-full overflow-hidden rounded-full bg-gray-200">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${progress.color}`}
                    style={{ width: `${Math.min(progress.percentage, 100)}%` }}
                  />
                </div>
              </div>

              {/* Calorie Notification */}
              {calorieNotification && (
                <div className={`mb-4 p-3 rounded-xl border ${
                  calorieNotification.type === 'danger'
                    ? 'bg-red-50 border-red-200'
                    : calorieNotification.type === 'warning'
                    ? 'bg-yellow-50 border-yellow-200'
                    : 'bg-green-50 border-green-200'
                }`}>
                  <div className="flex items-start gap-3">
                    {calorieNotification.type === 'danger' ? (
                      <AlertCircle className="h-5 w-5 text-red-500 shrink-0 mt-0.5" />
                    ) : calorieNotification.type === 'warning' ? (
                      <TrendingUp className="h-5 w-5 text-yellow-500 shrink-0 mt-0.5" />
                    ) : (
                      <CheckCircle className="h-5 w-5 text-green-500 shrink-0 mt-0.5" />
                    )}
                    <div className="flex-1">
                      <p className={`font-medium ${
                        calorieNotification.type === 'danger'
                          ? 'text-red-700'
                          : calorieNotification.type === 'warning'
                          ? 'text-yellow-700'
                          : 'text-green-700'
                      }`}>
                        {calorieNotification.message}
                      </p>
                      {calorieNotification.suggestion && (
                        <p className={`text-sm mt-1 ${
                          calorieNotification.type === 'danger'
                            ? 'text-red-600'
                            : calorieNotification.type === 'warning'
                            ? 'text-yellow-600'
                            : 'text-green-600'
                        }`}>
                          {calorieNotification.suggestion}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Summary Items */}
              <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
                <SummaryItem label="Calories" value={summary.total_calories} unit="kcal" color="green" />
                <SummaryItem label="Protein" value={Math.round(summary.total_protein_g)} unit="g" color="purple" />
                <SummaryItem label="Carbs" value={Math.round(summary.total_carbs_g)} unit="g" color="yellow" />
                <SummaryItem label="Fat" value={Math.round(summary.total_fat_g)} unit="g" color="orange" />
              </div>
            </>
          ) : null}
        </CardBody>
      </Card>

      {isHistoryMode ? (
        <Card>
          <CardBody className="space-y-4">
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">Từ ngày</label>
                <input
                  type="date"
                  value={historyStartDate}
                  onChange={(e) => setHistoryStartDate(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-4 py-2.5 focus:border-primary focus:ring-2 focus:ring-primary/20"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">Đến ngày</label>
                <input
                  type="date"
                  value={historyEndDate}
                  onChange={(e) => setHistoryEndDate(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-4 py-2.5 focus:border-primary focus:ring-2 focus:ring-primary/20"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">Loại bữa</label>
                <select
                  value={historyMealType}
                  onChange={(e) => setHistoryMealType(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-4 py-2.5 focus:border-primary focus:ring-2 focus:ring-primary/20"
                >
                  <option value="">Tất cả</option>
                  {MEAL_TYPES.map((meal) => (
                    <option key={meal.id} value={meal.id}>{meal.label}</option>
                  ))}
                </select>
              </div>
            </div>

            {historyLoading ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => <Skeleton key={i} className="h-24 w-full" />)}
              </div>
            ) : Object.entries(historyData?.logs_by_date ?? {}).length > 0 ? (
              <div className="space-y-4">
                {Object.entries(historyData?.logs_by_date ?? {}).map(([date, logs]) => (
                  <div key={date} className="overflow-hidden rounded-xl border border-gray-200">
                    <div className="flex items-center justify-between border-b border-gray-200 bg-gray-50 px-4 py-3">
                      <div>
                        <h3 className="font-semibold text-gray-900">{formatDate(date)}</h3>
                        <p className="text-sm text-gray-500">{Array.isArray(logs) ? logs.length : 0} món</p>
                      </div>
                      <Badge variant="info">{date}</Badge>
                    </div>
                    <div className="space-y-3 p-4">
                      {(Array.isArray(logs) ? logs : []).map((log) => (
                        <FoodLogItem
                          key={log.log_id}
                          log={log}
                          onDelete={() => deleteMutation.mutate(log.log_id)}
                        />
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState
                icon={<History className="h-8 w-8" />}
                title="Chưa có lịch sử trong khoảng này"
                description="Thử đổi khoảng ngày hoặc loại bữa để xem dữ liệu khác."
              />
            )}
          </CardBody>
        </Card>
      ) : (
        <div className="rounded-xl border border-gray-200 bg-white">
          <div className="flex border-b border-gray-200 px-4">
            {MEAL_TYPES.map((meal) => {
              const total = getMealTotal(logsByMealType[meal.id]);
              return (
                <button
                  key={meal.id}
                  onClick={() => setSelectedMealType(meal.id)}
                  className={`flex items-center gap-2 border-b-2 px-4 py-3 text-sm font-medium transition-colors ${
                    selectedMealType === meal.id
                      ? 'border-primary text-primary'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <span>{meal.icon}</span>
                  <span>{meal.label}</span>
                  <span className={`rounded-full px-2 py-0.5 text-xs ${selectedMealType === meal.id ? 'bg-primary/10 text-primary' : 'bg-gray-100 text-gray-500'}`}>
                    {total.calories} kcal
                  </span>
                </button>
              );
            })}
          </div>

          <div className="p-4">
            {logsLoading ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => <Skeleton key={i} className="h-20 w-full" />)}
              </div>
            ) : logsByMealType[selectedMealType].length > 0 ? (
              <div className="space-y-3">
                {logsByMealType[selectedMealType].map((log) => (
                  <FoodLogItem
                    key={log.log_id}
                    log={log}
                    onDelete={() => deleteMutation.mutate(log.log_id)}
                  />
                ))}
              </div>
            ) : (
              <EmptyState
                icon={<UtensilsCrossed className="h-8 w-8" />}
                title="Chưa có bữa ăn nào"
                description={`Thêm thực phẩm cho bữa ${MEAL_TYPES.find((meal) => meal.id === selectedMealType)?.label.toLowerCase() || 'đã chọn'}`}
                action={{
                  label: 'Thêm món',
                  onClick: () => setIsAddFoodModalOpen(true),
                }}
              />
            )}
          </div>
        </div>
      )}

      <AddFoodModal
        isOpen={isAddFoodModalOpen}
        onClose={() => setIsAddFoodModalOpen(false)}
        mealDate={selectedDate}
        mealType={selectedMealType}
      />

      <ApplyPlanModal
        isOpen={isApplyPlanModalOpen}
        onClose={() => setIsApplyPlanModalOpen(false)}
        onSuccess={(appliedCount) => {
          queryClient.invalidateQueries({ queryKey: ['foodLogs'] });
          queryClient.invalidateQueries({ queryKey: ['dailySummary'] });
          toast.success(`Đã thêm ${appliedCount} món ăn vào Nhật ký ăn`);
        }}
      />
    </PageContainer>
  );
}

interface SummaryItemProps {
  label: string;
  value: number;
  unit: string;
  color: string;
}

function SummaryItem({ label, value, unit, color }: SummaryItemProps) {
  const colorMap: Record<string, string> = {
    green: 'text-green-600',
    purple: 'text-purple-600',
    yellow: 'text-yellow-600',
    orange: 'text-orange-600',
  };

  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-4 text-center shadow-sm">
      <p className="text-sm text-gray-500">{label}</p>
      <p className={`text-xl font-bold ${colorMap[color]}`}>
        {Math.round(value)} <span className="text-sm font-normal">{unit}</span>
      </p>
    </div>
  );
}

interface FoodLogItemProps {
  log: FoodLog;
  onDelete: () => void;
}

function FoodLogItem({ log, onDelete }: FoodLogItemProps) {
  return (
    <div className="flex items-center justify-between rounded-2xl border border-gray-200 bg-white p-4 shadow-sm transition-colors hover:border-primary/20 hover:bg-gray-50">
      <div className="flex-1">
        <p className="font-medium text-gray-900">{log.food_name}</p>
        <p className="text-sm text-gray-500">
          {log.quantity} phần • {log.serving_size_g}g
        </p>
      </div>
      <div className="flex items-center gap-4">
        <div className="text-right">
          <p className="font-medium text-gray-900">{Math.round(log.calories)} kcal</p>
          <p className="text-xs text-gray-500">
            P: {Math.round(log.protein_g)}g • C: {Math.round(log.carbs_g)}g • F: {Math.round(log.fat_g)}g
          </p>
        </div>
        <button
          onClick={onDelete}
          className="rounded-lg p-2 text-gray-400 transition-colors hover:bg-red-50 hover:text-red-500"
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}

interface AddFoodModalProps {
  isOpen: boolean;
  onClose: () => void;
  mealDate: string;
  mealType: MealType;
}

function AddFoodModal({ isOpen, onClose, mealDate, mealType }: AddFoodModalProps) {
  const [activeTab, setActiveTab] = useState<'search' | 'vision'>('search');
  const [searchQuery, setSearchQuery] = useState('');
  const [barcodeQuery, setBarcodeQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [selectedFood, setSelectedFood] = useState<Food | null>(null);
  const [selectedPortionId, setSelectedPortionId] = useState('');
  const [quantity, setQuantity] = useState(1);
  const queryClient = useQueryClient();
  const toast = useToast();

  const resetManualState = () => {
    setSelectedFood(null);
    setSelectedPortionId('');
    setSearchQuery('');
    setBarcodeQuery('');
    setQuantity(1);
  };

  const handleLoggedSuccess = () => {
    queryClient.invalidateQueries({ queryKey: ['foodLogs', mealDate] });
    queryClient.invalidateQueries({ queryKey: ['dailySummary', mealDate] });
    toast.success('Đã thêm bữa ăn');
    resetManualState();
    onClose();
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(searchQuery);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  useEffect(() => {
    if (!isOpen) {
      setActiveTab('search');
      resetManualState();
    }
  }, [isOpen]);

  const { data: searchResults, isLoading: searchLoading } = useQuery<FoodSearchResponse>({
    queryKey: ['foodSearch', debouncedQuery],
    queryFn: () => foodApi.searchFoods(debouncedQuery),
    enabled: activeTab === 'search' && debouncedQuery.length >= 2,
  });

  const { data: barcodeFood, isLoading: barcodeLoading } = useQuery({
    queryKey: ['foodBarcodeLookup', barcodeQuery],
    queryFn: () => foodApi.getByBarcode(barcodeQuery.trim()),
    enabled: activeTab === 'search' && barcodeQuery.trim().length >= 6,
    retry: false,
  });

  const { data: portions = [] } = useQuery<FoodPortionPreset[]>({
    queryKey: ['foodPortions', selectedFood?.food_id],
    queryFn: () => foodApi.getPortions(selectedFood!.food_id),
    enabled: !!selectedFood?.food_id,
    retry: false,
  });

  const foods = searchResults?.foods ?? [];

  const logFoodMutation = useMutation({
    mutationFn: () => {
      const selectedPortion = portions.find((portion) => portion.preset_id === selectedPortionId);

      return foodApi.logMeal({
        food_id: selectedFood!.food_id,
        meal_type: mealType,
        meal_date: mealDate,
        quantity,
        serving_size_g: selectedPortion?.grams,
      });
    },
    onSuccess: handleLoggedSuccess,
    onError: () => {
      toast.error('Thêm bữa ăn thất bại');
    },
  });

  const handleSubmit = () => {
    if (!selectedFood) return;
    logFoodMutation.mutate();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Thêm thực phẩm" size="lg">
      <Tabs key={activeTab} defaultTab={activeTab} onChange={(tabId) => setActiveTab(tabId as 'search' | 'vision')}>
        <TabList
          tabs={[
            { id: 'search', label: 'Tìm kiếm', icon: <Search className="h-4 w-4" /> },
            { id: 'vision', label: 'AI Vision', icon: <Camera className="h-4 w-4" /> },
          ]}
          className="mb-4"
        />

        <TabPanel tabId="search">
          {!selectedFood ? (
            <div className="space-y-4">
              <div className="space-y-3 rounded-xl border border-blue-100 bg-blue-50 p-4">
                <label className="block text-sm font-medium text-blue-900">Tìm nhanh bằng barcode</label>
                <input
                  type="text"
                  placeholder="Nhập barcode sản phẩm..."
                  value={barcodeQuery}
                  onChange={(e) => setBarcodeQuery(e.target.value)}
                  className="w-full rounded-lg border border-blue-200 px-4 py-3 focus:border-primary focus:ring-2 focus:ring-primary/20"
                />
                {barcodeQuery.trim().length >= 6 ? (
                  barcodeLoading ? (
                    <p className="text-sm text-blue-700">Đang tìm theo barcode...</p>
                  ) : barcodeFood ? (
                    <button
                      onClick={() => setSelectedFood(barcodeFood)}
                      className="w-full rounded-lg border border-blue-100 bg-white p-3 text-left transition-colors hover:bg-blue-50"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <p className="font-medium text-gray-900">{barcodeFood.name_vi}</p>
                          <p className="text-sm text-gray-500">{barcodeFood.category}</p>
                        </div>
                        <Badge variant="info">{barcodeFood.barcode || 'Barcode'}</Badge>
                      </div>
                    </button>
                  ) : (
                    <p className="text-sm text-blue-700">Không tìm thấy thực phẩm theo barcode này.</p>
                  )
                ) : null}
              </div>

              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  placeholder="Tìm kiếm thực phẩm..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full rounded-lg border border-gray-200 py-3 pl-10 pr-4 focus:border-primary focus:ring-2 focus:ring-primary/20"
                  autoFocus
                />
              </div>

              <div className="max-h-96 space-y-2 overflow-y-auto">
                {searchLoading ? (
                  <div className="py-8 text-center">
                    <div className="mx-auto h-8 w-8 animate-spin rounded-full border-b-2 border-primary" />
                  </div>
                ) : foods.length > 0 ? (
                  foods.map((food) => (
                    <button
                      key={food.food_id}
                      onClick={() => setSelectedFood(food)}
                      className="w-full rounded-lg bg-gray-50 p-3 text-left transition-colors hover:bg-gray-100"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <p className="font-medium text-gray-900">{food.name_vi}</p>
                          <p className="text-sm text-gray-500">{food.category}</p>
                        </div>
                        <div className="text-right">
                          <p className="font-medium text-primary">{food.calories_per_100g} kcal</p>
                          <p className="text-xs text-gray-500">/100g</p>
                        </div>
                      </div>
                    </button>
                  ))
                ) : debouncedQuery.length >= 2 ? (
                  <p className="py-8 text-center text-gray-500">Không tìm thấy thực phẩm nào</p>
                ) : (
                  <p className="py-8 text-center text-gray-500">Nhập từ khóa để tìm kiếm</p>
                )}
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-start gap-4 rounded-xl bg-gray-50 p-4">
                <div className="flex-1">
                  <p className="font-medium text-gray-900">{selectedFood.name_vi}</p>
                  <p className="text-sm text-gray-500">{selectedFood.category}</p>
                </div>
                <button onClick={() => setSelectedFood(null)} className="text-sm text-primary hover:underline">
                  Đổi
                </button>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="rounded-xl bg-gray-50 p-3 text-center">
                  <p className="text-sm text-gray-500">Calories</p>
                  <p className="text-xl font-bold text-primary">
                    {Math.round(((portions.find((portion) => portion.preset_id === selectedPortionId)?.grams ?? 100) * selectedFood.calories_per_100g / 100) * quantity)}
                  </p>
                </div>
                <div className="rounded-xl bg-gray-50 p-3 text-center">
                  <p className="text-sm text-gray-500">Khẩu phần</p>
                  <input
                    type="number"
                    min="0.5"
                    step="0.5"
                    value={quantity}
                    onChange={(e) => setQuantity(parseFloat(e.target.value) || 1)}
                    className="w-20 rounded-lg border border-gray-200 py-1 text-center text-xl font-bold"
                  />
                </div>
              </div>

              {portions.length > 0 ? (
                <div>
                  <label className="mb-2 block text-sm font-medium text-gray-700">Chọn khẩu phần</label>
                  <div className="space-y-2">
                    {portions.map((portion) => (
                      <button
                        key={portion.preset_id}
                        onClick={() => setSelectedPortionId(portion.preset_id)}
                        className={`w-full rounded-lg border p-3 text-left transition-colors ${
                          selectedPortionId === portion.preset_id
                            ? 'border-primary bg-primary/10 text-primary'
                            : 'border-gray-200 bg-white hover:bg-gray-50'
                        }`}
                      >
                        <div className="flex items-center justify-between gap-3">
                          <div>
                            <p className="font-medium">{portion.display_name_vi}</p>
                            <p className="text-sm text-gray-500">{portion.size_label}</p>
                          </div>
                          <div className="text-sm font-medium">{portion.grams}g</div>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              ) : null}

              <div className="grid grid-cols-3 gap-2 text-center text-sm">
                <div>
                  <p className="text-gray-500">Protein</p>
                  <p className="font-medium">{selectedFood.protein_per_100g * quantity}g</p>
                </div>
                <div>
                  <p className="text-gray-500">Carbs</p>
                  <p className="font-medium">{selectedFood.carbs_per_100g * quantity}g</p>
                </div>
                <div>
                  <p className="text-gray-500">Fat</p>
                  <p className="font-medium">{selectedFood.fat_per_100g * quantity}g</p>
                </div>
              </div>

              <div className="flex gap-3 pt-4">
                <Button variant="outline" onClick={() => setSelectedFood(null)} className="flex-1">
                  Hủy
                </Button>
                <Button onClick={handleSubmit} isLoading={logFoodMutation.isPending} className="flex-1">
                  Thêm vào {MEAL_TYPES.find((m) => m.id === mealType)?.label}
                </Button>
              </div>
            </div>
          )}
        </TabPanel>

        <TabPanel tabId="vision">
          <AIVisionTab
            mealDate={mealDate}
            mealType={mealType}
            onSuccess={handleLoggedSuccess}
            onFallbackManual={() => setActiveTab('search')}
          />
        </TabPanel>
      </Tabs>
    </Modal>
  );
}
