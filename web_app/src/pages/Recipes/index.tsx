import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link, useNavigate } from 'react-router-dom';
import { Plus, Search, Clock, Users, ChefHat, Flame, Sparkles } from 'lucide-react';
import { Card, CardBody, Button, Badge, Skeleton, EmptyState } from '../../components/ui';
import { PageContainer } from '../../components/layout';
import { recipeApi } from '../../api/recipe';

export default function RecipesPage() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(1);
  const [category, setCategory] = useState('');

  const limit = 12;
  const skip = (page - 1) * limit;

  // Search recipes
  const { data: searchResults, isLoading: searchLoading } = useQuery({
    queryKey: ['recipeSearch', searchQuery],
    queryFn: () => recipeApi.searchRecipes(searchQuery, 50),
    enabled: searchQuery.length >= 2,
  });

  // Get recipes
  const { data: recipesData, isLoading: recipesLoading } = useQuery({
    queryKey: ['recipes', skip, limit, category],
    queryFn: () => recipeApi.getRecipes({ skip, limit, category: category || undefined }),
  });

  // Get categories
  const { data: categories } = useQuery({
    queryKey: ['recipeCategories'],
    queryFn: () => recipeApi.getCategories(),
  });

  const recipes = searchQuery.length >= 2 ? searchResults : recipesData;
  const total = searchQuery.length >= 2 ? (searchResults?.length || 0) : (recipesData?.length || 0);
  const totalPages = Math.ceil(total / limit);

  const getDifficultyColor = (level: string) => {
    switch (level) {
      case 'easy': return 'success';
      case 'medium': return 'warning';
      case 'hard': return 'error';
      default: return 'default';
    }
  };

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
      title="Công thức nấu ăn"
      subtitle={`${total} công thức có sẵn`}
      action={
        <Link to="/recipes/new">
          <Button leftIcon={<Plus className="w-4 h-4" />}>Tạo công thức</Button>
        </Link>
      }
    >
      {/* Search */}
      <Card className="mb-6 border-gray-200/80 bg-white/90">
        <CardBody className="space-y-4">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Tìm kiếm công thức..."
              value={searchQuery}
              onChange={(e) => { setSearchQuery(e.target.value); setPage(1); }}
              className="w-full pl-11 pr-4 py-3.5 rounded-2xl border border-gray-200 bg-white shadow-sm focus:border-primary focus:ring-4 focus:ring-primary/10"
            />
          </div>

          {/* Category Filters */}
          <div className="flex gap-2 flex-wrap">
            <button
              onClick={() => { setCategory(''); setPage(1); }}
              className={`px-3.5 py-2 rounded-full text-sm font-medium transition-colors ${
                category === '' ? 'bg-primary text-white shadow-sm' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              Tất cả
            </button>
            {categories?.map(cat => (
              <button
                key={cat}
                onClick={() => { setCategory(cat); setPage(1); }}
                className={`px-3.5 py-2 rounded-full text-sm font-medium transition-colors ${
                  category === cat ? 'bg-primary text-white shadow-sm' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </CardBody>
      </Card>

      {/* Recipes Grid */}
      {searchLoading || recipesLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {Array.from({ length: limit }).map((_, i) => (
            <Skeleton key={i} className="h-64 w-full rounded-xl" />
          ))}
        </div>
      ) : recipes && recipes.length > 0 ? (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {recipes.map((recipe) => (
              <RecipeCard key={recipe.recipe_id} recipe={recipe} getDifficultyColor={getDifficultyColor} getDifficultyLabel={getDifficultyLabel} />
            ))}
          </div>
          {totalPages > 1 && (
            <div className="mt-6 flex justify-center">
              <Button variant="outline" onClick={() => setPage(p => p - 1)} disabled={page === 1}>Trước</Button>
              <span className="px-4 py-2">{page} / {totalPages}</span>
              <Button variant="outline" onClick={() => setPage(p => p + 1)} disabled={page === totalPages}>Sau</Button>
            </div>
          )}
        </>
      ) : (
        <EmptyState
          title="Không tìm thấy"
          description={searchQuery ? `Không có công thức nào phù hợp với "${searchQuery}"` : 'Không có công thức nào'}
          action={{ label: 'Tạo công thức đầu tiên', onClick: () => navigate('/recipes/new') }}
        />
      )}
    </PageContainer>
  );
}

interface Recipe {
  recipe_id: string;
  name_vi: string;
  category: string;
  difficulty_level: string;
  prep_time_minutes: number;
  cook_time_minutes: number;
  servings: number;
  calories_per_serving: number;
  protein_per_serving: number;
  image_url: string | null;
  is_verified: boolean;
  favorite_count: number;
}

function RecipeCard({ recipe, getDifficultyColor, getDifficultyLabel }: { recipe: Recipe; getDifficultyColor: (l: string) => string; getDifficultyLabel: (l: string) => string }) {
  const totalTime = recipe.prep_time_minutes + recipe.cook_time_minutes;

  return (
    <Link to={`/recipes/${recipe.recipe_id}`} className="block h-full">
      <Card hoverable className="overflow-hidden h-full">
      <div className="h-40 bg-gradient-to-br from-green-50 via-emerald-50 to-white flex items-center justify-center relative">
        <ChefHat className="w-16 h-16 text-primary/30" />
        <Sparkles className="absolute bottom-3 right-3 w-5 h-5 text-primary/25" />
        {recipe.is_verified && (
          <Badge variant="success" className="absolute top-2 right-2">Đã xác minh</Badge>
        )}
      </div>
      <CardBody className="p-4">
        <h3 className="font-semibold text-gray-900 line-clamp-1 mb-1">{recipe.name_vi}</h3>
        <p className="text-sm text-gray-500 mb-3">{recipe.category}</p>

        <div className="flex items-center gap-3 mb-3 text-sm text-gray-500">
          <span className="flex items-center gap-1">
            <Clock className="w-4 h-4" />
            {totalTime} phút
          </span>
          <span className="flex items-center gap-1">
            <Users className="w-4 h-4" />
            {recipe.servings} người
          </span>
          <Badge variant={getDifficultyColor(recipe.difficulty_level) as any} className="text-xs">
            {getDifficultyLabel(recipe.difficulty_level)}
          </Badge>
        </div>

        <div className="grid grid-cols-2 gap-3 pt-3 border-t border-gray-100">
          <div className="rounded-xl bg-orange-50 p-3">
            <div className="flex items-center gap-2 text-orange-600 mb-1">
              <Flame className="w-4 h-4" />
              <span className="text-xs font-medium uppercase tracking-wide">Calories</span>
            </div>
            <p className="font-semibold text-gray-900">{recipe.calories_per_serving} kcal</p>
          </div>
          <div className="rounded-xl bg-purple-50 p-3">
            <p className="text-xs font-medium uppercase tracking-wide text-purple-600 mb-1">Protein</p>
            <p className="font-semibold text-gray-900">{Math.round(recipe.protein_per_serving)}g</p>
          </div>
        </div>
      </CardBody>
      </Card>
    </Link>
  );
}