import { useState, useMemo, useEffect } from 'react';
import { Calendar, AlertCircle, CheckCircle, ChevronLeft, Loader2, List } from 'lucide-react';
import { Modal, Button, useToast } from '../ui';
import { mealPlanApi } from '../../api/mealPlan';
import type { MealPlan, MealPlanWithItems } from '../../api/extended';

interface ApplyPlanModalProps {
  isOpen: boolean;
  onClose: () => void;
  plan?: MealPlanWithItems;
  onSuccess?: (appliedCount: number) => void;
}

type ModalStep = 'select' | 'apply';

export function ApplyPlanModal({ isOpen, onClose, plan: initialPlan, onSuccess }: ApplyPlanModalProps) {
  const [step, setStep] = useState<ModalStep>(initialPlan ? 'apply' : 'select');
  const [plans, setPlans] = useState<MealPlan[]>([]);
  const [selectedPlan, setSelectedPlan] = useState<MealPlanWithItems | null>(initialPlan || null);
  const [isLoadingPlans, setIsLoadingPlans] = useState(false);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);
  const [startDate, setStartDate] = useState(() => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    return tomorrow.toISOString().split('T')[0];
  });
  const [isApplying, setIsApplying] = useState(false);
  const toast = useToast();

  // Reset state when modal opens
  useEffect(() => {
    if (isOpen) {
      setStep(initialPlan ? 'apply' : 'select');
      setSelectedPlan(initialPlan || null);
      setIsApplying(false);

      // Reset date to tomorrow
      const tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);
      setStartDate(tomorrow.toISOString().split('T')[0]);

      // Load plans list if no initial plan
      if (!initialPlan) {
        loadPlans();
      }
    }
  }, [isOpen, initialPlan]);

  // Load all plans for selection
  const loadPlans = async () => {
    setIsLoadingPlans(true);
    try {
      const data = await mealPlanApi.getMyPlans();
      setPlans(data || []);
    } catch {
      toast.error('Không thể tải danh sách kế hoạch');
    } finally {
      setIsLoadingPlans(false);
    }
  };

  // Load plan detail when selected
  const handleSelectPlan = async (plan: MealPlan) => {
    setIsLoadingDetail(true);
    try {
      const detail = await mealPlanApi.getPlanDetail(plan.plan_id);
      setSelectedPlan(detail);
      setStep('apply');
    } catch {
      toast.error('Không thể tải chi tiết kế hoạch');
    } finally {
      setIsLoadingDetail(false);
    }
  };

  // Computed values for selected plan
  const planDays = useMemo(() => {
    if (!selectedPlan?.start_date || !selectedPlan?.end_date) return 0;
    const start = new Date(selectedPlan.start_date);
    const end = new Date(selectedPlan.end_date);
    return Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24)) + 1;
  }, [selectedPlan?.start_date, selectedPlan?.end_date]);

  const totalItems = useMemo(() => {
    if (!selectedPlan?.days) return 0;
    return selectedPlan.days.reduce((sum, day) => sum + (day.items?.length || 0), 0);
  }, [selectedPlan?.days]);

  const endDate = useMemo(() => {
    if (!startDate || planDays === 0) return '';
    const start = new Date(startDate);
    const end = new Date(start);
    end.setDate(end.getDate() + planDays - 1);
    return end.toISOString().split('T')[0];
  }, [startDate, planDays]);

  const minDate = useMemo(() => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    return tomorrow.toISOString().split('T')[0];
  }, []);

  // Handle apply
  const handleApply = async () => {
    if (!selectedPlan) return;
    setIsApplying(true);
    try {
      const result = await mealPlanApi.applyMealPlan(selectedPlan.plan_id, startDate);
      toast.success(result.message);
      onSuccess?.(result.applied_items);
      onClose();
    } catch (error: any) {
      const message = error?.response?.data?.detail || 'Áp dụng kế hoạch thất bại';
      toast.error(message);
    } finally {
      setIsApplying(false);
    }
  };

  // Handle back to plan selection
  const handleBack = () => {
    setStep('select');
    setSelectedPlan(null);
  };

  // Format date for display
  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('vi-VN', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={step === 'select' ? 'Chọn kế hoạch ăn' : 'Áp dụng kế hoạch vào Nhật ký ăn'}
      size={step === 'select' ? 'lg' : 'md'}
      footer={
        step === 'apply' ? (
          <div className="flex gap-3 justify-end">
            {initialPlan === undefined && (
              <Button variant="outline" onClick={handleBack} leftIcon={<ChevronLeft className="w-4 h-4" />}>
                Chọn kế hoạch khác
              </Button>
            )}
            <Button variant="outline" onClick={onClose}>
              Hủy
            </Button>
            <Button
              onClick={handleApply}
              isLoading={isApplying}
              leftIcon={<CheckCircle className="w-4 h-4" />}
            >
              Áp dụng
            </Button>
          </div>
        ) : undefined
      }
    >
      {/* Step 1: Plan Selection */}
      {step === 'select' && (
        <div className="space-y-4">
          {isLoadingPlans ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : plans.length === 0 ? (
            <div className="text-center py-12">
              <List className="w-12 h-12 mx-auto text-gray-400 mb-3" />
              <p className="text-gray-500 mb-2">Bạn chưa có kế hoạch nào</p>
              <p className="text-sm text-gray-400">Hãy tạo kế hoạch ăn mới trước</p>
            </div>
          ) : (
            <div className="space-y-3 max-h-[400px] overflow-y-auto">
              <p className="text-sm text-gray-600 mb-4">
                Chọn một kế hoạch ăn để áp dụng vào Nhật ký ăn của bạn:
              </p>
              {plans.map((plan) => (
                <button
                  key={plan.plan_id}
                  onClick={() => handleSelectPlan(plan)}
                  disabled={isLoadingDetail}
                  className="w-full p-4 text-left bg-white border border-gray-200 rounded-xl hover:border-primary hover:bg-primary/5 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900">{plan.plan_name}</h3>
                      <div className="mt-2 flex flex-wrap gap-2 text-sm text-gray-600">
                        <span className="px-2 py-0.5 bg-gray-100 rounded">
                          Tạo: {formatDate(plan.created_at)}
                        </span>
                        <span className={`px-2 py-0.5 rounded ${
                          plan.status === 'active' ? 'bg-green-100 text-green-700' :
                          plan.status === 'completed' ? 'bg-blue-100 text-blue-700' :
                          'bg-gray-100 text-gray-600'
                        }`}>
                          {plan.status === 'active' ? 'Đang hoạt động' :
                           plan.status === 'completed' ? 'Hoàn thành' : 'Đã lưu trữ'}
                        </span>
                      </div>
                    </div>
                    {isLoadingDetail && selectedPlan?.plan_id === plan.plan_id && (
                      <Loader2 className="w-5 h-5 animate-spin text-primary" />
                    )}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Step 2: Apply Form */}
      {step === 'apply' && selectedPlan && (
        <div className="space-y-6">
          {/* Plan Info */}
          <div className="p-4 bg-gradient-to-r from-primary/5 to-emerald-50 rounded-xl border border-primary/10">
            <h3 className="font-semibold text-gray-900 mb-2">{selectedPlan.plan_name}</h3>
            <div className="grid grid-cols-2 gap-2 text-sm text-gray-600">
              <div>
                <span className="text-gray-500">Kế hoạch gốc:</span>
                <p>{formatDate(selectedPlan.start_date)} - {formatDate(selectedPlan.end_date)}</p>
              </div>
              <div>
                <span className="text-gray-500">Thời lượng:</span>
                <p>{planDays} ngày - {totalItems} món</p>
              </div>
            </div>
          </div>

          {/* Date Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Ngày bắt đầu áp dụng
            </label>
            <div className="relative">
              <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none" />
              <input
                type="date"
                value={startDate}
                min={minDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full pl-10 pr-4 py-3 rounded-lg border border-gray-300 focus:border-primary focus:ring-2 focus:ring-primary/20 transition-colors"
              />
            </div>
            <p className="text-xs text-gray-500 mt-1.5">
              Chọn ngày bắt đầu để áp dụng kế hoạch vào Nhật ký ăn của bạn
            </p>
          </div>

          {/* Preview */}
          {startDate && (
            <div className="p-4 bg-primary/5 border border-primary/20 rounded-xl">
              <div className="flex items-center gap-2 mb-3">
                <AlertCircle className="w-4 h-4 text-primary" />
                <span className="font-medium text-primary">Xem trước</span>
              </div>
              <p className="text-sm text-gray-700">
                Kế hoạch <strong>{selectedPlan.plan_name}</strong> sẽ được áp dụng từ ngày{' '}
                <strong>{formatDate(startDate)}</strong> đến ngày{' '}
                <strong>{formatDate(endDate)}</strong>
              </p>
              <div className="mt-3 pt-3 border-t border-primary/10">
                <p className="text-xs text-gray-600">
                  Tất cả <strong>{totalItems}</strong> món ăn trong kế hoạch sẽ được thêm vào
                  Nhật ký ăn tương ứng với các ngày trong kế hoạch.
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </Modal>
  );
}
