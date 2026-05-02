import type { ChatAskRequest, ChatAskResponse } from './types';
import { aiServiceClient } from './client';

export const chatApi = {
  ask: async (data: ChatAskRequest): Promise<ChatAskResponse> => {
    const response = await aiServiceClient.post('/chat/ask', data);
    return response.data;
  },
};
