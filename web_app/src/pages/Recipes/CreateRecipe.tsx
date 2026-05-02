import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, Plus, Trash2, PlusCircle } from 'lucide-react';
import { Card, CardBody, CardHeader, Button, Input, Select, useToast } from '../../components/ui';
import { PageContainer } from '../../components/layout';
import { recipeApi } from '../../api/recipe';
import { useAuthStore } from '../../stores/authStore';

export default function CreateRecipePage() {
  const navigate = useNavigate();
  const toast = useToast();
  const queryClient = useQueryClient();
  const isAdmin = useAuthStore((state) => state.user?.is_admin);

  // Redirect non-admin users
  useEffect(() => {
    if (isAdmin === false) {
      toast.error('Chỉ admin mới có quyền tạo công thức');
      navigate('/recipes');
    }
  }, [isAdmin, navigate, toast]);

  const [formData, setFormData] = useState({
    name_vi: '',
    name_en: '',
    category: '',
    difficulty_level: 'medium',
    prep_time_minutes: 15,
    cook_time_minutes: 30,
    servings: 4,
    description: '',
    instructions: '',
    tags: [] as string[],
  });

  const [ingredients, setIngredients] = useState([
    { ingredient_name: '', quantity: 100, unit: 'gram', food_id: '', notes: '' },
  ]);

  const [tagInput, setTagInput] = useState('');

  const createRecipeMutation = useMutation({
    mutationFn: () => recipeApi.createRecipe({
      name_vi: formData.name_vi,
      category: formData.category,
      servings: formData.servings,
      prep_time_minutes: formData.prep_time_minutes,
      cook_time_minutes: formData.cook_time_minutes,
      difficulty_level: formData.difficulty_level as 'easy' | 'medium' | 'hard',
      description: formData.description,
      instructions: formData.instructions,
      tags: formData.tags,
      ingredients: ingredients
        .filter((ing) => ing.ingredient_name.trim())
        .map((ing, i) => ({
          ingredient_id: `temp-${i}`,
          food_id: ing.food_id || null,
          ingredient_name: ing.ingredient_name.trim(),
          quantity: ing.quantity,
          unit: ing.unit,
          notes: ing.notes || null,
          calories: 0,
          protein: 0,
          carbs: 0,
          fat: 0,
        })),
    }),
    onSuccess: (recipe) => {
      queryClient.invalidateQueries({ queryKey: ['recipes'] });
      queryClient.invalidateQueries({ queryKey: ['recipeSearch'] });
      toast.success('Đã tạo công thức mới');
      navigate(`/recipes/${recipe.recipe_id}`);
    },
    onError: () => {
      toast.error('Tạo công thức thất bại');
    },
  });

  const handleAddIngredient = () => {
    setIngredients([...ingredients, { ingredient_name: '', quantity: 100, unit: 'gram', food_id: '', notes: '' }]);
  };

  const handleRemoveIngredient = (index: number) => {
    setIngredients(ingredients.filter((_, i) => i !== index));
  };

  const handleIngredientChange = (index: number, field: string, value: any) => {
    const newIngredients = [...ingredients];
    newIngredients[index] = { ...newIngredients[index], [field]: value };
    setIngredients(newIngredients);
  };

  const handleAddTag = () => {
    if (tagInput.trim() && !formData.tags.includes(tagInput.trim())) {
      setFormData({ ...formData, tags: [...formData.tags, tagInput.trim()] });
      setTagInput('');
    }
  };

  const handleRemoveTag = (tag: string) => {
    setFormData({ ...formData, tags: formData.tags.filter(t => t !== tag) });
  };

  const handleSubmit = () => {
    if (!formData.name_vi.trim()) {
      toast.error('Vui lòng nhập tên công thức');
      return;
    }
    if (!formData.category) {
      toast.error('Vui lòng chọn danh mục');
      return;
    }

    const validIngredients = ingredients.filter((ing) => ing.ingredient_name.trim());
    if (validIngredients.length === 0) {
      toast.error('Vui lòng nhập ít nhất 1 nguyên liệu');
      return;
    }

    createRecipeMutation.mutate();
  };

  return (
    <PageContainer
      title="Tạo công thức mới"
      action={
        <Button variant="outline" onClick={() => navigate('/recipes')}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Hủy
        </Button>
      }
    >
      <div className="max-w-3xl mx-auto space-y-6">
        {/* Basic Info */}
        <Card>
          <CardHeader>
            <h2 className="font-semibold text-gray-900">Thông tin cơ bản</h2>
          </CardHeader>
          <CardBody className="space-y-4">
            <Input
              label="Tên công thức (Tiếng Việt) *"
              value={formData.name_vi}
              onChange={(e) => setFormData({ ...formData, name_vi: e.target.value })}
              placeholder="Ví dụ: Phở bò Hà Nội"
            />
            <Input
              label="Tên công thức (English)"
              value={formData.name_en}
              onChange={(e) => setFormData({ ...formData, name_en: e.target.value })}
              placeholder="Vietnamese Beef Noodle Soup"
            />
            <div className="grid grid-cols-2 gap-4">
              <Select
                label="Danh mục *"
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                options={[
                  { value: 'Soup', label: 'Súp' },
                  { value: 'Salad', label: 'Salad' },
                  { value: 'Main Course', label: 'Món chính' },
                  { value: 'Appetizer', label: 'Khai vị' },
                  { value: 'Dessert', label: 'Tráng miệng' },
                  { value: 'Drink', label: 'Đồ uống' },
                  { value: 'Breakfast', label: 'Bữa sáng' },
                  { value: 'Snack', label: 'Snack' },
                ]}
              />
              <Select
                label="Độ khó"
                value={formData.difficulty_level}
                onChange={(e) => setFormData({ ...formData, difficulty_level: e.target.value })}
                options={[
                  { value: 'easy', label: 'Dễ' },
                  { value: 'medium', label: 'Trung bình' },
                  { value: 'hard', label: 'Khó' },
                ]}
              />
            </div>
            <div className="grid grid-cols-4 gap-4">
              <Input
                label="Chuẩn bị (phút)"
                type="number"
                value={formData.prep_time_minutes}
                onChange={(e) => setFormData({ ...formData, prep_time_minutes: parseInt(e.target.value) || 0 })}
              />
              <Input
                label="Nấu (phút)"
                type="number"
                value={formData.cook_time_minutes}
                onChange={(e) => setFormData({ ...formData, cook_time_minutes: parseInt(e.target.value) || 0 })}
              />
              <Input
                label="Khẩu phần"
                type="number"
                value={formData.servings}
                onChange={(e) => setFormData({ ...formData, servings: parseInt(e.target.value) || 1 })}
              />
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Tags</label>
                <div className="flex flex-wrap gap-2">
                  {formData.tags.map(tag => (
                    <span key={tag} className="px-2 py-1 bg-primary/10 text-primary rounded-full text-sm flex items-center gap-1">
                      {tag}
                      <button onClick={() => handleRemoveTag(tag)} className="hover:text-primary/70">&times;</button>
                    </span>
                  ))}
                </div>
              </div>
            </div>
            <div className="flex gap-2">
              <Input
                placeholder="Thêm tag..."
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleAddTag()}
                className="flex-1"
              />
              <Button variant="outline" onClick={handleAddTag}>Thêm</Button>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Mô tả</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Mô tả ngắn về công thức..."
                rows={3}
                className="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:border-primary focus:ring-2 focus:ring-primary/20"
              />
            </div>
          </CardBody>
        </Card>

        {/* Ingredients */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <h2 className="font-semibold text-gray-900">Nguyên liệu</h2>
            <Button size="sm" variant="outline" onClick={handleAddIngredient} leftIcon={<Plus className="w-4 h-4" />}>
              Thêm nguyên liệu
            </Button>
          </CardHeader>
          <CardBody className="space-y-3">
            {ingredients.map((ing, index) => (
              <div key={index} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center text-primary font-medium text-sm">
                  {index + 1}
                </div>
                <input
                  type="text"
                  placeholder="Tên nguyên liệu"
                  value={ing.ingredient_name}
                  onChange={(e) => handleIngredientChange(index, 'ingredient_name', e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-200 rounded-lg focus:border-primary"
                />
                <input
                  type="number"
                  placeholder="Số lượng"
                  value={ing.quantity}
                  onChange={(e) => handleIngredientChange(index, 'quantity', parseFloat(e.target.value) || 0)}
                  className="w-20 px-3 py-2 border border-gray-200 rounded-lg text-center"
                />
                <select
                  value={ing.unit}
                  onChange={(e) => handleIngredientChange(index, 'unit', e.target.value)}
                  className="w-24 px-3 py-2 border border-gray-200 rounded-lg"
                >
                  <option value="gram">gram</option>
                  <option value="ml">ml</option>
                  <option value="cup">cup</option>
                  <option value="tbsp">tbsp</option>
                  <option value="tsp">tsp</option>
                  <option value="pcs">cái</option>
                </select>
                <button
                  onClick={() => handleRemoveIngredient(index)}
                  className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </CardBody>
        </Card>

        {/* Instructions */}
        <Card>
          <CardHeader>
            <h2 className="font-semibold text-gray-900">Cách làm</h2>
          </CardHeader>
          <CardBody>
            <textarea
              value={formData.instructions}
              onChange={(e) => setFormData({ ...formData, instructions: e.target.value })}
              placeholder="Viết các bước thực hiện... (mỗi bước viết trên một dòng)"
              rows={10}
              className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-primary focus:ring-2 focus:ring-primary/20"
            />
            <p className="text-sm text-gray-500 mt-2">
              Mỗi dòng là một bước. Ví dụ:
              <br />1. Cho nước vào nồi, đun sôi
              <br />2. Thêm gia vị
            </p>
          </CardBody>
        </Card>

        {/* Submit */}
        <div className="flex gap-4">
          <Button variant="outline" onClick={() => navigate('/recipes')} className="flex-1">
            Hủy
          </Button>
          <Button
            onClick={handleSubmit}
            isLoading={createRecipeMutation.isPending}
            className="flex-1"
            leftIcon={<PlusCircle className="w-4 h-4" />}
          >
            Tạo công thức
          </Button>
        </div>
      </div>
    </PageContainer>
  );
}