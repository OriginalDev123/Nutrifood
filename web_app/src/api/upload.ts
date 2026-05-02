import { apiClient } from './client';
import type { UploadResponse, BulkUploadResponse } from './extended';

// File upload helper
const createFormData = (file: File): FormData => {
  const formData = new FormData();
  formData.append('file', file);
  return formData;
};

export const uploadApi = {
  // Upload food image (for meal logging, AI recognition, recipe images)
  uploadFoodImage: async (file: File): Promise<UploadResponse> => {
    const response = await apiClient.post('/uploads/food-image', createFormData(file), {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // Upload profile picture (automatically updates user profile)
  uploadProfileImage: async (file: File): Promise<UploadResponse & { message: string }> => {
    const response = await apiClient.post('/uploads/profile-image', createFormData(file), {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // Upload recipe image
  uploadRecipeImage: async (file: File): Promise<UploadResponse> => {
    const response = await apiClient.post('/uploads/recipe-image', createFormData(file), {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // Upload multiple images at once (max 10)
  bulkUpload: async (
    files: File[]
  ): Promise<BulkUploadResponse> => {
    if (files.length > 10) {
      throw new Error('Maximum 10 files allowed per request');
    }
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));
    const response = await apiClient.post('/uploads/bulk-upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // Delete uploaded image
  deleteImage: async (filename: string): Promise<{ message: string; filename: string }> => {
    const response = await apiClient.delete(`/uploads/image/${filename}`);
    return response.data;
  },

  // Get upload statistics
  getStats: async (): Promise<{
    foods: number;
    profiles: number;
    recipes: number;
    bulk: number;
    total_files: number;
    total_size_mb: number;
  }> => {
    const response = await apiClient.get('/uploads/stats');
    return response.data;
  },
};