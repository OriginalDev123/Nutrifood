import { useState, useEffect, useCallback } from 'react';
import { X, Plus, AlertTriangle } from 'lucide-react';
import { Button, Input, Badge } from '../../components/ui';
import type { HealthProfileData } from '../../api/healthProfile';

interface HealthProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: HealthProfileData) => void;
  initialData?: HealthProfileData;
}

// Predefined options for common health conditions, allergies, and dietary preferences
const HEALTH_CONDITIONS_OPTIONS = [
  'Tiểu đường type 1',
  'Tiểu đường type 2',
  'Huyết áp cao',
  'Huyết áp thấp',
  'Bệnh tim mạch',
  'Cholesterol cao',
  'Gan nhiễm mỡ',
  'Viêm khớp',
  'Loãng xương',
  'Suy thận',
  'Hen suyễn',
  'Dị ứng',
];

const FOOD_ALLERGIES_OPTIONS = [
  'Hải sản',
  'Tôm',
  'Cua',
  'Cá',
  'Đậu phộng',
  'Đậu nành',
  'Gluten',
  'Sữa',
  'Trứng',
  'Đậu',
  'Ngô',
  'Hạt',
  'Óc chó',
  'Hạnh nhân',
  'Bột mì',
];

const DIETARY_PREFERENCES_OPTIONS = [
  'Low Carb',
  'Keto',
  'Eat Clean',
  'Vegetarian',
  'Vegan',
  'Paleo',
  'Mediterranean',
  'Dash',
  'Low Fat',
  'Low Sodium',
  'High Protein',
  'High Fiber',
  'Gluten Free',
  'Sugar Free',
  'Raw Food',
];

export function HealthProfileModal({
  isOpen,
  onClose,
  onSave,
  initialData,
}: HealthProfileModalProps) {
  const [isSaving, setIsSaving] = useState(false);

  const [healthConditions, setHealthConditions] = useState<string[]>([]);
  const [customCondition, setCustomCondition] = useState('');
  const [foodAllergies, setFoodAllergies] = useState<string[]>([]);
  const [customAllergy, setCustomAllergy] = useState('');
  const [dietaryPreferences, setDietaryPreferences] = useState<string[]>([]);
  const [customPreference, setCustomPreference] = useState('');

  // Load initial data when modal opens
  useEffect(() => {
    if (isOpen && initialData) {
      setHealthConditions(initialData.health_conditions || []);
      setFoodAllergies(initialData.food_allergies || []);
      setDietaryPreferences(initialData.dietary_preferences || []);
    } else if (!isOpen) {
      // Reset form when modal closes
      setHealthConditions([]);
      setFoodAllergies([]);
      setDietaryPreferences([]);
      setCustomCondition('');
      setCustomAllergy('');
      setCustomPreference('');
    }
  }, [isOpen, initialData]);

  const handleAddCustomCondition = useCallback(() => {
    const trimmed = customCondition.trim();
    if (trimmed && !healthConditions.includes(trimmed)) {
      setHealthConditions([...healthConditions, trimmed]);
      setCustomCondition('');
    }
  }, [customCondition, healthConditions]);

  const handleAddCustomAllergy = useCallback(() => {
    const trimmed = customAllergy.trim();
    if (trimmed && !foodAllergies.includes(trimmed)) {
      setFoodAllergies([...foodAllergies, trimmed]);
      setCustomAllergy('');
    }
  }, [customAllergy, foodAllergies]);

  const handleAddCustomPreference = useCallback(() => {
    const trimmed = customPreference.trim();
    if (trimmed && !dietaryPreferences.includes(trimmed)) {
      setDietaryPreferences([...dietaryPreferences, trimmed]);
      setCustomPreference('');
    }
  }, [customPreference, dietaryPreferences]);

  const toggleHealthCondition = (condition: string) => {
    setHealthConditions((prev) =>
      prev.includes(condition)
        ? prev.filter((c) => c !== condition)
        : [...prev, condition]
    );
  };

  const toggleAllergy = (allergy: string) => {
    setFoodAllergies((prev) =>
      prev.includes(allergy)
        ? prev.filter((a) => a !== allergy)
        : [...prev, allergy]
    );
  };

  const togglePreference = (preference: string) => {
    setDietaryPreferences((prev) =>
      prev.includes(preference)
        ? prev.filter((p) => p !== preference)
        : [...prev, preference]
    );
  };

  const removeHealthCondition = (condition: string) => {
    setHealthConditions((prev) => prev.filter((c) => c !== condition));
  };

  const removeAllergy = (allergy: string) => {
    setFoodAllergies((prev) => prev.filter((a) => a !== allergy));
  };

  const removePreference = (preference: string) => {
    setDietaryPreferences((prev) => prev.filter((p) => p !== preference));
  };

  const handleSave = () => {
    setIsSaving(true);
    try {
      // Pass local data to parent - parent will handle API call
      const data: HealthProfileData = {
        health_conditions: healthConditions,
        food_allergies: foodAllergies,
        dietary_preferences: dietaryPreferences,
      };
      onSave(data);
    } finally {
      setIsSaving(false);
    }
  };

  const handleClose = () => {
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm transition-opacity"
        onClick={handleClose}
      />

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative w-full max-w-2xl bg-white rounded-2xl shadow-xl transform transition-all">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-100">
            <div>
              <h2 className="text-xl font-bold text-gray-900">Cập nhật thể trạng</h2>
              <p className="text-sm text-gray-500 mt-1">
                Thông tin này giúp AI đề xuất thực đơn phù hợp với bạn
              </p>
            </div>
            <button
              onClick={handleClose}
              className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Content */}
          <div className="p-6 max-h-[calc(100vh-200px)] overflow-y-auto">
            <div className="space-y-6">
              {/* Health Conditions */}
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <h3 className="font-semibold text-gray-900">Điều kiện sức khỏe</h3>
                  <span className="text-xs text-gray-500">(tùy chọn)</span>
                </div>

                {/* Selected tags */}
                {healthConditions.length > 0 && (
                  <div className="flex flex-wrap gap-2 mb-3">
                    {healthConditions.map((condition) => (
                      <Badge
                        key={condition}
                        variant="info"
                        className="cursor-pointer pr-1"
                        onClick={() => removeHealthCondition(condition)}
                      >
                        {condition}
                        <X className="w-3 h-3 ml-1" />
                      </Badge>
                    ))}
                  </div>
                )}

                {/* Options */}
                <div className="flex flex-wrap gap-2 mb-3">
                  {HEALTH_CONDITIONS_OPTIONS.filter(
                    (opt) => !healthConditions.includes(opt)
                  ).map((condition) => (
                    <button
                      key={condition}
                      onClick={() => toggleHealthCondition(condition)}
                      className="px-3 py-1.5 text-sm rounded-full border border-gray-200 text-gray-600 hover:border-primary hover:text-primary transition-colors"
                    >
                      {condition}
                    </button>
                  ))}
                </div>

                {/* Custom input */}
                <div className="flex gap-2">
                  <Input
                    placeholder="Thêm điều kiện khác..."
                    value={customCondition}
                    onChange={(e) => setCustomCondition(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        handleAddCustomCondition();
                      }
                    }}
                    className="flex-1"
                  />
                  <Button
                    variant="outline"
                    onClick={handleAddCustomCondition}
                    disabled={!customCondition.trim()}
                    size="sm"
                  >
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              {/* Food Allergies */}
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <h3 className="font-semibold text-gray-900">Dị ứng thực phẩm</h3>
                  <span className="text-xs text-gray-500">(tùy chọn)</span>
                  <span className="flex items-center text-xs text-amber-600">
                    <AlertTriangle className="w-3 h-3 mr-1" />
                    Quan trọng
                  </span>
                </div>

                {/* Selected tags */}
                {foodAllergies.length > 0 && (
                  <div className="flex flex-wrap gap-2 mb-3">
                    {foodAllergies.map((allergy) => (
                      <Badge
                        key={allergy}
                        variant="error"
                        className="cursor-pointer pr-1"
                        onClick={() => removeAllergy(allergy)}
                      >
                        {allergy}
                        <X className="w-3 h-3 ml-1" />
                      </Badge>
                    ))}
                  </div>
                )}

                {/* Options */}
                <div className="flex flex-wrap gap-2 mb-3">
                  {FOOD_ALLERGIES_OPTIONS.filter(
                    (opt) => !foodAllergies.includes(opt)
                  ).map((allergy) => (
                    <button
                      key={allergy}
                      onClick={() => toggleAllergy(allergy)}
                      className="px-3 py-1.5 text-sm rounded-full border border-gray-200 text-gray-600 hover:border-red-400 hover:text-red-500 transition-colors"
                    >
                      {allergy}
                    </button>
                  ))}
                </div>

                {/* Custom input */}
                <div className="flex gap-2">
                  <Input
                    placeholder="Thêm dị ứng khác..."
                    value={customAllergy}
                    onChange={(e) => setCustomAllergy(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        handleAddCustomAllergy();
                      }
                    }}
                    className="flex-1"
                  />
                  <Button
                    variant="outline"
                    onClick={handleAddCustomAllergy}
                    disabled={!customAllergy.trim()}
                    size="sm"
                  >
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              {/* Dietary Preferences */}
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <h3 className="font-semibold text-gray-900">Chế độ ăn ưu tiên</h3>
                  <span className="text-xs text-gray-500">(tùy chọn)</span>
                </div>

                {/* Selected tags */}
                {dietaryPreferences.length > 0 && (
                  <div className="flex flex-wrap gap-2 mb-3">
                    {dietaryPreferences.map((preference) => (
                      <Badge
                        key={preference}
                        variant="success"
                        className="cursor-pointer pr-1"
                        onClick={() => removePreference(preference)}
                      >
                        {preference}
                        <X className="w-3 h-3 ml-1" />
                      </Badge>
                    ))}
                  </div>
                )}

                {/* Options */}
                <div className="flex flex-wrap gap-2 mb-3">
                  {DIETARY_PREFERENCES_OPTIONS.filter(
                    (opt) => !dietaryPreferences.includes(opt)
                  ).map((preference) => (
                    <button
                      key={preference}
                      onClick={() => togglePreference(preference)}
                      className="px-3 py-1.5 text-sm rounded-full border border-gray-200 text-gray-600 hover:border-emerald-400 hover:text-emerald-600 transition-colors"
                    >
                      {preference}
                    </button>
                  ))}
                </div>

                {/* Custom input */}
                <div className="flex gap-2">
                  <Input
                    placeholder="Thêm chế độ ăn khác..."
                    value={customPreference}
                    onChange={(e) => setCustomPreference(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        handleAddCustomPreference();
                      }
                    }}
                    className="flex-1"
                  />
                  <Button
                    variant="outline"
                    onClick={handleAddCustomPreference}
                    disabled={!customPreference.trim()}
                    size="sm"
                  >
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-100 bg-gray-50 rounded-b-2xl">
            <Button variant="outline" onClick={handleClose} disabled={isSaving}>
              Hủy
            </Button>
            <Button onClick={handleSave} isLoading={isSaving}>
              Lưu thể trạng
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
