import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, Heart, Clock, Users, ChefHat, Flame, Beef, Wheat, Droplets, Share2 } from 'lucide-react';
import { Card, CardBody, Button, Badge, Skeleton, useToast } from '../../components/ui';
import { PageContainer } from '../../components/layout';
import { recipeApi } from '../../api/recipe';

export default function RecipeDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const toast = useToast();
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState('ingredients');

  // Fetch recipe detail
  const { data: recipe, isLoading, error } = useQuery({
    queryKey: ['recipe', id],
    queryFn: () => recipeApi.getRecipeDetail(id!),
    enabled: !!id,
  });

  // Toggle favorite mutation
  const toggleFavoriteMutation = useMutation({
    mutationFn: async () => {
      if (recipe?.is_favorited) {
        await recipeApi.removeFavorite(id!);
        return;
      }

      await recipeApi.addFavorite(id!);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recipe', id] });
      toast.success(recipe?.is_favorited ? 'Đã xóa khỏi yêu thích' : 'Đã thêm vào yêu thích');
    },
    onError: () => {
      toast.error('Có lỗi xảy ra');
    },
  });

  if (isLoading) {
    return (
      <PageContainer title="Chi tiết công thức">
        <div className="max-w-3xl mx-auto">
          <Skeleton className="h-64 w-full mb-6" />
          <Skeleton className="h-8 w-1/2 mb-4" />
          <Skeleton className="h-48 w-full" />
        </div>
      </PageContainer>
    );
  }

  if (error || !recipe) {
    return (
      <PageContainer title="Chi tiết công thức">
        <div className="text-center py-12">
          <p className="text-gray-500 mb-4">Không tìm thấy công thức này</p>
          <Button variant="outline" onClick={() => navigate('/recipes')}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Quay lại danh sách
          </Button>
        </div>
      </PageContainer>
    );
  }

  const totalTime = (recipe.prep_time_minutes || 0) + (recipe.cook_time_minutes || 0);

  const instructionSteps = Array.isArray(recipe.instructions)
    ? recipe.instructions
    : typeof recipe.instructions === 'string'
      ? recipe.instructions
          .split('\n')
          .map((step: string) => step.trim())
          .filter(Boolean)
      : [];

  const getDifficultyLabel = (level: string) => {
    switch (level) {
      case 'easy': return 'Dễ';
      case 'medium': return 'Trung bình';
      case 'hard': return 'Khó';
      default: return level;
    }
  };

  return (
    <PageContainer
      title={recipe.name_vi}
      action={
        <Button variant="outline" onClick={() => navigate('/recipes')}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Quay lại
        </Button>
      }
    >
      <div className="max-w-4xl mx-auto">
        {/* Recipe Header */}
        <Card className="mb-6">
          <div className="relative">
            <div className="h-64 bg-gradient-to-br from-green-50 to-emerald-50 flex items-center justify-center">
              <ChefHat className="w-24 h-24 text-primary/20" />
            </div>
            {recipe.is_verified && (
              <Badge variant="success" className="absolute top-4 right-4">
                Đã xác minh
              </Badge>
            )}
          </div>
          <CardBody>
            <div className="flex items-start justify-between mb-4">
              <div>
                <h1 className="text-2xl font-bold text-gray-900 mb-2">{recipe.name_vi}</h1>
                {recipe.name_en && (
                  <p className="text-gray-500 mb-3">{recipe.name_en}</p>
                )}
                <p className="text-gray-600">{recipe.description}</p>
              </div>
              <Button
                variant={recipe.is_favorited ? 'primary' : 'outline'}
                onClick={() => toggleFavoriteMutation.mutate()}
                leftIcon={<Heart className={`w-4 h-4 ${recipe.is_favorited ? 'fill-current' : ''}`} />}
              >
                {recipe.is_favorited ? 'Yêu thích' : 'Lưu'}
              </Button>
            </div>

            {/* Meta Info */}
            <div className="flex flex-wrap gap-4 mb-6">
              <div className="flex items-center gap-2 text-gray-600">
                <Clock className="w-5 h-5" />
                <span>{totalTime} phút</span>
              </div>
              <div className="flex items-center gap-2 text-gray-600">
                <Users className="w-5 h-5" />
                <span>{recipe.servings} người</span>
              </div>
              <Badge variant={recipe.difficulty_level === 'easy' ? 'success' : recipe.difficulty_level === 'medium' ? 'warning' : 'error'}>
                {getDifficultyLabel(recipe.difficulty_level)}
              </Badge>
              <span className="px-3 py-1 bg-gray-100 rounded-full text-sm text-gray-600">
                {recipe.category}
              </span>
            </div>

            {/* Nutrition Summary */}
            <div className="grid grid-cols-4 gap-4 p-4 bg-gray-50 rounded-xl">
              <div className="text-center">
                <Flame className="w-5 h-5 mx-auto text-orange-500 mb-1" />
                <p className="text-xl font-bold text-gray-900">{recipe.calories_per_serving}</p>
                <p className="text-xs text-gray-500">kcal</p>
              </div>
              <div className="text-center">
                <Beef className="w-5 h-5 mx-auto text-purple-500 mb-1" />
                <p className="text-xl font-bold text-gray-900">{recipe.protein_per_serving}g</p>
                <p className="text-xs text-gray-500">Protein</p>
              </div>
              <div className="text-center">
                <Wheat className="w-5 h-5 mx-auto text-yellow-500 mb-1" />
                <p className="text-xl font-bold text-gray-900">{recipe.carbs_per_serving}g</p>
                <p className="text-xs text-gray-500">Carbs</p>
              </div>
              <div className="text-center">
                <Droplets className="w-5 h-5 mx-auto text-blue-500 mb-1" />
                <p className="text-xl font-bold text-gray-900">{recipe.fat_per_serving}g</p>
                <p className="text-xs text-gray-500">Fat</p>
              </div>
            </div>
          </CardBody>
        </Card>

        {/* Tabs */}
        <Card>
          <div className="flex px-4 border-b border-gray-200">
            <button
              onClick={() => setActiveTab('ingredients')}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'ingredients'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Nguyên liệu
            </button>
            <button
              onClick={() => setActiveTab('instructions')}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'instructions'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Cách làm
            </button>
            <button
              onClick={() => setActiveTab('nutrition')}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'nutrition'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Dinh dưỡng
            </button>
          </div>

          <CardBody className="p-6">
            {activeTab === 'ingredients' && (
              <div className="space-y-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-gray-900">Nguyên liệu cho {recipe.servings} người</h3>
                  <Button size="sm" variant="outline" leftIcon={<Share2 className="w-4 h-4" />}>
                    Chia sẻ
                  </Button>
                </div>
                <div className="space-y-3">
                  {recipe.ingredients?.map((ing: any, index: number) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center text-primary font-medium text-sm">
                          {index + 1}
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">{ing.ingredient_name}</p>
                          <p className="text-sm text-gray-500">{ing.notes || ''}</p>
                        </div>
                      </div>
                      <p className="text-sm text-gray-600">
                        {ing.quantity} {ing.unit}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'instructions' && (
              <div className="space-y-6">
                <h3 className="font-semibold text-gray-900">Các bước thực hiện</h3>
                {instructionSteps.length > 0 ? instructionSteps.map((step: string, index: number) => (
                  <div key={index} className="flex gap-4">
                    <div className="w-10 h-10 bg-primary text-white rounded-full flex items-center justify-center font-bold flex-shrink-0">
                      {index + 1}
                    </div>
                    <div className="flex-1 pt-2">
                      <p className="text-gray-700 leading-relaxed">{step}</p>
                    </div>
                  </div>
                )) : (
                  <p className="text-gray-500">Chưa có hướng dẫn nấu ăn</p>
                )}
              </div>
            )}

            {activeTab === 'nutrition' && (
              <div className="space-y-4">
                <h3 className="font-semibold text-gray-900">Thông tin dinh dưỡng (mỗi phần)</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-orange-50 rounded-xl">
                    <div className="flex items-center gap-2 mb-2">
                      <Flame className="w-5 h-5 text-orange-500" />
                      <span className="text-gray-600">Calories</span>
                    </div>
                    <p className="text-3xl font-bold text-orange-600">{recipe.calories_per_serving}</p>
                    <p className="text-sm text-gray-500">kcal</p>
                  </div>
                  <div className="p-4 bg-purple-50 rounded-xl">
                    <div className="flex items-center gap-2 mb-2">
                      <Beef className="w-5 h-5 text-purple-500" />
                      <span className="text-gray-600">Protein</span>
                    </div>
                    <p className="text-3xl font-bold text-purple-600">{recipe.protein_per_serving}g</p>
                  </div>
                  <div className="p-4 bg-yellow-50 rounded-xl">
                    <div className="flex items-center gap-2 mb-2">
                      <Wheat className="w-5 h-5 text-yellow-500" />
                      <span className="text-gray-600">Carbs</span>
                    </div>
                    <p className="text-3xl font-bold text-yellow-600">{recipe.carbs_per_serving}g</p>
                  </div>
                  <div className="p-4 bg-blue-50 rounded-xl">
                    <div className="flex items-center gap-2 mb-2">
                      <Droplets className="w-5 h-5 text-blue-500" />
                      <span className="text-gray-600">Fat</span>
                    </div>
                    <p className="text-3xl font-bold text-blue-600">{recipe.fat_per_serving}g</p>
                  </div>
                </div>
              </div>
            )}
          </CardBody>
        </Card>
      </div>
    </PageContainer>
  );
}