import { useState } from 'react';
import type { ReactNode } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Target, Calendar, Check, Flame, Scale, Timer, Heart, AlertTriangle } from 'lucide-react';
import { Card, CardBody, CardHeader, Button, Badge, Modal, Input, EmptyState, useToast } from '../../components/ui';
import { DatePicker } from '../../components/ui/DatePicker';
import { PageContainer } from '../../components/layout';
import { goalApi } from '../../api/goal';
import type { HealthProfileData } from '../../api/healthProfile';
import { HealthProfileModal, HealthProfileDisplay } from '../../components/health';

export default function GoalsPage() {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const { data: goals, isLoading } = useQuery({
    queryKey: ['goals'],
    queryFn: () => goalApi.getAll(),
  });

  const activeGoal = goals?.find((g: any) => g.is_active);

  const getGoalTypeLabel = (type: string) => {
    switch (type) {
      case 'weight_loss': return 'Giảm cân';
      case 'weight_gain': return 'Tăng cân';
      case 'maintain': return 'Duy trì cân nặng';
      case 'healthy_lifestyle': return 'Sống khỏe mạnh';
      default: return type;
    }
  };

  const getGoalTypeColor = (type: string) => {
    switch (type) {
      case 'weight_loss': return 'success';
      case 'weight_gain': return 'warning';
      case 'maintain': return 'info';
      case 'healthy_lifestyle': return 'success';
      default: return 'default';
    }
  };

  return (
    <PageContainer
      title="Mục tiêu dinh dưỡng"
      subtitle="Thiết lập và theo dõi mục tiêu của bạn"
      action={
        <Button onClick={() => setIsModalOpen(true)} leftIcon={<Plus className="w-4 h-4" />}>
          Tạo mục tiêu mới
        </Button>
      }
    >
      {/* Active Goal */}
      {activeGoal && (
        <Card className="mb-6 overflow-hidden">
          <div className="h-20 bg-gradient-to-r from-primary/10 via-emerald-100/80 to-white" />
          <CardHeader className="-mt-8 border-b-0 pb-2">
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div className="flex items-center gap-3">
                <div className="p-3 bg-white rounded-2xl shadow-sm border border-primary/10">
                  <Target className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <h2 className="font-semibold text-gray-900">Mục tiêu hiện tại</h2>
                  <p className="text-sm text-gray-500">Theo dõi chỉ số chính và tiến độ mỗi ngày</p>
                </div>
              </div>
              <Badge variant={getGoalTypeColor(activeGoal.goal_type) as any} className="w-fit">
                {getGoalTypeLabel(activeGoal.goal_type)}
              </Badge>
            </div>
          </CardHeader>
          <CardBody>
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
              <GoalStat label="Cân nặng hiện tại" value={`${activeGoal.current_weight_kg} kg`} icon={<Scale className="w-4 h-4" />} />
              <GoalStat label="Cân nặng mục tiêu" value={`${activeGoal.target_weight_kg || '-'} kg`} icon={<Target className="w-4 h-4" />} />
              <GoalStat label="Calories/ngày" value={`${activeGoal.daily_calorie_target || '-'} kcal`} icon={<Flame className="w-4 h-4" />} />
              <GoalStat label="Hạn chót" value={activeGoal.target_date ? new Date(activeGoal.target_date).toLocaleDateString('vi-VN') : 'Không có'} icon={<Timer className="w-4 h-4" />} />
            </div>

            {/* Health Profile Summary in Active Goal */}
            {(() => {
              const hasConditions = (activeGoal as any).health_conditions?.length > 0;
              const hasAllergies = (activeGoal as any).food_allergies?.length > 0;
              const hasPreferences = (activeGoal as any).dietary_preferences?.length > 0;
              return hasConditions || hasAllergies || hasPreferences ? (
                <div className="mt-6 pt-6 border-t border-gray-100">
                  <h3 className="text-sm font-medium text-gray-700 mb-4">Thể trạng</h3>
                  <div className="flex flex-wrap gap-2">
                    {hasAllergies ? (
                      <Badge variant="danger">
                        <AlertTriangle className="w-3 h-3 mr-1" />
                        {(activeGoal as any).food_allergies.length} dị ứng
                      </Badge>
                    ) : null}
                    {hasConditions ? (
                      <Badge variant="info">
                        <Heart className="w-3 h-3 mr-1" />
                        {(activeGoal as any).health_conditions.length} điều kiện
                      </Badge>
                    ) : null}
                    {hasPreferences ? (
                      <Badge variant="success">
                        {(activeGoal as any).dietary_preferences.length} chế độ ăn
                      </Badge>
                    ) : null}
                  </div>
                </div>
              ) : null;
            })()}

            {activeGoal.protein_target_g && activeGoal.carbs_target_g && activeGoal.fat_target_g && (
              <div className="mt-6 pt-6 border-t border-gray-100">
                <h3 className="text-sm font-medium text-gray-700 mb-4">Macro mục tiêu</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <MacroTarget label="Protein" value={activeGoal.protein_target_g} color="purple" />
                  <MacroTarget label="Carbs" value={activeGoal.carbs_target_g} color="yellow" />
                  <MacroTarget label="Fat" value={activeGoal.fat_target_g} color="orange" />
                </div>
              </div>
            )}
          </CardBody>
        </Card>
      )}

      {/* Goals History */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-50 rounded-lg">
              <Calendar className="w-5 h-5 text-blue-500" />
            </div>
            <h2 className="font-semibold text-gray-900">Lịch sử mục tiêu</h2>
          </div>
        </CardHeader>
        <CardBody>
          {isLoading ? (
            <div className="space-y-3 animate-pulse">
              {Array.from({ length: 3 }).map((_, index) => (
                <div key={index} className="h-24 rounded-2xl border border-gray-200 bg-gray-50" />
              ))}
            </div>
          ) : goals && goals.length > 0 ? (
            <div className="space-y-3">
              {goals.map((goal: any) => (
                <div key={goal.goal_id} className="flex flex-col gap-4 rounded-2xl border border-gray-200 bg-gradient-to-r from-white to-gray-50/80 p-4 shadow-sm md:flex-row md:items-center md:justify-between">
                  <div className="flex items-center gap-4">
                    {goal.is_active ? (
                      <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-green-100 text-green-600">
                        <Check className="w-5 h-5" />
                      </div>
                    ) : (
                      <div className="flex h-10 w-10 items-center justify-center rounded-2xl border border-gray-200 bg-white text-gray-300">
                        <Target className="w-5 h-5" />
                      </div>
                    )}
                    <div className="space-y-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="font-medium text-gray-900">{getGoalTypeLabel(goal.goal_type)}</p>
                        {goal.is_active && <Badge variant="success">Mục tiêu hiện tại</Badge>}
                      </div>
                      <p className="text-sm text-gray-500">
                        {goal.current_weight_kg} kg → {goal.target_weight_kg || '?'} kg
                      </p>
                      <p className="text-xs text-gray-400">
                        {goal.target_date ? `Đích đến: ${new Date(goal.target_date).toLocaleDateString('vi-VN')}` : 'Chưa đặt hạn chót'}
                      </p>
                    </div>
                  </div>
                  <div className="flex flex-wrap items-center gap-2 md:justify-end">
                    {goal.daily_calorie_target && (
                      <div className="rounded-xl bg-orange-50 px-3 py-2 text-sm font-medium text-orange-700">
                        {goal.daily_calorie_target} kcal/ngày
                      </div>
                    )}
                    <Badge variant={goal.is_active ? 'success' : 'default'}>
                      {goal.is_active ? 'Đang hoạt động' : 'Đã kết thúc'}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState title="Chưa có mục tiêu nào" description="Tạo mục tiêu mới để theo dõi dinh dưỡng và cân nặng dễ hơn." />
          )}
        </CardBody>
      </Card>

      {/* Create Goal Modal */}
      <CreateGoalModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
    </PageContainer>
  );
}

function GoalStat({ label, value, icon }: { label: string; value: string; icon: ReactNode }) {
  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <span className="text-sm text-gray-500">{label}</span>
        <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-primary/10 text-primary">{icon}</span>
      </div>
      <p className="text-lg font-bold text-gray-900">{value}</p>
    </div>
  );
}

function MacroTarget({ label, value, color }: { label: string; value: number; color: string }) {
  const colorMap: Record<string, string> = {
    purple: 'bg-purple-100 text-purple-700',
    yellow: 'bg-yellow-100 text-yellow-700',
    orange: 'bg-orange-100 text-orange-700',
  };

  return (
    <div className={`p-4 rounded-2xl border border-white/60 shadow-sm ${colorMap[color]}`}>
      <p className="text-sm font-medium">{label}</p>
      <p className="text-2xl font-bold mt-1">{value}g</p>
    </div>
  );
}

function CreateGoalModal({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const toast = useToast();
  const queryClient = useQueryClient();

  const [goalType, setGoalType] = useState('weight_loss');
  const [currentWeight, setCurrentWeight] = useState('');
  const [targetWeight, setTargetWeight] = useState('');
  const [targetDate, setTargetDate] = useState('');
  const [calorieTarget, setCalorieTarget] = useState('');

  // Health profile state
  const [healthProfile, setHealthProfile] = useState<HealthProfileData>({
    health_conditions: [],
    food_allergies: [],
    dietary_preferences: [],
  });
  const [isHealthProfileModalOpen, setIsHealthProfileModalOpen] = useState(false);
  const [showHealthSection, setShowHealthSection] = useState(false);

  const hasHealthProfileData =
    healthProfile.health_conditions.length > 0 ||
    healthProfile.food_allergies.length > 0 ||
    healthProfile.dietary_preferences.length > 0;

  const handleCreate = () => {
    const cw = parseFloat(currentWeight);
    if (!currentWeight || isNaN(cw) || cw <= 0 || cw > 300) {
      toast.error('Cân nặng hiện tại phải từ 0.1 đến 300 kg');
      return;
    }
    if (targetWeight) {
      const tw = parseFloat(targetWeight);
      if (isNaN(tw) || tw <= 0 || tw > 300) {
        toast.error('Cân nặng mục tiêu phải từ 0.1 đến 300 kg');
        return;
      }
    }
    if (calorieTarget) {
      const cal = parseInt(calorieTarget);
      if (isNaN(cal) || cal < 1200) {
        toast.error('Calories mục tiêu phải từ 1200 kcal trở lên');
        return;
      }
    }
    // Validation cho ngày đích khi giảm/tăng cân
    if ((goalType === 'weight_loss' || goalType === 'weight_gain') && !targetDate) {
      toast.error('Vui lòng chọn ngày đích để đạt mục tiêu');
      return;
    }
    if (targetDate) {
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      const selectedDate = new Date(targetDate);
      if (selectedDate <= today) {
        toast.error('Ngày đích phải lớn hơn ngày hiện tại');
        return;
      }
    }
    createMutation.mutate();
  };

  const createMutation = useMutation({
    mutationFn: () => goalApi.create({
      goal_type: goalType as any,
      current_weight_kg: parseFloat(currentWeight),
      target_weight_kg: targetWeight ? parseFloat(targetWeight) : undefined,
      target_date: targetDate || undefined,
      daily_calorie_target: calorieTarget ? parseInt(calorieTarget) : undefined,
      health_conditions: hasHealthProfileData ? healthProfile.health_conditions : undefined,
      food_allergies: hasHealthProfileData ? healthProfile.food_allergies : undefined,
      dietary_preferences: hasHealthProfileData ? healthProfile.dietary_preferences : undefined,
    }),
    onSuccess: () => {
      toast.success('Đã tạo mục tiêu mới');
      queryClient.invalidateQueries({ queryKey: ['goals'] });
      setCurrentWeight('');
      setTargetWeight('');
      setTargetDate('');
      setCalorieTarget('');
      setGoalType('weight_loss');
      setHealthProfile({
        health_conditions: [],
        food_allergies: [],
        dietary_preferences: [],
      });
      setShowHealthSection(false);
      onClose();
    },
    onError: (error: any) => {
      const detail = error?.response?.data?.detail;
      if (typeof detail === 'string' && detail.includes('đã có một mục tiêu')) {
        toast.error('Bạn đã có một mục tiêu đang hoạt động. Vui lòng kết thúc mục tiêu hiện tại trước khi tạo mới.');
      } else if (typeof detail === 'string') {
        toast.error(detail);
      } else {
        toast.error('Tạo mục tiêu thất bại');
      }
    },
  });

  const handleSaveHealthProfile = (data: HealthProfileData) => {
    setHealthProfile(data);
    setIsHealthProfileModalOpen(false);
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Tạo mục tiêu mới">
      <div className="space-y-5">
        <div className="rounded-2xl border border-gray-200 bg-gray-50/80 p-4">
          <label className="block text-sm font-medium text-gray-700 mb-3">Loại mục tiêu</label>
          <div className="grid grid-cols-2 gap-2">
            {[
              { value: 'weight_loss', label: 'Giảm cân' },
              { value: 'weight_gain', label: 'Tăng cân' },
              { value: 'maintain', label: 'Duy trì' },
              { value: 'healthy_lifestyle', label: 'Sống khỏe' },
            ].map(opt => (
              <button
                key={opt.value}
                onClick={() => setGoalType(opt.value)}
                className={`rounded-xl border p-3 text-sm font-medium transition-colors ${
                  goalType === opt.value
                    ? 'border-primary bg-primary/10 text-primary shadow-sm'
                    : 'border-gray-200 bg-white text-gray-600 hover:bg-gray-50'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        <Input
          label="Cân nặng hiện tại (kg)"
          type="number"
          step="0.1"
          value={currentWeight}
          onChange={(e) => setCurrentWeight(e.target.value)}
          placeholder="65"
        />

        <Input
          label="Cân nặng mục tiêu (kg)"
          type="number"
          step="0.1"
          value={targetWeight}
          onChange={(e) => setTargetWeight(e.target.value)}
          placeholder="60"
        />

        {(goalType === 'weight_loss' || goalType === 'weight_gain') && (
          <DatePicker
            label="Ngày đích (muốn đạt được vào ngày)"
            value={targetDate}
            onChange={(e) => setTargetDate(e.target.value)}
            min={new Date().toISOString().split('T')[0]}
            placeholder="Chọn ngày"
          />
        )}

        <Input
          label="Calories mục tiêu/ngày"
          type="number"
          value={calorieTarget}
          onChange={(e) => setCalorieTarget(e.target.value)}
          placeholder="2000"
        />

        {/* Health Profile Section */}
        <div className="rounded-2xl border border-gray-200 bg-gray-50/80 p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Heart className="w-5 h-5 text-gray-500" />
              <span className="font-medium text-gray-700">Thể trạng (tùy chọn)</span>
            </div>
            <button
              onClick={() => setShowHealthSection(!showHealthSection)}
              className="text-sm text-primary hover:text-primary/80"
            >
              {showHealthSection ? 'Ẩn bớt' : 'Thêm thể trạng'}
            </button>
          </div>

          {showHealthSection && (
            <div className="space-y-3">
              {hasHealthProfileData && (
                <div className="bg-white rounded-lg p-3 border border-gray-100">
                  <HealthProfileDisplay data={healthProfile} compact />
                </div>
              )}

              <Button
                variant="outline"
                onClick={() => setIsHealthProfileModalOpen(true)}
                className="w-full"
                size="sm"
              >
                {hasHealthProfileData ? 'Cập nhật thể trạng' : 'Nhập thể trạng'}
              </Button>

              {hasHealthProfileData && (
                <p className="text-xs text-gray-500 text-center">
                  Thể trạng sẽ được lưu cùng với mục tiêu này
                </p>
              )}
            </div>
          )}
        </div>

        <div className="flex gap-3 pt-2">
          <Button variant="outline" onClick={onClose} className="flex-1">Hủy</Button>
          <Button onClick={handleCreate} isLoading={createMutation.isPending} className="flex-1">
            Tạo mục tiêu
          </Button>
        </div>
      </div>

      {/* Health Profile Modal */}
      <HealthProfileModal
        isOpen={isHealthProfileModalOpen}
        onClose={() => setIsHealthProfileModalOpen(false)}
        onSave={handleSaveHealthProfile}
        initialData={healthProfile}
        isLoading={false}
      />
    </Modal>
  );
}
