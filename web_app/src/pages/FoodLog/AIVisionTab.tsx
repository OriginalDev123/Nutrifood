import { useEffect, useRef, useState } from 'react';
import axios from 'axios';
import { useMutation } from '@tanstack/react-query';
import { AlertTriangle, Camera, ImagePlus, RefreshCcw, Search } from 'lucide-react';
import { Badge, Button, EmptyState, Skeleton, useToast } from '../../components/ui';
import { visionApi, type VisionAnalyzeResponse, type VisionCalculateNutritionResponse } from '../../api/vision';

const MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024;
const ACCEPTED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp'];

type MealType = 'breakfast' | 'lunch' | 'dinner' | 'snack';

interface AIVisionTabProps {
  mealDate: string;
  mealType: MealType;
  onSuccess: () => void;
  onFallbackManual: () => void;
}

function getErrorMessage(error: unknown, fallback: string) {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string' && detail.trim()) {
      return detail;
    }
  }

  if (error instanceof Error && error.message.trim()) {
    return error.message;
  }

  return fallback;
}

function getConfidenceVariant(confidence: number): 'success' | 'warning' | 'error' {
  if (confidence >= 0.8) return 'success';
  if (confidence >= 0.5) return 'warning';
  return 'error';
}

export function AIVisionTab({ mealDate, mealType, onSuccess, onFallbackManual }: AIVisionTabProps) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const cameraInputRef = useRef<HTMLInputElement | null>(null);
  const toast = useToast();

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [userHint, setUserHint] = useState('');
  const [visionContext, setVisionContext] = useState<VisionAnalyzeResponse | null>(null);
  const [selectedPresetId, setSelectedPresetId] = useState('');
  const [customPortionGrams, setCustomPortionGrams] = useState(100);
  const [quantity, setQuantity] = useState(1);
  const [errorMessage, setErrorMessage] = useState('');
  const [lastAction, setLastAction] = useState<'analyze' | 'calculate' | 'log' | null>(null);

  useEffect(() => {
    if (!selectedFile) {
      setPreviewUrl(null);
      return;
    }

    const objectUrl = URL.createObjectURL(selectedFile);
    setPreviewUrl(objectUrl);

    return () => {
      URL.revokeObjectURL(objectUrl);
    };
  }, [selectedFile]);

  const calculateMutation = useMutation({
    mutationFn: visionApi.calculateNutrition,
    onSuccess: () => {
      setErrorMessage('');
    },
    onError: (error) => {
      setLastAction('calculate');
      setErrorMessage(getErrorMessage(error, 'Không thể tính dinh dưỡng cho khẩu phần đã chọn.'));
    },
  });

  const analyzeMutation = useMutation({
    mutationFn: ({ file, hint }: { file: File; hint?: string }) => visionApi.analyzeImage(file, hint),
    onSuccess: (data) => {
      setVisionContext(data);
      setErrorMessage('');
      setLastAction(null);
      setQuantity(1);

      const defaultPreset = data.portion_presets.find((preset) => preset.is_default) ?? data.portion_presets[0];
      if (defaultPreset) {
        setSelectedPresetId(defaultPreset.preset_id);
        setCustomPortionGrams(defaultPreset.grams);
      } else {
        const fallbackGrams = data.database_match?.item_type === 'recipe' ? 400 : 100;
        setSelectedPresetId('');
        setCustomPortionGrams(fallbackGrams);
      }
    },
    onError: (error) => {
      setVisionContext(null);
      setLastAction('analyze');
      setErrorMessage(getErrorMessage(error, 'Không thể phân tích ảnh lúc này.'));
    },
  });

  const logMealMutation = useMutation({
    mutationFn: () => {
      if (!visionContext) {
        throw new Error('Chưa có kết quả AI Vision để lưu bữa ăn.');
      }

      return visionApi.logMeal({
        vision_context: visionContext,
        preset_id: selectedPresetId || undefined,
        portion_grams: selectedPresetId ? undefined : customPortionGrams,
        quantity,
        meal_type: mealType,
        meal_date: mealDate,
      });
    },
    onSuccess: () => {
      toast.success('Đã thêm bữa ăn từ AI Vision');
      onSuccess();
    },
    onError: (error) => {
      setLastAction('log');
      const message = getErrorMessage(error, 'Lưu bữa ăn thất bại.');
      setErrorMessage(message);
      toast.error(message);
    },
  });

  useEffect(() => {
    if (!visionContext || !visionContext.is_food || visionContext.needs_retry || !visionContext.database_match) {
      return;
    }

    const hasPreset = Boolean(selectedPresetId);
    const hasCustomGrams = !selectedPresetId && customPortionGrams > 0;

    if (!hasPreset && !hasCustomGrams) {
      return;
    }

    calculateMutation.mutate({
      vision_context: visionContext,
      preset_id: hasPreset ? selectedPresetId : undefined,
      portion_grams: hasPreset ? undefined : customPortionGrams,
      quantity,
    });
  }, [visionContext, selectedPresetId, customPortionGrams, quantity]);

  const validateFile = (file: File) => {
    if (!ACCEPTED_IMAGE_TYPES.includes(file.type)) {
      return 'Chỉ hỗ trợ ảnh JPG, PNG hoặc WEBP.';
    }

    if (file.size > MAX_IMAGE_SIZE_BYTES) {
      return 'Ảnh vượt quá 10MB. Vui lòng chọn ảnh nhỏ hơn.';
    }

    return '';
  };

  const resetVisionState = () => {
    setVisionContext(null);
    setSelectedPresetId('');
    setCustomPortionGrams(100);
    setQuantity(1);
    setErrorMessage('');
    setLastAction(null);
    calculateMutation.reset();
    analyzeMutation.reset();
    logMealMutation.reset();
  };

  const handleFileChange = (file: File | null) => {
    if (!file) return;

    const validationMessage = validateFile(file);
    if (validationMessage) {
      setSelectedFile(null);
      setVisionContext(null);
      setErrorMessage(validationMessage);
      toast.error(validationMessage);
      return;
    }

    resetVisionState();
    setSelectedFile(file);
  };

  const handleAnalyze = () => {
    if (!selectedFile) {
      setErrorMessage('Hãy chọn ảnh món ăn trước khi phân tích.');
      return;
    }

    const validationMessage = validateFile(selectedFile);
    if (validationMessage) {
      setErrorMessage(validationMessage);
      toast.error(validationMessage);
      return;
    }

    setLastAction('analyze');
    setErrorMessage('');
    analyzeMutation.mutate({
      file: selectedFile,
      hint: userHint.trim() || undefined,
    });
  };

  const handleRetry = () => {
    if (visionContext && !visionContext.needs_retry && lastAction === 'log') {
      logMealMutation.mutate();
      return;
    }

    handleAnalyze();
  };

  const canShowResult = Boolean(visionContext);
  const canLogMeal = Boolean(
    visionContext &&
      visionContext.is_food &&
      !visionContext.needs_retry &&
      visionContext.database_match &&
      !calculateMutation.isPending &&
      calculateMutation.data
  );

  const selectedPreset = visionContext?.portion_presets.find((preset) => preset.preset_id === selectedPresetId);
  const nutritionPreview: VisionCalculateNutritionResponse | undefined = calculateMutation.data;

  return (
    <div className="space-y-4">
      <div className="rounded-2xl border border-dashed border-primary/30 bg-primary/5 p-4">
        {!previewUrl ? (
          <EmptyState
            icon={<ImagePlus className="h-8 w-8" />}
            title="Thêm ảnh món ăn"
            description="Chọn ảnh từ máy hoặc mở camera để AI nhận diện món ăn."
            className="py-8"
          />
        ) : (
          <div className="space-y-3">
            <img
              src={previewUrl}
              alt="Xem trước món ăn"
              className="mx-auto max-h-64 rounded-xl border border-gray-200 object-cover"
            />
            <div className="flex flex-wrap justify-center gap-2">
              <Button variant="outline" onClick={() => fileInputRef.current?.click()}>
                Đổi ảnh
              </Button>
              <Button variant="ghost" onClick={() => cameraInputRef.current?.click()} leftIcon={<Camera className="h-4 w-4" />}>
                Chụp lại
              </Button>
            </div>
          </div>
        )}

        <div className="mt-4 flex flex-wrap gap-3">
          <Button type="button" onClick={() => fileInputRef.current?.click()} leftIcon={<ImagePlus className="h-4 w-4" />}>
            Chọn ảnh
          </Button>
          <Button type="button" variant="outline" onClick={() => cameraInputRef.current?.click()} leftIcon={<Camera className="h-4 w-4" />}>
            Mở camera
          </Button>
        </div>

        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          className="hidden"
          onChange={(event) => handleFileChange(event.target.files?.[0] ?? null)}
        />
        <input
          ref={cameraInputRef}
          type="file"
          accept="image/*"
          capture="environment"
          className="hidden"
          onChange={(event) => handleFileChange(event.target.files?.[0] ?? null)}
        />
      </div>

      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">Gợi ý tên món (tuỳ chọn)</label>
        <input
          type="text"
          value={userHint}
          onChange={(event) => setUserHint(event.target.value)}
          placeholder="Ví dụ: cơm tấm, bún bò, salad gà..."
          className="w-full rounded-lg border border-gray-200 px-4 py-3 focus:border-primary focus:ring-2 focus:ring-primary/20"
        />
        <p className="text-xs text-gray-500">Gợi ý sẽ giúp AI nhận diện chính xác hơn khi ảnh khó nhìn.</p>
      </div>

      <Button
        type="button"
        onClick={handleAnalyze}
        isLoading={analyzeMutation.isPending}
        leftIcon={<Camera className="h-4 w-4" />}
        className="w-full"
      >
        Phân tích ảnh
      </Button>

      {errorMessage ? (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          <div className="flex items-start gap-3">
            <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0" />
            <div className="space-y-3">
              <p>{errorMessage}</p>
              {visionContext?.retry_suggestions?.length ? (
                <ul className="list-disc space-y-1 pl-5">
                  {visionContext.retry_suggestions.map((suggestion) => (
                    <li key={suggestion}>{suggestion}</li>
                  ))}
                </ul>
              ) : null}
              <div className="flex flex-wrap gap-2">
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={handleRetry}
                  isLoading={analyzeMutation.isPending || logMealMutation.isPending}
                  leftIcon={<RefreshCcw className="h-4 w-4" />}
                >
                  Thử lại
                </Button>
                <Button type="button" size="sm" variant="ghost" onClick={onFallbackManual} leftIcon={<Search className="h-4 w-4" />}>
                  Tìm thủ công
                </Button>
              </div>
            </div>
          </div>
        </div>
      ) : null}

      {analyzeMutation.isPending ? (
        <div className="space-y-3 rounded-2xl border border-gray-200 p-4">
          <Skeleton className="h-6 w-40" />
          <Skeleton className="h-24 w-full rounded-xl" />
          <Skeleton className="h-12 w-full rounded-xl" />
        </div>
      ) : null}

      {canShowResult ? (
        <div className="space-y-4 rounded-2xl border border-gray-200 bg-white p-4">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm text-gray-500">AI nhận diện</p>
              <h3 className="text-lg font-semibold text-gray-900">{visionContext?.food_name || 'Không rõ món ăn'}</h3>
              {visionContext?.description ? (
                <p className="mt-1 text-sm text-gray-600">{visionContext.description}</p>
              ) : null}
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge variant={getConfidenceVariant(visionContext?.confidence ?? 0)}>
                {Math.round((visionContext?.confidence ?? 0) * 100)}% tự tin
              </Badge>
              {visionContext?.from_cache ? <Badge variant="info">Cache</Badge> : null}
            </div>
          </div>

          {visionContext?.database_match ? (
            <div className="rounded-xl border border-gray-200 bg-gray-50 p-4">
              <p className="text-sm text-gray-500">Khớp dữ liệu</p>
              <div className="mt-1 flex flex-wrap items-center gap-2">
                <p className="font-medium text-gray-900">{visionContext.database_match.name_vi}</p>
                <Badge variant="info">{visionContext.database_match.item_type === 'recipe' ? 'Recipe' : 'Food'}</Badge>
              </div>
            </div>
          ) : (
            <div className="rounded-xl border border-yellow-200 bg-yellow-50 p-4 text-sm text-yellow-800">
              AI chưa map được món này vào database. Bạn có thể thử lại hoặc chuyển sang tìm kiếm thủ công.
            </div>
          )}

          {visionContext?.needs_retry ? (
            <div className="rounded-xl border border-yellow-200 bg-yellow-50 p-4 text-sm text-yellow-800">
              <p className="font-medium">AI gợi ý chụp lại ảnh để có kết quả tốt hơn.</p>
              {visionContext.retry_suggestions.length ? (
                <ul className="mt-2 list-disc space-y-1 pl-5">
                  {visionContext.retry_suggestions.map((suggestion) => (
                    <li key={suggestion}>{suggestion}</li>
                  ))}
                </ul>
              ) : null}
            </div>
          ) : null}

          {visionContext?.alternatives?.length ? (
            <div className="space-y-2">
              <p className="text-sm font-medium text-gray-700">Gợi ý gần đúng</p>
              <div className="flex flex-wrap gap-2">
                {visionContext.alternatives.slice(0, 3).map((alternative) => (
                  <Badge key={`${alternative.item_type}-${alternative.item_id}`} variant="default">
                    {alternative.name_vi}
                  </Badge>
                ))}
              </div>
            </div>
          ) : null}

          <div className="space-y-3">
            <div className="flex items-center justify-between gap-3">
              <label className="text-sm font-medium text-gray-700">Chọn khẩu phần</label>
              {selectedPreset ? <Badge variant="info">{selectedPreset.grams}g</Badge> : null}
            </div>
            {visionContext?.portion_presets?.length ? (
              <div className="space-y-2">
                {visionContext.portion_presets.map((preset) => (
                  <button
                    key={preset.preset_id}
                    type="button"
                    onClick={() => {
                      setSelectedPresetId(preset.preset_id);
                      setCustomPortionGrams(preset.grams);
                    }}
                    className={`w-full rounded-xl border p-3 text-left transition-colors ${
                      selectedPresetId === preset.preset_id
                        ? 'border-primary bg-primary/10 text-primary'
                        : 'border-gray-200 bg-white hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <p className="font-medium">{preset.display_name_vi || preset.size_label}</p>
                        <p className="text-sm text-gray-500">{preset.size_label}</p>
                      </div>
                      <div className="text-sm font-medium">{preset.grams}g</div>
                    </div>
                  </button>
                ))}
              </div>
            ) : (
              <div className="rounded-xl border border-gray-200 bg-gray-50 p-4">
                <label className="block text-sm font-medium text-gray-700">Nhập khối lượng</label>
                <input
                  type="number"
                  min="1"
                  value={customPortionGrams}
                  onChange={(event) => {
                    setSelectedPresetId('');
                    setCustomPortionGrams(Math.max(1, Number(event.target.value) || 1));
                  }}
                  className="mt-2 w-full rounded-lg border border-gray-200 px-4 py-3 focus:border-primary focus:ring-2 focus:ring-primary/20"
                />
              </div>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-xl border border-gray-200 bg-gray-50 p-3 text-center">
              <p className="text-sm text-gray-500">Số lượng</p>
              <input
                type="number"
                min="0.5"
                step="0.5"
                value={quantity}
                onChange={(event) => setQuantity(Math.max(0.5, Number(event.target.value) || 1))}
                className="mx-auto mt-2 w-20 rounded-lg border border-gray-200 py-1 text-center text-xl font-bold"
              />
            </div>
            <div className="rounded-xl border border-gray-200 bg-gray-50 p-3 text-center">
              <p className="text-sm text-gray-500">Khẩu phần hiện tại</p>
              <p className="mt-2 text-xl font-bold text-primary">
                {Math.round(nutritionPreview?.total_portion_grams ?? customPortionGrams)}g
              </p>
            </div>
          </div>

          {calculateMutation.isPending ? (
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              {[1, 2, 3, 4].map((item) => (
                <Skeleton key={item} className="h-20 w-full rounded-xl" />
              ))}
            </div>
          ) : nutritionPreview ? (
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              <div className="rounded-xl border border-gray-200 bg-gray-50 p-3 text-center">
                <p className="text-sm text-gray-500">Calories</p>
                <p className="text-lg font-bold text-primary">{Math.round(nutritionPreview.nutrition.calories)} kcal</p>
              </div>
              <div className="rounded-xl border border-gray-200 bg-gray-50 p-3 text-center">
                <p className="text-sm text-gray-500">Protein</p>
                <p className="text-lg font-bold text-gray-900">{Math.round(nutritionPreview.nutrition.protein_g)}g</p>
              </div>
              <div className="rounded-xl border border-gray-200 bg-gray-50 p-3 text-center">
                <p className="text-sm text-gray-500">Carbs</p>
                <p className="text-lg font-bold text-gray-900">{Math.round(nutritionPreview.nutrition.carbs_g)}g</p>
              </div>
              <div className="rounded-xl border border-gray-200 bg-gray-50 p-3 text-center">
                <p className="text-sm text-gray-500">Fat</p>
                <p className="text-lg font-bold text-gray-900">{Math.round(nutritionPreview.nutrition.fat_g)}g</p>
              </div>
            </div>
          ) : null}

          <div className="flex flex-wrap gap-3 pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={handleRetry}
              isLoading={analyzeMutation.isPending || logMealMutation.isPending}
              leftIcon={<RefreshCcw className="h-4 w-4" />}
            >
              Phân tích lại
            </Button>
            <Button
              type="button"
              onClick={() => logMealMutation.mutate()}
              isLoading={logMealMutation.isPending}
              disabled={!canLogMeal}
              className="flex-1"
            >
              Thêm vào bữa {mealType === 'breakfast' ? 'Sáng' : mealType === 'lunch' ? 'Trưa' : mealType === 'dinner' ? 'Tối' : 'Snack'}
            </Button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
