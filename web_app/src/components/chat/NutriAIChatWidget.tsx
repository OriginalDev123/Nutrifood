import axios from 'axios';
import { useState, useRef, useEffect } from 'react';
import { X, Send, Bot, Sparkles, ChevronUp, Minus, Trash2 } from 'lucide-react';
import { useToast } from '../../components/ui/Toast';
import { useAuthStore } from '../../stores/authStore';
import { chatApi } from '../../api/chat';
import { goalApi } from '../../api/goal';
import { foodApi } from '../../api/food';
import type { ChatSourceDocument, DailySummary, UserGoal } from '../../api/types';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: ChatSourceDocument[];
  processingTimeMs?: number;
}

interface PersistedChatSession {
  sessionId?: string;
  messages: Array<Omit<ChatMessage, 'timestamp'> & { timestamp: string }>;
  savedAt: number;
}

const CHAT_SESSION_TTL_MS = 24 * 60 * 60 * 1000;

const QUICK_QUESTIONS = [
  'Tính calories hôm nay',
  'Gợi ý bữa ăn sáng',
  'Cách giảm cân hiệu quả',
  'Thực phẩm giàu protein',
];
export default function NutriAIChatWidget() {
  const { user } = useAuthStore();
  const toast = useToast();
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [activeGoal, setActiveGoal] = useState<UserGoal | null>(null);
  const [todaySummary, setTodaySummary] = useState<DailySummary | null>(null);
  const [showQuickSuggestions, setShowQuickSuggestions] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const storageKey = user?.user_id ? `chat_session_${user.user_id}` : null;

  const userName = user?.full_name?.split(' ').pop() || user?.email?.split('@')[0] || 'bạn';

  // Restore chat session from localStorage
  useEffect(() => {
    if (!storageKey) return;

    try {
      const raw = localStorage.getItem(storageKey);
      if (!raw) return;

      const parsed = JSON.parse(raw) as PersistedChatSession;
      if (!parsed || typeof parsed !== 'object') return;
      if (!parsed.savedAt || Date.now() - parsed.savedAt > CHAT_SESSION_TTL_MS) {
        localStorage.removeItem(storageKey);
        return;
      }

      if (parsed.sessionId) {
        setSessionId(parsed.sessionId);
      }

      if (Array.isArray(parsed.messages) && parsed.messages.length > 0) {
        setMessages(
          parsed.messages.map((msg) => ({
            ...msg,
            timestamp: new Date(msg.timestamp),
          }))
        );
      }
    } catch {
      localStorage.removeItem(storageKey);
    }
  }, [storageKey]);

  // Persist chat session
  useEffect(() => {
    if (!storageKey || messages.length === 0) return;

    const payload: PersistedChatSession = {
      sessionId,
      savedAt: Date.now(),
      messages: messages.map((msg) => ({
        ...msg,
        timestamp: msg.timestamp.toISOString(),
      })),
    };

    localStorage.setItem(storageKey, JSON.stringify(payload));
  }, [messages, sessionId, storageKey]);

  // Initialize with welcome message
  useEffect(() => {
    if (isOpen && messages.length === 0) {
      setMessages([
        {
          id: 'welcome',
          role: 'assistant',
          content: `Xin chào ${userName}! 👋\n\nTôi là NutriAI Assistant, sẵn sàng giúp bạn:\n• Tính toán calories và dinh dưỡng\n• Gợi ý thực đơn lành mạnh\n• Tư vấn chế độ ăn phù hợp\n• Trả lời thắc mắc về sức khỏe\n\nBạn cần tôi hỗ trợ gì hôm nay?`,
          timestamp: new Date(),
        },
      ]);
    }
  }, [isOpen, userName, messages.length]);

  // Load contextual data for smarter responses
  useEffect(() => {
    if (!isOpen || !user?.user_id) return;

    const today = new Date().toISOString().slice(0, 10);

    Promise.all([
      goalApi.getActive().catch(() => null),
      foodApi.getDailySummary(today).catch(() => null),
    ]).then(([goal, summary]) => {
      setActiveGoal(goal);
      setTodaySummary(summary);
    });
  }, [isOpen, user?.user_id]);

  // Auto-scroll to bottom when new message arrives
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const handleSendMessage = async (message?: string) => {
    const text = (message || inputValue).trim();
    if (!text || isTyping) return;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);
    setShowQuickSuggestions(false);

    try {
      const response = await chatApi.ask({
        question: text,
        session_id: sessionId,
        user_context: {
          user_id: user?.user_id,
          current_weight: activeGoal?.current_weight_kg,
          goal_type: activeGoal?.goal_type,
          daily_target: activeGoal?.daily_calorie_target ?? undefined,
          consumed_today: todaySummary?.total_calories,
        },
      });

      setSessionId(response.session_id);

      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.answer,
        timestamp: new Date(),
        sources: response.sources,
        processingTimeMs: response.processing_time_ms,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Chat request failed:', error);

      let errorMessage = 'Không thể kết nối AI chatbot. Vui lòng thử lại.';
      if (axios.isAxiosError(error)) {
        errorMessage = error.response?.data?.detail || errorMessage;
      }

      toast.error(errorMessage);

      const assistantMessage: ChatMessage = {
        id: `assistant-error-${Date.now()}`,
        role: 'assistant',
        content: 'Xin lỗi, hiện tại mình đang gặp sự cố kết nối. Anh thử lại sau ít phút nhé.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleQuickQuestion = (question: string) => {
    handleSendMessage(question);
  };

  const handleClearConversation = () => {
    setMessages([]);
    setSessionId(undefined);
    if (storageKey) {
      localStorage.removeItem(storageKey);
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 w-14 h-14 bg-primary hover:bg-primary/90 text-white rounded-full shadow-lg flex items-center justify-center transition-all duration-300 hover:scale-105 z-50"
        aria-label="Mở chat hỗ trợ"
      >
        <Sparkles className="w-6 h-6" />
        <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full animate-pulse" />
      </button>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 z-50 flex w-[min(22rem,calc(100vw-3rem))] sm:w-80 max-w-[calc(100vw-3rem)] h-[min(28rem,calc(100vh-5rem))] max-h-[calc(100vh-5rem)] flex-col overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-2xl">
      {/* Header */}
      <div className="shrink-0 bg-primary px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
            <Bot className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="text-white font-semibold text-sm">Hỗ trợ NutriAI</h3>
            <p className="text-white/70 text-xs">Trực tuyến</p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={handleClearConversation}
            className="p-1.5 text-white/80 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
            aria-label="Xoá cuộc trò chuyện"
          >
            <Trash2 className="w-4 h-4" />
          </button>
          <button
            onClick={() => setIsMinimized(!isMinimized)}
            className="p-1.5 text-white/80 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
            aria-label={isMinimized ? 'Phóng to' : 'Thu nhỏ'}
          >
            {isMinimized ? <ChevronUp className="w-4 h-4" /> : <Minus className="w-4 h-4" />}
          </button>
          <button
            onClick={() => setIsOpen(false)}
            className="p-1.5 text-white/80 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
            aria-label="Đóng chat"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Chat Content */}
      {!isMinimized && (
        <>
          {/* Messages — min-h-0 让 flex 子项可被压缩，长回复只在区内滚动 */}
          <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain p-4 space-y-4 bg-gray-50">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-2.5 ${
                    msg.role === 'user'
                      ? 'bg-primary text-white rounded-br-md'
                      : 'bg-white text-gray-800 rounded-bl-md shadow-sm border border-gray-100'
                  }`}
                >
                  <p className="text-sm whitespace-pre-line break-words [overflow-wrap:anywhere]">{msg.content}</p>

                  {msg.role === 'assistant' && msg.sources?.length ? (
                    <div className="mt-2 border-t border-gray-100 pt-2">
                      <p className="text-xs text-gray-500">Nguồn tham khảo:</p>
                      <ul className="mt-1 space-y-1">
                        {msg.sources.slice(0, 3).map((source) => (
                          <li key={`${msg.id}-${source.title}`} className="text-xs text-gray-500">
                            • {source.title} ({Math.round(source.relevance_score * 100)}%)
                          </li>
                        ))}
                      </ul>
                    </div>
                  ) : null}

                  <p
                    className={`text-xs mt-1 ${
                      msg.role === 'user' ? 'text-white/60' : 'text-gray-400'
                    }`}
                  >
                    {msg.timestamp.toLocaleTimeString('vi-VN', {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                    {msg.role === 'assistant' && msg.processingTimeMs ? ` · ${msg.processingTimeMs}ms` : ''}
                  </p>
                </div>
              </div>
            ))}

            {/* Typing indicator */}
            {isTyping && (
              <div className="flex justify-start">
                <div className="bg-white text-gray-800 rounded-2xl rounded-bl-md shadow-sm border border-gray-100 px-4 py-3">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Quick Questions */}
          <div className="shrink-0 px-4 py-2 bg-gray-50 border-t border-gray-100">
            {showQuickSuggestions ? (
              <>
                <div className="flex items-center justify-between mb-2">
                  <p className="text-xs text-gray-500">Gợi ý nhanh:</p>
                  <button
                    onClick={() => setShowQuickSuggestions(false)}
                    className="text-xs text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    Ẩn gợi ý
                  </button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {QUICK_QUESTIONS.map((question) => (
                    <button
                      key={question}
                      onClick={() => handleQuickQuestion(question)}
                      className="text-xs px-3 py-1.5 bg-primary/10 text-primary rounded-full hover:bg-primary/20 transition-colors"
                    >
                      {question}
                    </button>
                  ))}
                </div>
              </>
            ) : (
              <button
                onClick={() => setShowQuickSuggestions(true)}
                className="w-full text-xs text-gray-500 hover:text-primary transition-colors py-1"
              >
                Hiện gợi ý nhanh
              </button>
            )}
          </div>

          {/* Input */}
          <div className="shrink-0 p-3 bg-white border-t border-gray-100">
            <div className="flex gap-2">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                placeholder="Nhập câu hỏi của bạn..."
                className="flex-1 px-4 py-2.5 text-sm border border-gray-200 rounded-full bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-colors"
                disabled={isTyping}
              />
              <button
                onClick={() => handleSendMessage()}
                disabled={!inputValue.trim() || isTyping}
                className="p-2.5 bg-primary text-white rounded-full hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                aria-label="Gửi"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Footer */}
          <div className="shrink-0 px-4 py-2 bg-gray-50 border-t border-gray-100 text-center">
            <p className="text-xs text-gray-400">Được hỗ trợ bởi AI</p>
          </div>
        </>
      )}
    </div>
  );
}
