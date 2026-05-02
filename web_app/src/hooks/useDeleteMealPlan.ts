import { useMutation, useQueryClient, type UseMutationOptions } from '@tanstack/react-query';
import { mealPlanApi } from '../api/mealPlan';

export function useDeleteMealPlan(
  options?: Omit<UseMutationOptions<void, Error, string>, 'mutationFn'>
) {
  const queryClient = useQueryClient();
  return useMutation({
    ...options,
    mutationFn: (planId: string) => mealPlanApi.deletePlan(planId),
    onSuccess: (data, planId, onMutateResult, context) => {
      queryClient.invalidateQueries({ queryKey: ['mealPlans'] });
      queryClient.removeQueries({ queryKey: ['mealPlan', planId] });
      queryClient.removeQueries({ queryKey: ['mealPlanAnalysis', planId] });
      queryClient.removeQueries({ queryKey: ['shoppingList', planId] });
      options?.onSuccess?.(data, planId, onMutateResult, context);
    },
  });
}
