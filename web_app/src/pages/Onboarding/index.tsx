import { useEffect, useMemo, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Leaf,
  Calendar,
  Check,
  TrendingDown,
  TrendingUp,
  ArrowUp,
  Heart,
  Mars,
  Venus,
  CircleUserRound,
} from 'lucide-react';
import { Button, Input, Card, CardBody, useToast } from '../../components/ui';
import { userApi } from '../../api/user';
import { goalApi, type CreateGoalData } from '../../api/goal';
import type { UserGoal } from '../../api/types';
import {
  isOnboardingPending,
  markOnboardingComplete,
} from '../../lib/onboardingStorage';

type GoalType = 'weight_loss' | 'weight_gain' | 'maintain' | 'healthy_lifestyle';

const GOAL_LABELS: Record<GoalType, string> = {
  weight_loss: 'Giảm cân',
  weight_gain: 'Tăng cân',
  maintain: 'Duy trì',
  healthy_lifestyle: 'Sống khỏe',
};

const MAX_KG_PER_WEEK = 1.5;

function todayLocalISO(): string {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

function addDaysLocalISO(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() + days);
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

function getAxiosDetail(err: unknown): string {
  const e = err as { response?: { data?: { detail?: unknown } } };
  const detail = e.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return (
      detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join('; ') ||
      'Đã xảy ra lỗi.'
    );
  }
  return 'Đã xảy ra lỗi. Vui lòng thử lại.';
}

function estimateKgPerWeek(
  goalType: GoalType,
  current: number,
  target: number,
  weeks: number
): number | null {
  if (weeks < 1) return null;
  if (goalType !== 'weight_loss' && goalType !== 'weight_gain') return null;
  return Math.abs(target - current) / weeks;
}

function buildGoalPayload(
  currentWeight: number,
  targetWeight: number,
  weeks: number,
  goalType: GoalType
): CreateGoalData {
  const w = Math.max(1, weeks);
  const targetDate = addDaysLocalISO(w * 7);

  return {
    goal_type: goalType,
    current_weight_kg: currentWeight,
    target_weight_kg: targetWeight,
    target_date: targetDate,
  };
}

export default function OnboardingPage() {
  const navigate = useNavigate();
  const toast = useToast();

  // Dùng ref để theo dõi step — tránh guard effect chạy sau khi user đã bắt đầu
  const hasStartedRef = useRef(false);

  const [step, setStep] = useState<1 | 2 | 3 | 4>(1);

  const [fullName, setFullName] = useState('');
  const [dateOfBirth, setDateOfBirth] = useState('');
  const [gender, setGender] = useState<'male' | 'female' | 'other' | ''>('');
  const [heightCm, setHeightCm] = useState(170);
  const [currentWeightKg, setCurrentWeightKg] = useState(65);

  const [goalType, setGoalType] = useState<GoalType>('weight_loss');
  const [targetWeightKg, setTargetWeightKg] = useState(65);
  const [weeks, setWeeks] = useState(12);

  const [createdGoal, setCreatedGoal] = useState<UserGoal | null>(null);
  const [goalError, setGoalError] = useState<string | null>(null);
  const [hintKgPerWeek, setHintKgPerWeek] = useState<string | null>(null);

  const [savingProfile, setSavingProfile] = useState(false);
  const [savingGoal, setSavingGoal] = useState(false);
  const [step2Error, setStep2Error] = useState<string | null>(null);

  // Guard: chỉ redirect nếu chưa bắt đầu onboarding (step=1) và không còn pending
  useEffect(() => {
    if (hasStartedRef.current) return;
    if (!isOnboardingPending()) {
      navigate('/dashboard', { replace: true });
    }
  }, [navigate]);

  const kgPerWeekPreview = useMemo(
    () => estimateKgPerWeek(goalType, currentWeightKg, targetWeightKg, weeks),
    [goalType, currentWeightKg, targetWeightKg, weeks]
  );

  useEffect(() => {
    if (step !== 3 || kgPerWeekPreview === null) {
      setHintKgPerWeek(null);
      return;
    }
    if (kgPerWeekPreview > MAX_KG_PER_WEEK) {
      setHintKgPerWeek(
        `Tốc độ ước tính ~${kgPerWeekPreview.toFixed(2)} kg/tuần — không nên vượt quá ${MAX_KG_PER_WEEK} kg/tuần. Hãy điều chỉnh cân đích hoặc thời gian.`
      );
    } else {
      setHintKgPerWeek(null);
    }
  }, [step, kgPerWeekPreview]);

  const macroBar = useMemo(() => {
    const g = createdGoal;
    if (!g?.protein_target_g || !g?.carbs_target_g || !g?.fat_target_g) {
      return null;
    }
    const p = g.protein_target_g * 4;
    const c = g.carbs_target_g * 4;
    const f = g.fat_target_g * 9;
    const t = p + c + f;
    if (t <= 0) return null;
    return {
      p: (p / t) * 100,
      c: (c / t) * 100,
      f: (f / t) * 100,
    };
  }, [createdGoal]);

  const validateStep2 = (): boolean => {
    setStep2Error(null);
    if (!fullName.trim() || fullName.trim().length < 2) {
      setStep2Error('Vui lòng nhập họ và tên (ít nhất 2 ký tự).');
      return false;
    }
    if (!dateOfBirth) {
      setStep2Error('Vui lòng chọn ngày sinh.');
      return false;
    }
    if (!gender) {
      setStep2Error('Vui lòng chọn giới tính.');
      return false;
    }
    if (heightCm < 50 || heightCm > 250) {
      setStep2Error('Chiều cao phải trong khoảng 50–250 cm.');
      return false;
    }
    if (currentWeightKg < 20 || currentWeightKg > 300) {
      setStep2Error('Cân nặng hiện tại không hợp lệ.');
      return false;
    }
    return true;
  };

  const handleStep2Continue = async () => {
    if (!validateStep2()) return;
    setSavingProfile(true);
    setStep2Error(null);
    try {
      // Gọi API cập nhật profile
      await userApi.updateProfile({
        full_name: fullName.trim(),
        date_of_birth: dateOfBirth,
        gender: gender as 'male' | 'female' | 'other',
        height_cm: heightCm,
        activity_level: 'lightly_active',
      });

      // Ghi nhận cân nặng hiện tại
      await userApi.logWeight({
        weight_kg: currentWeightKg,
        measured_date: todayLocalISO(),
      });

      // Đánh dấu đã bắt đầu — từ đây guard effect sẽ không redirect nữa
      hasStartedRef.current = true;

      // Điều chỉnh cân đích mặc định theo loại mục tiêu
      setTargetWeightKg((tw) => {
        if (goalType === 'weight_loss') return Math.min(tw, currentWeightKg - 0.5);
        if (goalType === 'weight_gain') return Math.max(tw, currentWeightKg + 0.5);
        return currentWeightKg;
      });

      setStep(3);
    } catch (err) {
      setStep2Error(getAxiosDetail(err));
      toast.error(getAxiosDetail(err));
    } finally {
      setSavingProfile(false);
    }
  };

  const handleStep3Continue = async () => {
    setGoalError(null);
    if (weeks < 1) {
      setGoalError('Thời gian phải ít nhất 1 tuần.');
      return;
    }
    if (goalType === 'weight_loss' && targetWeightKg >= currentWeightKg) {
      setGoalError('Mục tiêu giảm cân cần cân đích nhỏ hơn cân nặng hiện tại.');
      return;
    }
    if (goalType === 'weight_gain' && targetWeightKg <= currentWeightKg) {
      setGoalError('Mục tiêu tăng cân cần cân đích lớn hơn cân nặng hiện tại.');
      return;
    }

    const preview = estimateKgPerWeek(goalType, currentWeightKg, targetWeightKg, weeks);
    if (preview !== null && preview > MAX_KG_PER_WEEK + 0.01) {
      const msg = `Tốc độ thay đổi cân ước tính (${preview.toFixed(2)} kg/tuần) vượt quá ${MAX_KG_PER_WEEK} kg/tuần. Vui lòng chỉnh cân đích hoặc số tuần.`;
      setGoalError(msg);
      toast.warning(msg);
      return;
    }

    const effectiveTarget =
      goalType === 'maintain' ? currentWeightKg : targetWeightKg;

    const payload = buildGoalPayload(currentWeightKg, effectiveTarget, weeks, goalType);

    setSavingGoal(true);
    try {
      const goal = await goalApi.create(payload);
      setCreatedGoal(goal);
      setStep(4);
      toast.success('Đã lưu mục tiêu dinh dưỡng');
    } catch (err) {
      const msg = getAxiosDetail(err);
      setGoalError(msg);
      toast.error(msg);
    } finally {
      setSavingGoal(false);
    }
  };

  const finishOnboarding = () => {
    markOnboardingComplete();
    navigate('/dashboard', { replace: true });
  };

  const progressBar = (
    <div className="flex gap-1.5 w-full max-w-md mx-auto mb-6">
      {[1, 2, 3, 4].map((i) => (
        <div
          key={i}
          className={`h-1.5 flex-1 rounded-full transition-colors ${
            i <= step ? 'bg-primary' : 'bg-gray-200'
          }`}
        />
      ))}
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-b from-emerald-50/80 via-white to-white flex flex-col">
      <div className="flex-1 w-full max-w-lg mx-auto px-4 py-8 pb-32 flex flex-col">
        {progressBar}

        {step === 1 && (
          <div className="flex-1 flex flex-col items-center text-center pt-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-primary to-emerald-600 rounded-2xl mb-6 shadow-lg shadow-emerald-200/60">
              <Leaf className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Chào mừng đến với NutriAI</h1>
            <p className="text-gray-600 text-sm leading-relaxed max-w-sm mb-10">
              Vài bước ngắn để cá nhân hóa lộ trình dinh dưỡng và mục tiêu hàng ngày cho bạn.
            </p>
            <Button className="w-full max-w-xs" onClick={() => {
              hasStartedRef.current = true;
              setStep(2);
            }}>
              Bắt đầu
            </Button>
          </div>
        )}

        {step === 2 && (
          <div className="flex-1">
            <h1 className="text-xl font-bold text-gray-900 mb-1">Thông tin cơ bản</h1>
            <p className="text-sm text-gray-500 mb-6">
              Giúp NutriAI hiểu rõ hơn về cơ thể bạn để tính toán lộ trình phù hợp.
            </p>

            {step2Error && (
              <div className="mb-4 p-3 text-sm text-red-600 bg-red-50 border border-red-100 rounded-xl">
                {step2Error}
              </div>
            )}

            <div className="space-y-4">
              <Input
                label="Họ và tên *"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Nguyễn Văn A"
              />

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Ngày sinh <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <Input
                    type="date"
                    value={dateOfBirth}
                    max={todayLocalISO()}
                    onChange={(e) => setDateOfBirth(e.target.value)}
                    className="pr-10"
                  />
                  <Calendar className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none" />
                </div>
              </div>

              <div>
                <p className="text-sm font-medium text-gray-700 mb-2">
                  Giới tính <span className="text-red-500">*</span>
                </p>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { id: 'male' as const, label: 'Nam', icon: Mars },
                    { id: 'female' as const, label: 'Nữ', icon: Venus },
                    { id: 'other' as const, label: 'Khác', icon: CircleUserRound },
                  ].map(({ id, label, icon: Icon }) => (
                    <button
                      key={id}
                      type="button"
                      onClick={() => setGender(id)}
                      className={`flex flex-col items-center gap-1 rounded-xl border-2 py-3 px-2 text-sm font-medium transition-colors ${
                        gender === id
                          ? 'border-primary text-primary bg-emerald-50/50'
                          : 'border-gray-200 text-gray-500 hover:border-gray-300'
                      }`}
                    >
                      <Icon className="w-6 h-6" />
                      {label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="font-medium text-gray-700">Chiều cao</span>
                  <span className="font-semibold text-primary">{heightCm} cm</span>
                </div>
                <input
                  type="range"
                  min={100}
                  max={220}
                  value={heightCm}
                  onChange={(e) => setHeightCm(Number(e.target.value))}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary"
                />
              </div>

              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="font-medium text-gray-700">Cân nặng hiện tại</span>
                  <span className="font-semibold text-primary">{currentWeightKg} kg</span>
                </div>
                <input
                  type="range"
                  min={35}
                  max={180}
                  step={0.1}
                  value={currentWeightKg}
                  onChange={(e) => setCurrentWeightKg(Number(e.target.value))}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary"
                />
              </div>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="flex-1">
            <h1 className="text-xl font-bold text-gray-900 mb-1">Mục tiêu của bạn là gì?</h1>
            <p className="text-sm text-gray-500 mb-5">
              Chọn mục tiêu phù hợp nhất để NutriAI cá nhân hóa thực đơn cho bạn.
            </p>

            <div className="space-y-3 mb-6">
              {(
                [
                  {
                    type: 'weight_loss' as const,
                    title: 'Giảm cân',
                    desc: 'Giảm mỡ và cải thiện vóc dáng',
                    icon: TrendingDown,
                    color: 'text-red-500',
                  },
                  {
                    type: 'weight_gain' as const,
                    title: 'Tăng cân',
                    desc: 'Tăng cơ bắp và khối lượng',
                    icon: TrendingUp,
                    color: 'text-blue-500',
                  },
                  {
                    type: 'maintain' as const,
                    title: 'Duy trì',
                    desc: 'Giữ vững cân nặng hiện tại',
                    icon: ArrowUp,
                    color: 'text-amber-500',
                  },
                  {
                    type: 'healthy_lifestyle' as const,
                    title: 'Sống khỏe',
                    desc: 'Cải thiện sức khỏe tổng quát',
                    icon: Heart,
                    color: 'text-primary',
                  },
                ] as const
              ).map((opt) => (
                <button
                  key={opt.type}
                  type="button"
                  onClick={() => {
                    setGoalType(opt.type);
                    if (opt.type === 'maintain' || opt.type === 'healthy_lifestyle') {
                      setTargetWeightKg(currentWeightKg);
                    } else if (opt.type === 'weight_loss') {
                      setTargetWeightKg((w) => Math.min(w, currentWeightKg - 0.5));
                    } else if (opt.type === 'weight_gain') {
                      setTargetWeightKg((w) => Math.max(w, currentWeightKg + 0.5));
                    }
                  }}
                  className={`w-full flex items-center gap-3 p-4 rounded-2xl border-2 text-left transition-colors ${
                    goalType === opt.type
                      ? 'border-primary bg-emerald-50/40 shadow-sm'
                      : 'border-gray-100 bg-white hover:border-gray-200'
                  }`}
                >
                  <div className={`shrink-0 ${opt.color}`}>
                    <opt.icon className="w-8 h-8" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-gray-900">{opt.title}</p>
                    <p className="text-xs text-gray-500">{opt.desc}</p>
                  </div>
                  <div
                    className={`shrink-0 w-6 h-6 rounded-full border-2 flex items-center justify-center ${
                      goalType === opt.type
                        ? 'border-primary bg-primary text-white'
                        : 'border-gray-200'
                    }`}
                  >
                    {goalType === opt.type && <Check className="w-3.5 h-3.5" />}
                  </div>
                </button>
              ))}
            </div>

            <div className="rounded-2xl border border-gray-100 bg-gray-50/50 p-4 space-y-4">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Chi tiết mục tiêu</p>

              {(goalType === 'weight_loss' ||
                goalType === 'weight_gain' ||
                goalType === 'healthy_lifestyle') && (
                <Input
                  label="Cân nặng đích (kg)"
                  type="number"
                  step={0.1}
                  min={20}
                  max={300}
                  value={String(targetWeightKg)}
                  onChange={(e) => setTargetWeightKg(Number(e.target.value))}
                />
              )}

              {goalType === 'maintain' && (
                <p className="text-sm text-gray-600">
                  Duy trì cân nặng hiện tại:{' '}
                  <strong className="text-primary">{currentWeightKg} kg</strong>
                </p>
              )}

              <div className="flex gap-2 items-end">
                <div className="flex-1">
                  <Input
                    label="Thời gian (tuần)"
                    type="number"
                    min={1}
                    max={104}
                    value={String(weeks)}
                    onChange={(e) => setWeeks(Math.max(1, Number(e.target.value) || 1))}
                  />
                </div>
                <span className="text-sm text-gray-500 pb-2.5">tuần</span>
              </div>

              {hintKgPerWeek && (
                <p className="text-sm text-amber-700 bg-amber-50 border border-amber-100 rounded-xl px-3 py-2">
                  {hintKgPerWeek}
                </p>
              )}

              {goalError && (
                <p className="text-sm text-red-600 bg-red-50 border border-red-100 rounded-xl px-3 py-2">
                  {goalError}
                </p>
              )}
            </div>
          </div>
        )}

        {step === 4 && createdGoal && (
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-9 h-9 rounded-full bg-primary text-white flex items-center justify-center">
                <Check className="w-5 h-5" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Xác nhận</h1>
                <p className="text-sm text-gray-500">Lộ trình đề xuất dựa trên chỉ số của bạn.</p>
              </div>
            </div>

            <Card className="mt-4 border-gray-100 shadow-sm">
              <CardBody className="p-4 space-y-3">
                <p className="text-xs font-bold text-gray-400 tracking-wide">THÔNG TIN CÁ NHÂN</p>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <p className="text-gray-400 text-xs uppercase">Mục tiêu</p>
                    <p className="font-semibold text-gray-900">{GOAL_LABELS[createdGoal.goal_type]}</p>
                  </div>
                  <div>
                    <p className="text-gray-400 text-xs uppercase">Cân nặng đích</p>
                    <p className="font-semibold text-gray-900">
                      {createdGoal.target_weight_kg != null
                        ? `${Math.round(createdGoal.target_weight_kg)} kg`
                        : '—'}
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-400 text-xs uppercase">Cân nặng hiện tại</p>
                    <p className="font-semibold text-gray-900">{currentWeightKg} kg</p>
                  </div>
                  <div>
                    <p className="text-gray-400 text-xs uppercase">Lộ trình</p>
                    <p className="font-semibold text-gray-900">Đề xuất</p>
                  </div>
                </div>
              </CardBody>
            </Card>

            <div className="mt-4 rounded-2xl bg-emerald-50/80 border border-emerald-100 p-4 text-center">
              <p className="text-xs text-gray-500 mb-1">Mục tiêu hàng ngày</p>
              <p className="text-3xl font-bold text-primary">
                {createdGoal.daily_calorie_target != null
                  ? `${Math.round(createdGoal.daily_calorie_target)} kcal`
                  : '—'}
              </p>
            </div>

            {macroBar && (
              <div className="mt-6">
                <p className="text-xs font-bold text-gray-500 tracking-wide mb-2">
                  TỶ LỆ DINH DƯỠNG (MACROS)
                </p>
                <div className="flex h-3 rounded-full overflow-hidden bg-gray-100">
                  <div
                    className="h-full bg-blue-400 transition-all"
                    style={{ width: `${macroBar.c}%` }}
                    title="Carbs"
                  />
                  <div
                    className="h-full bg-primary transition-all"
                    style={{ width: `${macroBar.p}%` }}
                    title="Protein"
                  />
                  <div
                    className="h-full bg-orange-400 transition-all"
                    style={{ width: `${macroBar.f}%` }}
                    title="Fat"
                  />
                </div>
                <div className="flex justify-between text-xs text-gray-500 mt-2">
                  <span>Carbs ~{Math.round(macroBar.c)}%</span>
                  <span>Protein ~{Math.round(macroBar.p)}%</span>
                  <span>Fat ~{Math.round(macroBar.f)}%</span>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Footer nav */}
      {(step === 2 || step === 3 || step === 4) && (
        <div className="fixed bottom-0 left-0 right-0 p-4 bg-white/95 border-t border-gray-100 backdrop-blur-sm">
          <div className="max-w-lg mx-auto flex gap-3">
            {step > 1 && (
              <Button
                variant="outline"
                className="flex-1"
                onClick={() => {
                  if (step === 4) {
                    setCreatedGoal(null);
                    setGoalError(null);
                    setStep(3);
                  } else {
                    setStep((s) => (s > 1 ? ((s - 1) as 1 | 2 | 3 | 4) : s));
                  }
                }}
              >
                Quay lại
              </Button>
            )}
            {step === 2 && (
              <Button
                className="flex-[2]"
                isLoading={savingProfile}
                onClick={handleStep2Continue}
              >
                Tiếp tục
              </Button>
            )}
            {step === 3 && (
              <Button
                className="flex-[2]"
                isLoading={savingGoal}
                onClick={handleStep3Continue}
              >
                Tiếp tục
              </Button>
            )}
            {step === 4 && (
              <div className="flex flex-col flex-[2] gap-2">
                <Button className="w-full" onClick={finishOnboarding}>
                  Tiếp tục đăng nhập
                </Button>
                <button
                  type="button"
                  className="text-sm text-gray-500 hover:text-gray-800"
                  onClick={() => {
                    setCreatedGoal(null);
                    setGoalError(null);
                    setStep(3);
                  }}
                >
                  Quay lại chỉnh sửa
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
