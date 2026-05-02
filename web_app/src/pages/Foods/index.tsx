import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, Grid, List } from 'lucide-react';
import { Card, CardBody, Badge, Pagination, Skeleton, EmptyState } from '../../components/ui';
import { PageContainer } from '../../components/layout';
import { foodApi } from '../../api/food';
import type { Food } from '../../api/types';

export default function FoodsPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [page, setPage] = useState(1);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  // Debounce search query (300ms delay)
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(searchQuery);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const limit = 12;
  const skip = (page - 1) * limit;

  // Search foods (only when debounced query >= 2 chars)
  const { data: searchResults, isLoading: searchLoading } = useQuery({
    queryKey: ['foodSearch', debouncedQuery],
    queryFn: () => foodApi.searchFoods(debouncedQuery),
    enabled: debouncedQuery.length >= 2,
  });

  // Get foods list
  const { data: foodsData, isLoading: foodsLoading } = useQuery({
    queryKey: ['foods', skip, limit],
    queryFn: () => foodApi.getFoods({ skip, limit }),
  });

  // Category display names
  const categoryLabels: Record<string, string> = {
    '': 'Tất cả',
    'protein': 'Thịt & Protein',
    'carbohydrate': 'Tinh bột',
    'iron-fiber': 'Rau củ & Đậu',
    'fat-protein': 'Mỡ & Đạm',
    'sugar-fat': 'Đường & Mỡ',
    'milk': 'Sữa',
    'vegetable': 'Rau',
    'fruit': 'Trái cây',
    'snack': 'Snack',
    'soup': 'Súp',
    'sauce': 'Nước chấm',
    'drink': 'Đồ uống',
  };

  const getCategoryLabel = (cat: string) => categoryLabels[cat] || cat;

  const foods = debouncedQuery.length >= 2 ? searchResults?.foods : foodsData?.foods;
  const total = debouncedQuery.length >= 2 ? (searchResults?.total || 0) : (foodsData?.total || 0);
  const totalPages = Math.ceil(total / limit);

  return (
    <PageContainer
      title="Thực phẩm"
      subtitle={`${total} thực phẩm trong cơ sở dữ liệu`}
    >
      {/* Search & Filters */}
      <Card className="mb-6 border-gray-200/80 bg-white/90">
        <CardBody className="space-y-4">
          <div className="flex flex-col gap-4 lg:flex-row">
            <div className="flex-1 relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Tìm kiếm thực phẩm..."
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setPage(1);
                }}
                className="w-full pl-11 pr-4 py-3.5 rounded-2xl border border-gray-200 bg-white shadow-sm focus:border-primary focus:ring-4 focus:ring-primary/10"
              />
            </div>
            <div className="flex items-center gap-2 self-start bg-white border border-gray-200 rounded-2xl p-1 shadow-sm">
              <button
                onClick={() => setViewMode('grid')}
                className={`p-2.5 rounded-xl ${viewMode === 'grid' ? 'bg-primary text-white shadow-sm' : 'text-gray-500 hover:bg-gray-50'}`}
              >
                <Grid className="w-5 h-5" />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`p-2.5 rounded-xl ${viewMode === 'list' ? 'bg-primary text-white shadow-sm' : 'text-gray-500 hover:bg-gray-50'}`}
              >
                <List className="w-5 h-5" />
              </button>
            </div>
          </div>

        </CardBody>
      </Card>

      {/* Foods Grid/List */}
      {searchLoading || foodsLoading ? (
        <div className={viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4' : 'space-y-3'}>
          {Array.from({ length: limit }).map((_, i) => (
            <Skeleton key={i} className={viewMode === 'grid' ? 'h-48 w-full rounded-xl' : 'h-20 w-full rounded-xl'} />
          ))}
        </div>
      ) : foods && foods.length > 0 ? (
        <>
          <div className={viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4' : 'space-y-3'}>
            {foods.map((food: Food) => (
              viewMode === 'grid' ? (
                <FoodCard key={food.food_id} food={food} getCategoryLabel={getCategoryLabel} />
              ) : (
                <FoodListItem key={food.food_id} food={food} getCategoryLabel={getCategoryLabel} />
              )
            ))}
          </div>

          {totalPages > 1 && (
            <div className="mt-6 flex justify-center">
              <Pagination
                currentPage={page}
                totalPages={totalPages}
                onPageChange={setPage}
              />
            </div>
          )}
        </>
      ) : (
        <EmptyState
          title="Không tìm thấy"
          description={searchQuery ? `Không có thực phẩm nào phù hợp với "${searchQuery}"` : 'Không có thực phẩm nào'}
        />
      )}
    </PageContainer>
  );
}

function FoodCard({ food, getCategoryLabel }: { food: Food; getCategoryLabel: (cat: string) => string }) {
  return (
    <Card hoverable className="overflow-hidden">
      <div className="relative h-32 bg-gradient-to-br from-green-50 to-emerald-50 flex items-center justify-center">
        <span className="text-5xl">🍎</span>
        <Badge variant={food.is_verified ? 'success' : 'default'} className="absolute right-3 top-3">
          {food.is_verified ? 'Đã xác minh' : 'Chưa xác minh'}
        </Badge>
      </div>
      <CardBody className="p-4">
        <h3 className="font-semibold text-gray-900 line-clamp-1">{food.name_vi}</h3>
        <p className="text-sm text-gray-500 mb-3">{getCategoryLabel(food.category)}</p>
        <div className="grid grid-cols-2 gap-2">
          <div className="rounded-xl bg-orange-50 p-2.5 text-center">
            <p className="text-xs text-gray-500">Calories</p>
            <p className="font-semibold text-orange-700 text-sm">{food.calories_per_100g} kcal</p>
          </div>
          <div className="rounded-xl bg-purple-50 p-2.5 text-center">
            <p className="text-xs text-gray-500">Protein</p>
            <p className="font-semibold text-purple-700 text-sm">{food.protein_per_100g}g</p>
          </div>
          <div className="rounded-xl bg-yellow-50 p-2.5 text-center">
            <p className="text-xs text-gray-500">Carbs</p>
            <p className="font-semibold text-yellow-700 text-sm">{food.carbs_per_100g}g</p>
          </div>
          <div className="rounded-xl bg-emerald-50 p-2.5 text-center">
            <p className="text-xs text-gray-500">Fat</p>
            <p className="font-semibold text-emerald-700 text-sm">{food.fat_per_100g}g</p>
          </div>
        </div>
      </CardBody>
    </Card>
  );
}

function FoodListItem({ food, getCategoryLabel }: { food: Food; getCategoryLabel: (cat: string) => string }) {
  return (
    <Card hoverable>
      <CardBody className="flex flex-col gap-4 md:flex-row md:items-center">
        <div className="w-16 h-16 bg-gradient-to-br from-green-50 via-emerald-50 to-white rounded-2xl border border-gray-100 flex items-center justify-center">
          <span className="text-3xl">🍎</span>
        </div>
        <div className="flex-1">
          <h3 className="font-semibold text-gray-900">{food.name_vi}</h3>
          <p className="text-sm text-gray-500">{getCategoryLabel(food.category)}</p>
        </div>
        <Badge variant={food.is_verified ? 'success' : 'default'}>
          {food.is_verified ? 'Đã xác minh' : 'Chưa xác minh'}
        </Badge>
        <div className="grid grid-cols-2 gap-2 md:w-72">
          <div className="rounded-xl bg-orange-50 p-2 text-center">
            <p className="text-xs text-gray-500">Kcal</p>
            <p className="font-semibold text-orange-700 text-sm">{food.calories_per_100g}</p>
          </div>
          <div className="rounded-xl bg-purple-50 p-2 text-center">
            <p className="text-xs text-gray-500">Protein</p>
            <p className="font-semibold text-purple-700 text-sm">{food.protein_per_100g}g</p>
          </div>
          <div className="rounded-xl bg-yellow-50 p-2 text-center">
            <p className="text-xs text-gray-500">Carbs</p>
            <p className="font-semibold text-yellow-700 text-sm">{food.carbs_per_100g}g</p>
          </div>
          <div className="rounded-xl bg-emerald-50 p-2 text-center">
            <p className="text-xs text-gray-500">Fat</p>
            <p className="font-semibold text-emerald-700 text-sm">{food.fat_per_100g}g</p>
          </div>
        </div>
      </CardBody>
    </Card>
  );
}
