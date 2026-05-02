import type {
  MacroDistribution,
  MealPatternsResponse,
  NutritionTrend,
  NutritionTrendsResponse,
  WeightProgressItem,
  WeightProgressResponse,
} from '../api/extended';

function addDays(isoDate: string, delta: number): string {
  const d = new Date(isoDate + 'T12:00:00');
  d.setDate(d.getDate() + delta);
  return d.toISOString().split('T')[0];
}

function todayISO(): string {
  return new Date().toISOString().split('T')[0];
}

/** 0–1 伪随机，按索引稳定，避免每次渲染跳动 */
function stableJitter(index: number, salt: number): number {
  const x = Math.sin(index * 12.9898 + salt * 78.233) * 43758.5453;
  return x - Math.floor(x);
}

export function buildMockNutritionTrends(periodDays: number): NutritionTrendsResponse {
  const n = periodDays === 30 || periodDays === 90 ? periodDays : 7;
  const end = todayISO();
  const trends: NutritionTrend[] = [];
  for (let i = 0; i < n; i++) {
    const date = addDays(end, -(n - 1 - i));
    const j = stableJitter(i, 1);
    const baseCal = 1580 + Math.round(j * 420);
    const protein = Math.round(68 + stableJitter(i, 2) * 32);
    const carbs = Math.round(165 + stableJitter(i, 3) * 55);
    const fat = Math.round(52 + stableJitter(i, 4) * 22);
    const meal_count = 3 + (i % 4 === 0 ? 1 : 0);
    trends.push({ date, total_calories: baseCal, protein, carbs, fat, meal_count });
  }
  return {
    start_date: addDays(end, -(n - 1)),
    end_date: end,
    group_by: 'day',
    data_points: trends.length,
    trends,
  };
}

export function buildMockMacroDistribution(targetDate: string): MacroDistribution {
  const protein_grams = 84;
  const carbs_grams = 198;
  const fat_grams = 56;
  const protein_calories = protein_grams * 4;
  const carbs_calories = carbs_grams * 4;
  const fat_calories = fat_grams * 9;
  const total_calories = protein_calories + carbs_calories + fat_calories;
  return {
    date: targetDate,
    protein_grams,
    protein_calories,
    protein_percentage: (protein_calories / total_calories) * 100,
    carbs_grams,
    carbs_calories,
    carbs_percentage: (carbs_calories / total_calories) * 100,
    fat_grams,
    fat_calories,
    fat_percentage: (fat_calories / total_calories) * 100,
    total_calories,
  };
}

export function buildMockWeightProgress(periodDays: number): WeightProgressResponse {
  const end = todayISO();
  const start = addDays(end, -(periodDays - 1));
  const history: WeightProgressItem[] = [];
  let w = 72.4;
  for (let i = 0; i < periodDays; i++) {
    const date = addDays(start, i);
    w += (stableJitter(i, 5) - 0.55) * 0.28 - 0.04;
    history.push({ date, weight_kg: Math.round(w * 10) / 10 });
  }
  const starting_weight = history[0].weight_kg;
  const current_weight = history[history.length - 1].weight_kg;
  const target_weight = 68;
  const change_kg = Math.round((current_weight - starting_weight) * 10) / 10;
  const trend: WeightProgressResponse['trend'] =
    change_kg < -0.3 ? 'losing' : change_kg > 0.3 ? 'gaining' : 'stable';
  return {
    days_analyzed: periodDays,
    start_date: start,
    end_date: end,
    starting_weight,
    current_weight,
    target_weight,
    change_kg,
    change_percentage: starting_weight ? Math.round((change_kg / starting_weight) * 1000) / 10 : 0,
    trend,
    history,
  };
}

export function buildMockMealPatterns(periodDays: number): MealPatternsResponse {
  const b = Math.max(1, Math.round(periodDays * 0.93));
  const l = Math.max(1, Math.round(periodDays * 0.9));
  const d = Math.max(1, Math.round(periodDays * 0.88));
  const s = Math.max(2, Math.round(periodDays * 1.15));
  return {
    days_analyzed: periodDays,
    total_meals: b + l + d + s,
    patterns: {
      breakfast: {
        meal_type: 'breakfast',
        count: b,
        avg_calories: 385 + stableJitter(periodDays, 6) * 80,
        avg_percentage: 24,
      },
      lunch: {
        meal_type: 'lunch',
        count: l,
        avg_calories: 520 + stableJitter(periodDays, 7) * 90,
        avg_percentage: 32,
      },
      dinner: {
        meal_type: 'dinner',
        count: d,
        avg_calories: 495 + stableJitter(periodDays, 8) * 85,
        avg_percentage: 31,
      },
      snack: {
        meal_type: 'snack',
        count: s,
        avg_calories: 165 + stableJitter(periodDays, 9) * 60,
        avg_percentage: 13,
      },
    },
  };
}
