import { Sparkles, TrendingUp, TrendingDown, Minus, RefreshCw, ChevronRight, Lightbulb, Trophy, Target, CheckCircle2, AlertTriangle, ThumbsUp, Zap } from 'lucide-react';
import { Card, CardBody, Skeleton } from '../ui';
import type { NutritionAdviceResponse, QuickAdviceResponse, ProgressReportResponse } from '../../api/extended';

// ==========================================
// NUTRITION ADVICE PANEL (Main Panel)
// ==========================================

interface NutritionAdvicePanelProps {
  advice: NutritionAdviceResponse | null;
  isLoading: boolean;
  onRefresh?: () => void;
  period: 'day' | 'week' | 'month';
}

export function NutritionAdvicePanel({ advice, isLoading, onRefresh, period }: NutritionAdvicePanelProps) {
  const periodLabel = period === 'day' ? 'hôm nay' : period === 'week' ? 'tuần' : 'tháng';

  if (isLoading) {
    return (
      <Card className="border-2 border-primary/20 bg-gradient-to-br from-primary/5 via-purple-50/30 to-blue-50/20">
        <CardBody>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-primary animate-pulse" />
              <span className="font-bold text-lg text-gray-900">Lời khuyên AI</span>
            </div>
            <Skeleton className="h-8 w-20" />
          </div>
          <Skeleton className="h-20 w-full mb-4" />
          <div className="space-y-3">
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
          </div>
        </CardBody>
      </Card>
    );
  }

  if (!advice) {
    return (
      <Card className="border border-gray-200 bg-gray-50">
        <CardBody className="text-center py-8">
          <Sparkles className="w-10 h-10 text-gray-400 mx-auto mb-3" />
          <p className="text-gray-500 mb-2">Chưa có lời khuyên</p>
          <p className="text-sm text-gray-400">Nhấn nút "Nhận lời khuyên AI" để bắt đầu phân tích</p>
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="mt-4 px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary/90 transition-colors"
            >
              Thử lại
            </button>
          )}
        </CardBody>
      </Card>
    );
  }

  return (
    <Card className="border-2 border-primary/20 bg-gradient-to-br from-primary/5 via-purple-50/30 to-blue-50/20 overflow-hidden">
      <CardBody>
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-primary" />
            <span className="font-bold text-lg text-gray-900">Lời khuyên AI</span>
            <span className="text-xs px-2 py-0.5 bg-primary/10 text-primary rounded-full">
              Phân tích {periodLabel}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-400">
              {new Date(advice.generated_at).toLocaleString('vi-VN')}
            </span>
            {onRefresh && (
              <button
                onClick={onRefresh}
                className="p-1.5 hover:bg-white/60 rounded-lg transition-colors"
                title="Làm mới"
              >
                <RefreshCw className="w-4 h-4 text-gray-500" />
              </button>
            )}
          </div>
        </div>

        {/* Summary */}
        <div className="p-4 bg-white/70 rounded-xl border border-primary/10 mb-4">
          <p className="text-gray-700 leading-relaxed">{advice.summary}</p>
        </div>

        {/* Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Highlights - Điểm sáng */}
          {advice.highlights && advice.highlights.length > 0 && (
            <div className="p-4 bg-green-50 rounded-xl border border-green-200">
              <div className="flex items-center gap-2 mb-3">
                <CheckCircle2 className="w-4 h-4 text-green-600" />
                <span className="font-semibold text-green-800 text-sm">Điểm sáng</span>
              </div>
              <ul className="space-y-2">
                {advice.highlights.map((h, i) => (
                  <li key={i} className="text-sm text-green-700 flex items-start gap-2">
                    <span className="text-green-500 mt-0.5">✓</span>
                    <span>{h}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Concerns - Cần cải thiện */}
          {advice.concerns && advice.concerns.length > 0 && (
            <div className="p-4 bg-amber-50 rounded-xl border border-amber-200">
              <div className="flex items-center gap-2 mb-3">
                <AlertTriangle className="w-4 h-4 text-amber-600" />
                <span className="font-semibold text-amber-800 text-sm">Cần cải thiện</span>
              </div>
              <ul className="space-y-2">
                {advice.concerns.map((c, i) => (
                  <li key={i} className="text-sm text-amber-700 flex items-start gap-2">
                    <span className="text-amber-500 mt-0.5">!</span>
                    <span>{c}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Recommendations - Lời khuyên */}
        {advice.recommendations && advice.recommendations.length > 0 && (
          <div className="mt-4 p-4 bg-blue-50 rounded-xl border border-blue-200">
            <div className="flex items-center gap-2 mb-3">
              <Lightbulb className="w-4 h-4 text-blue-600" />
              <span className="font-semibold text-blue-800 text-sm">Lời khuyên cụ thể</span>
            </div>
            <ul className="space-y-2">
              {advice.recommendations.map((r, i) => (
                <li key={i} className="text-sm text-blue-700 flex items-start gap-2">
                  <ChevronRight className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
                  <span>{r}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Motivational Tip */}
        {advice.motivational_tip && (
          <div className="mt-4 p-4 bg-gradient-to-r from-green-100 to-emerald-50 rounded-xl border border-green-300">
            <div className="flex items-center gap-2">
              <ThumbsUp className="w-4 h-4 text-green-600" />
              <span className="text-sm text-green-800 font-medium italic">
                {advice.motivational_tip}
              </span>
            </div>
          </div>
        )}

        {/* Footer info */}
        <div className="mt-4 pt-3 border-t border-gray-200/50 flex items-center justify-between text-xs text-gray-400">
          <span>Phân tích {advice.days_analyzed} ngày dữ liệu</span>
          <span>AI-powered by NutriAI</span>
        </div>
      </CardBody>
    </Card>
  );
}

// ==========================================
// QUICK ADVICE CARD (Compact)
// ==========================================

interface QuickAdviceCardProps {
  advice: QuickAdviceResponse | null;
  isLoading: boolean;
}

export function QuickAdviceCard({ advice, isLoading }: QuickAdviceCardProps) {
  if (isLoading) {
    return (
      <Card className="bg-gradient-to-r from-orange-50 to-yellow-50 border-orange-200">
        <CardBody>
          <div className="flex items-center gap-2 mb-2">
            <Skeleton className="h-5 w-5 rounded-full" />
            <Skeleton className="h-5 w-24" />
          </div>
          <Skeleton className="h-8 w-full mb-2" />
          <Skeleton className="h-4 w-3/4" />
        </CardBody>
      </Card>
    );
  }

  if (!advice) return null;

  return (
    <Card className="bg-gradient-to-r from-orange-50 to-yellow-50 border-orange-200">
      <CardBody>
        <div className="flex items-center gap-2 mb-3">
          <div className="p-1.5 bg-orange-100 rounded-lg">
            <Lightbulb className="w-4 h-4 text-orange-600" />
          </div>
          <span className="font-semibold text-orange-800 text-sm">Gợi ý nhanh</span>
        </div>

        <p className="text-lg font-bold text-gray-900 mb-2">{advice.quick_tip}</p>

        <div className="space-y-2">
          <div className="flex items-start gap-2">
            <ChevronRight className="w-4 h-4 text-orange-500 mt-0.5" />
            <div>
              <span className="text-sm font-medium text-gray-700">Hành động: </span>
              <span className="text-sm text-gray-600">{advice.action}</span>
            </div>
          </div>
          {advice.why && (
            <div className="flex items-start gap-2">
              <span className="text-orange-400 mt-0.5">💡</span>
              <span className="text-sm text-gray-500 italic">{advice.why}</span>
            </div>
          )}
        </div>
      </CardBody>
    </Card>
  );
}

// ==========================================
// PROGRESS REPORT CARD
// ==========================================

interface ProgressReportCardProps {
  report: ProgressReportResponse | null;
  isLoading: boolean;
  onRefresh?: () => void;
}

export function ProgressReportCard({ report, isLoading, onRefresh }: ProgressReportCardProps) {
  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600 bg-green-100';
    if (score >= 60) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getTrendIcon = (onTrack: boolean | undefined) => {
    if (onTrack === undefined) return <Minus className="w-4 h-4" />;
    return onTrack ? (
      <TrendingUp className="w-4 h-4" />
    ) : (
      <TrendingDown className="w-4 h-4" />
    );
  };

  const getTrendColor = (onTrack: boolean | undefined) => {
    if (onTrack === undefined) return 'text-gray-600 bg-gray-100';
    return onTrack ? 'text-green-600 bg-green-100' : 'text-red-600 bg-red-100';
  };

  if (isLoading) {
    return (
      <Card>
        <CardBody>
          <Skeleton className="h-32 w-full" />
        </CardBody>
      </Card>
    );
  }

  if (!report) return null;

  return (
    <Card className="border-2 border-purple-200 bg-gradient-to-br from-purple-50/50 to-pink-50/30">
      <CardBody>
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Trophy className="w-5 h-5 text-purple-600" />
            <span className="font-bold text-lg text-gray-900">Báo cáo tiến độ</span>
            <span className="text-xs px-2 py-0.5 bg-purple-100 text-purple-700 rounded-full capitalize">
              {report.period === 'week' ? 'Tuần này' : 'Tháng này'}
            </span>
          </div>
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="p-1.5 hover:bg-white/60 rounded-lg transition-colors"
            >
              <RefreshCw className="w-4 h-4 text-gray-500" />
            </button>
          )}
        </div>

        {/* Overall Score */}
        <div className="flex items-center gap-4 mb-4 p-4 bg-white/70 rounded-xl border border-purple-100">
          <div className={`p-3 rounded-xl ${getScoreColor(report.overall_score)}`}>
            <span className="text-2xl font-bold">{report.overall_score}</span>
          </div>
          <div>
            <p className="text-sm text-gray-500">Điểm tổng thể</p>
            <p className="text-gray-700">{report.summary}</p>
          </div>
        </div>

        {/* Weight Analysis */}
        {report.weight_analysis && (
          <div className="mb-4 p-4 bg-gray-50 rounded-xl">
            <div className="flex items-center gap-2 mb-2">
              <Target className="w-4 h-4 text-blue-600" />
              <span className="font-semibold text-gray-800 text-sm">Phân tích cân nặng</span>
              <div className={`ml-auto p-1.5 rounded-lg ${getTrendColor(report.weight_analysis.on_track)}`}>
                {getTrendIcon(report.weight_analysis.on_track)}
              </div>
            </div>
            <p className="text-sm text-gray-600 mb-1">{report.weight_analysis.progress}</p>
            {report.weight_analysis.reasoning && (
              <p className="text-xs text-gray-500 italic">{report.weight_analysis.reasoning}</p>
            )}
          </div>
        )}

        {/* Achievements */}
        {report.achievements && report.achievements.length > 0 && (
          <div className="mb-4">
            <div className="flex items-center gap-2 mb-2">
              <Trophy className="w-4 h-4 text-yellow-500" />
              <span className="font-semibold text-gray-800 text-sm">Thành tựu</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {report.achievements.map((a, i) => (
                <span key={i} className="px-3 py-1 bg-yellow-100 text-yellow-800 text-xs rounded-full">
                  🏆 {a}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Areas for Improvement */}
        {report.areas_for_improvement && report.areas_for_improvement.length > 0 && (
          <div className="mb-4">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="w-4 h-4 text-amber-500" />
              <span className="font-semibold text-gray-800 text-sm">Cần cải thiện</span>
            </div>
            <ul className="space-y-1">
              {report.areas_for_improvement.map((area, i) => (
                <li key={i} className="text-sm text-amber-700 flex items-start gap-2">
                  <span className="text-amber-400">•</span>
                  {area}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Next Week Tips */}
        {report.next_week_tips && report.next_week_tips.length > 0 && (
          <div className="mb-4 p-4 bg-blue-50 rounded-xl border border-blue-100">
            <div className="flex items-center gap-2 mb-2">
              <Lightbulb className="w-4 h-4 text-blue-600" />
              <span className="font-semibold text-blue-800 text-sm">Tips cho thời gian tới</span>
            </div>
            <ul className="space-y-1">
              {report.next_week_tips.map((tip, i) => (
                <li key={i} className="text-sm text-blue-700 flex items-start gap-2">
                  <ChevronRight className="w-4 h-4 text-blue-400 mt-0.5" />
                  {tip}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Motivation */}
        {report.motivation && (
          <div className="p-4 bg-gradient-to-r from-green-100 to-emerald-50 rounded-xl border border-green-200">
            <p className="text-sm text-green-800 font-medium text-center">
              🌟 {report.motivation}
            </p>
          </div>
        )}
      </CardBody>
    </Card>
  );
}

// ==========================================
// AI ADVICE FULL PAGE (For separate tab)
// ==========================================

interface AIAdviceFullPageProps {
  advice: NutritionAdviceResponse | null;
  quickAdvice: QuickAdviceResponse | null;
  progressReport: ProgressReportResponse | null;
  isLoadingAdvice: boolean;
  isLoadingQuick: boolean;
  isLoadingProgress: boolean;
  selectedPeriod: 'day' | 'week' | 'month';
  onPeriodChange: (period: 'day' | 'week' | 'month') => void;
  onRefresh: () => void;
  onRequestAdvice: () => void;
  hasRequestedAdvice: boolean;
}

export function AIAdviceFullPage({
  advice,
  quickAdvice,
  progressReport,
  isLoadingAdvice,
  isLoadingQuick,
  isLoadingProgress,
  selectedPeriod,
  onPeriodChange,
  onRefresh,
  onRequestAdvice,
  hasRequestedAdvice,
}: AIAdviceFullPageProps) {
  // Show placeholder UI when user hasn't requested advice yet
  if (!hasRequestedAdvice) {
    return (
      <div className="text-center py-16 px-4">
        <div className="w-24 h-24 mx-auto mb-6 bg-gradient-to-br from-primary/10 to-purple-100 rounded-full flex items-center justify-center">
          <Sparkles className="w-12 h-12 text-primary" />
        </div>
        <h3 className="text-2xl font-bold text-gray-900 mb-3">
          Nhận lời khuyên dinh dưỡng từ AI
        </h3>
        <p className="text-gray-500 mb-8 max-w-md mx-auto leading-relaxed">
          AI sẽ phân tích dữ liệu dinh dưỡng của bạn và đưa ra
          lời khuyên cá nhân hóa dựa trên mục tiêu sức khỏe.
        </p>
        <button
          onClick={onRequestAdvice}
          className="px-8 py-4 bg-primary text-white rounded-xl font-semibold
                     hover:bg-primary/90 transition-all duration-200
                     shadow-lg shadow-primary/25 hover:shadow-xl hover:shadow-primary/30
                     flex items-center gap-3 mx-auto"
        >
          <Zap className="w-5 h-5" />
          Nhận lời khuyên AI
        </button>
        <div className="flex items-center justify-center gap-6 mt-8 text-sm text-gray-400">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-green-400" />
            <span>Phân tích cá nhân hóa</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-blue-400" />
            <span>Lời khuyên thực tế</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Period Selector */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-gray-900">Lời khuyên từ AI</h2>
        <div className="flex gap-2">
          {(['day', 'week', 'month'] as const).map(period => (
            <button
              key={period}
              onClick={() => onPeriodChange(period)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                selectedPeriod === period
                  ? 'bg-primary text-white'
                  : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'
              }`}
            >
              {period === 'day' ? 'Hôm nay' : period === 'week' ? '7 ngày' : '30 ngày'}
            </button>
          ))}
        </div>
      </div>

      {/* Quick Advice */}
      <QuickAdviceCard advice={quickAdvice} isLoading={isLoadingQuick} />

      {/* Main Advice Panel */}
      <NutritionAdvicePanel
        advice={advice}
        isLoading={isLoadingAdvice}
        onRefresh={onRefresh}
        period={selectedPeriod}
      />

      {/* Progress Report */}
      <ProgressReportCard
        report={progressReport}
        isLoading={isLoadingProgress}
        onRefresh={onRefresh}
      />
    </div>
  );
}
