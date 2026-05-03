import { Heart, AlertTriangle, UtensilsCrossed } from 'lucide-react';
import { Badge } from '../../components/ui';
import type { HealthProfileData } from '../../api/healthProfile';

interface HealthProfileDisplayProps {
  data: HealthProfileData;
  onEdit?: () => void;
  compact?: boolean;
}

export function HealthProfileDisplay({
  data,
  onEdit,
  compact = false,
}: HealthProfileDisplayProps) {
  const hasData =
    (data.health_conditions && data.health_conditions.length > 0) ||
    (data.food_allergies && data.food_allergies.length > 0) ||
    (data.dietary_preferences && data.dietary_preferences.length > 0);

  if (!hasData) {
    return (
      <div className="text-center py-6 text-gray-500">
        <p className="text-sm">Chưa có thông tin thể trạng</p>
        {onEdit && (
          <button
            onClick={onEdit}
            className="mt-2 text-sm text-primary hover:text-primary/80"
          >
            Nhập thông tin thể trạng
          </button>
        )}
      </div>
    );
  }

  if (compact) {
    return (
      <div className="flex flex-wrap items-center gap-2">
        {data.health_conditions && data.health_conditions.length > 0 && (
          <Badge variant="info" className="text-xs">
            <Heart className="w-3 h-3 mr-1" />
            {data.health_conditions.length} điều kiện
          </Badge>
        )}
        {data.food_allergies && data.food_allergies.length > 0 && (
          <Badge variant="danger" className="text-xs">
            <AlertTriangle className="w-3 h-3 mr-1" />
            {data.food_allergies.length} dị ứng
          </Badge>
        )}
        {data.dietary_preferences && data.dietary_preferences.length > 0 && (
          <Badge variant="success" className="text-xs">
            <UtensilsCrossed className="w-3 h-3 mr-1" />
            {data.dietary_preferences.length} chế độ
          </Badge>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Health Conditions */}
      {data.health_conditions && data.health_conditions.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Heart className="w-4 h-4 text-blue-500" />
            <span className="text-sm font-medium text-gray-700">
              Điều kiện sức khỏe
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {data.health_conditions.map((condition) => (
              <Badge key={condition} variant="info">
                {condition}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Food Allergies */}
      {data.food_allergies && data.food_allergies.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-4 h-4 text-amber-500" />
            <span className="text-sm font-medium text-gray-700">Dị ứng thực phẩm</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {data.food_allergies.map((allergy) => (
              <Badge key={allergy} variant="danger">
                {allergy}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Dietary Preferences */}
      {data.dietary_preferences && data.dietary_preferences.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-2">
            <UtensilsCrossed className="w-4 h-4 text-emerald-500" />
            <span className="text-sm font-medium text-gray-700">Chế độ ăn ưu tiên</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {data.dietary_preferences.map((preference) => (
              <Badge key={preference} variant="success">
                {preference}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Edit button */}
      {onEdit && (
        <button
          onClick={onEdit}
          className="text-sm text-primary hover:text-primary/80 transition-colors"
        >
          Chỉnh sửa thể trạng
        </button>
      )}
    </div>
  );
}
