"""
Analytics Insights Service (Task 10)

AI-powered insights generator for nutrition analytics.
Analyzes backend analytics data and generates personalized insights using Gemini AI.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
import httpx
from decimal import Decimal

from app.config import settings
import google.generativeai as genai

logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=settings.GOOGLE_API_KEY)


# ==========================================
# ANALYTICS INSIGHTS SERVICE
# ==========================================

class AnalyticsInsightsService:
    """
    AI-powered analytics insights generator
    
    Features:
    - Fetches data from backend analytics endpoints
    - Analyzes trends using AI
    - Generates natural language insights
    - Provides personalized recommendations
    """
    
    def __init__(self, backend_url: str = "http://backend:8000"):
        """
        Initialize Analytics Insights Service
        
        Args:
            backend_url: URL of backend API
        """
        self.backend_url = backend_url.rstrip("/")
        self.analytics_base_url = f"{self.backend_url}/api/v1/analytics"
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        logger.info(f"✅ AnalyticsInsightsService initialized (backend: {backend_url})")
    
    
    # ==========================================
    # DATA FETCHING (from Backend)
    # ==========================================
    
    async def fetch_analytics_data(
        self,
        user_token: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Fetch comprehensive analytics data from backend
        
        Args:
            user_token: JWT token for authentication
            days: Number of days to analyze
            
        Returns:
            Combined analytics data
        """
        today = date.today()
        start_date = today - timedelta(days=days)
        
        headers = {"Authorization": f"Bearer {user_token}"}
        
        async with httpx.AsyncClient() as client:
            try:
                # Fetch multiple endpoints in parallel
                tasks = [
                    client.get(
                        f"{self.analytics_base_url}/nutrition-trends",
                        params={
                            "start_date": start_date.isoformat(),
                            "end_date": today.isoformat(),
                            "group_by": "day"
                        },
                        headers=headers
                    ),
                    client.get(
                        f"{self.analytics_base_url}/weight-progress",
                        params={"days": days},
                        headers=headers
                    ),
                    client.get(
                        f"{self.analytics_base_url}/goal-progress",
                        headers=headers
                    ),
                    client.get(
                        f"{self.analytics_base_url}/meal-patterns",
                        params={"days": days},
                        headers=headers
                    ),
                    client.get(
                        f"{self.analytics_base_url}/calorie-comparison",
                        params={
                            "start_date": start_date.isoformat(),
                            "end_date": today.isoformat()
                        },
                        headers=headers
                    )
                ]
                
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Parse responses
                data = {
                    "nutrition_trends": responses[0].json() if not isinstance(responses[0], Exception) else None,
                    "weight_progress": responses[1].json() if not isinstance(responses[1], Exception) else None,
                    "goal_progress": responses[2].json() if not isinstance(responses[2], Exception) else None,
                    "meal_patterns": responses[3].json() if not isinstance(responses[3], Exception) else None,
                    "calorie_comparison": responses[4].json() if not isinstance(responses[4], Exception) else None
                }
                
                logger.info(f"📊 Fetched analytics data for {days} days")
                return data
                
            except Exception as e:
                logger.error(f"❌ Error fetching analytics data: {e}")
                raise
    
    
    # ==========================================
    # INSIGHT GENERATION
    # ==========================================
    
    async def generate_weekly_insights(
        self,
        user_token: str,
        language: str = "vi"
    ) -> Dict[str, Any]:
        """
        Generate comprehensive weekly insights using AI
        
        Args:
            user_token: User JWT token
            language: Output language (vi/en)
            
        Returns:
            {
                "period": "last_7_days",
                "summary": "Natural language summary",
                "highlights": ["Achievement 1", "Achievement 2"],
                "concerns": ["Concern 1", "Concern 2"],
                "recommendations": ["Recommendation 1", "Recommendation 2"],
                "data": {...raw data...}
            }
        """
        # Fetch data
        data = await self.fetch_analytics_data(user_token, days=7)
        
        # Build prompt for Gemini
        prompt = self._build_insights_prompt(data, language)
        
        # Generate insights with Gemini
        try:
            response = await self.model.generate_content_async(prompt)
            insights_text = response.text
            
            # Parse structured insights from AI response
            insights = self._parse_ai_insights(insights_text)
            
            # Add raw data
            insights["data"] = data
            insights["period"] = "last_7_days"
            insights["generated_at"] = datetime.now().isoformat()
            
            logger.info(f"✅ Generated weekly insights ({language})")
            return insights
            
        except Exception as e:
            logger.error(f"❌ Error generating insights: {e}")
            raise
    
    
    async def generate_goal_progress_insights(
        self,
        user_token: str,
        language: str = "vi"
    ) -> Dict[str, Any]:
        """
        Generate insights specifically for goal progress
        
        Args:
            user_token: User JWT token
            language: Output language (vi/en)
            
        Returns:
            Goal-specific insights with recommendations
        """
        headers = {"Authorization": f"Bearer {user_token}"}
        
        async with httpx.AsyncClient() as client:
            try:
                # Fetch goal progress
                response = await client.get(
                    f"{self.analytics_base_url}/goal-progress",
                    headers=headers
                )

                if response.status_code == 404:
                    logger.info("ℹ️ Goal insights requested but user has no active goal")
                    return {
                        "status_message": "Bạn chưa có mục tiêu hoạt động",
                        "progress_assessment": "Hiện chưa có dữ liệu mục tiêu để phân tích tiến độ. Hãy tạo goal trước để nhận đánh giá AI chính xác hơn.",
                        "recommendations": [
                            "Tạo mục tiêu cân nặng hoặc calories trong app backend",
                            "Thiết lập mốc thời gian và chỉ số mục tiêu cụ thể",
                            "Ghi log bữa ăn hằng ngày để hệ thống theo dõi tiến độ"
                        ],
                        "motivation": "Bắt đầu từ một mục tiêu nhỏ để dễ duy trì thói quen.",
                        "data": {},
                        "generated_at": datetime.now().isoformat()
                    }

                if response.status_code != 200:
                    raise ValueError(f"Failed to fetch goal progress: {response.status_code}")
                
                goal_data = response.json()
                
                # Build prompt
                prompt = self._build_goal_insights_prompt(goal_data, language)
                
                # Generate with AI
                ai_response = await self.model.generate_content_async(prompt)
                insights = self._parse_goal_insights(ai_response.text)
                
                insights["data"] = goal_data
                insights["generated_at"] = datetime.now().isoformat()
                
                logger.info(f"✅ Generated goal progress insights ({language})")
                return insights
                
            except Exception as e:
                logger.error(f"❌ Error generating goal insights: {e}")
                raise
    
    
    async def generate_nutrition_trend_insights(
        self,
        user_token: str,
        days: int = 30,
        language: str = "vi"
    ) -> Dict[str, Any]:
        """
        Generate insights about nutrition trends over time
        
        Args:
            user_token: User JWT token
            days: Number of days to analyze
            language: Output language (vi/en)
            
        Returns:
            Trend analysis with patterns and recommendations
        """
        today = date.today()
        start_date = today - timedelta(days=days)
        
        headers = {"Authorization": f"Bearer {user_token}"}
        
        async with httpx.AsyncClient() as client:
            try:
                # Fetch nutrition trends
                response = await client.get(
                    f"{self.analytics_base_url}/nutrition-trends",
                    params={
                        "start_date": start_date.isoformat(),
                        "end_date": today.isoformat(),
                        "group_by": "day"
                    },
                    headers=headers
                )
                
                if response.status_code != 200:
                    raise ValueError(f"Failed to fetch nutrition trends: {response.status_code}")
                
                trends_data = response.json()
                
                # Analyze trends
                analysis = self._analyze_trends(trends_data.get("trends", []))
                
                # Generate AI insights
                prompt = self._build_trend_insights_prompt(trends_data, analysis, language)
                ai_response = await self.model.generate_content_async(prompt)
                
                insights = {
                    "period_days": days,
                    "analysis": analysis,
                    "insights": ai_response.text,
                    "data": trends_data,
                    "generated_at": datetime.now().isoformat()
                }
                
                logger.info(f"✅ Generated nutrition trend insights ({days} days, {language})")
                return insights
                
            except Exception as e:
                logger.error(f"❌ Error generating trend insights: {e}")
                raise
    
    
    # ==========================================
    # PROMPT BUILDING
    # ==========================================
    
    def _build_insights_prompt(self, data: Dict, language: str) -> str:
        """Build prompt for weekly insights generation"""
        
        lang_instructions = {
            "vi": "Trả lời bằng tiếng Việt tự nhiên, thân thiện",
            "en": "Respond in natural, friendly English"
        }
        
        # Extract key metrics
        nutrition = data.get("nutrition_trends", {}).get("trends", [])
        weight = data.get("weight_progress", {})
        goal = data.get("goal_progress", {})
        patterns = data.get("meal_patterns", {})
        comparison = data.get("calorie_comparison", {})
        
        # Calculate averages
        if nutrition:
            avg_calories = sum(d.get("total_calories", 0) for d in nutrition) / len(nutrition)
            avg_protein = sum(d.get("total_protein_g", 0) for d in nutrition) / len(nutrition)
        else:
            avg_calories = avg_protein = 0
        
        prompt = f"""
Bạn là chuyên gia dinh dưỡng AI của NutriAI. Phân tích dữ liệu dinh dưỡng 7 ngày qua và tạo insights.

**Yêu cầu:** {lang_instructions.get(language, lang_instructions["vi"])}

**DỮ LIỆU PHÂN TÍCH (7 ngày qua):**

**1. Nutrition Overview:**
- Trung bình mỗi ngày: {avg_calories:.0f} calories, {avg_protein:.0f}g protein
- Số ngày ghi nhận: {len(nutrition)} ngày
- Số bữa ăn: {patterns.get('total_meals', 0)} bữa

**2. Weight Progress:**
- Cân nặng bắt đầu: {weight.get('starting_weight', 'N/A')} kg
- Cân nặng hiện tại: {weight.get('current_weight', 'N/A')} kg
- Thay đổi: {weight.get('change_kg', 0)} kg
- Xu hướng: {weight.get('trend', 'no_data')}

**3. Goal Progress:**
- Loại mục tiêu: {goal.get('goal_type', 'N/A')}
- Tiến độ: {goal.get('progress_percent', 0):.1f}%
- Mục tiêu calories hàng ngày: {goal.get('daily_calorie_target', 'N/A')} kcal
- Tình trạng: {goal.get('status', 'N/A')}

**4. Calorie Adherence:**
- Số ngày tuân thủ mục tiêu: {comparison.get('days_on_track', 0)}/{comparison.get('days_tracked', 0)}
- Tỷ lệ tuân thủ: {comparison.get('adherence_rate', 0):.1f}%

**5. Meal Patterns:**
{patterns.get('patterns', {})}

**YÊU CẦU TRẢ LỜI (định dạng STRICT):**

Trả lời theo cấu trúc JSON này (KHÔNG thêm markdown, KHÔNG thêm ```json):

{{
  "summary": "Tổng quan ngắn gọn về tuần qua (2-3 câu)",
  "highlights": [
    "Điểm nổi bật tích cực 1",
    "Điểm nổi bật tích cực 2",
    "Điểm nổi bật tích cực 3"
  ],
  "concerns": [
    "Vấn đề cần lưu ý 1",
    "Vấn đề cần lưu ý 2"
  ],
  "recommendations": [
    "Khuyến nghị cụ thể 1 (actionable)",
    "Khuyến nghị cụ thể 2 (actionable)",
    "Khuyến nghị cụ thể 3 (actionable)"
  ]
}}

**LƯU Ý:**
- Phân tích dựa trên dữ liệu thực tế
- Highlights: Thành tựu, điểm mạnh (nếu có tiến bộ)
- Concerns: Vấn đề cần cải thiện (nếu có)
- Recommendations: Cụ thể, thực tế, có thể thực hiện ngay
- Nếu không có data, nói rõ "Chưa có đủ dữ liệu để phân tích"
"""
        
        return prompt
    
    
    def _build_goal_insights_prompt(self, goal_data: Dict, language: str) -> str:
        """Build prompt for goal progress insights"""
        
        lang_instructions = {
            "vi": "Trả lời bằng tiếng Việt",
            "en": "Respond in English"
        }
        
        prompt = f"""
Bạn là chuyên gia dinh dưỡng AI. Phân tích tiến độ mục tiêu của người dùng.

**Yêu cầu:** {lang_instructions.get(language, lang_instructions["vi"])}

**DỮ LIỆU MỤC TIÊU:**
- Loại mục tiêu: {goal_data.get('goal_type')}
- Cân nặng bắt đầu: {goal_data.get('starting_weight')} kg
- Cân nặng hiện tại: {goal_data.get('current_weight')} kg
- Cân nặng mục tiêu: {goal_data.get('target_weight')} kg
- Thay đổi: {goal_data.get('weight_change')} kg
- Còn lại: {goal_data.get('remaining')} kg
- Tiến độ: {goal_data.get('progress_percent')}%
- Số ngày đã trôi qua: {goal_data.get('days_elapsed')}
- Số ngày còn lại: {goal_data.get('days_to_target')}
- Mục tiêu calories: {goal_data.get('daily_calorie_target')} kcal/ngày

**YÊU CẦU TRẢ LỜI (JSON format):**

{{
  "status_message": "Đánh giá tình trạng hiện tại (1 câu)",
  "progress_assessment": "Phân tích chi tiết tiến độ (2-3 câu)",
  "recommendations": [
    "Khuyến nghị 1",
    "Khuyến nghị 2",
    "Khuyến nghị 3"
  ],
  "motivation": "Lời động viên (1 câu)"
}}

Không thêm markdown, không thêm ```json.
"""
        
        return prompt
    
    
    def _build_trend_insights_prompt(
        self,
        trends_data: Dict,
        analysis: Dict,
        language: str
    ) -> str:
        """Build prompt for nutrition trend insights"""
        
        prompt = f"""
Bạn là chuyên gia dinh dưỡng AI. Phân tích xu hướng dinh dưỡng.

**Ngôn ngữ:** {"Tiếng Việt" if language == "vi" else "English"}

**PHÂN TÍCH XU HƯỚNG:**
- Tổng số ngày: {len(trends_data.get('trends', []))}
- Calories trung bình: {analysis.get('avg_calories', 0):.0f} kcal/ngày
- Xu hướng calories: {analysis.get('calorie_trend', 'stable')}
- Protein trung bình: {analysis.get('avg_protein', 0):.0f}g/ngày
- Xu hướng protein: {analysis.get('protein_trend', 'stable')}
- Ngày ghi nhận đầy đủ: {analysis.get('consistent_days', 0)}/{len(trends_data.get('trends', []))}

**YÊU CẦU:**

Tạo phân tích tự nhiên (2-4 đoạn văn) về:
1. Tổng quan xu hướng
2. Các pattern đáng chú ý
3. Đánh giá tính consistency
4. Khuyến nghị cải thiện

Trả lời trực tiếp bằng tự nhiên (KHÔNG dùng JSON, KHÔNG dùng markdown format).
"""
        
        return prompt
    
    
    # ==========================================
    # DATA ANALYSIS
    # ==========================================
    
    def _analyze_trends(self, trends: List[Dict]) -> Dict:
        """
        Analyze nutrition trends to detect patterns
        
        Args:
            trends: List of daily nutrition data
            
        Returns:
            Analysis summary with detected patterns
        """
        if not trends:
            return {
                "avg_calories": 0,
                "avg_protein": 0,
                "avg_carbs": 0,
                "avg_fat": 0,
                "calorie_trend": "no_data",
                "protein_trend": "no_data",
                "consistent_days": 0
            }
        
        # Calculate averages
        calories = [t.get("total_calories", 0) for t in trends]
        proteins = [t.get("total_protein_g", 0) for t in trends]
        carbs = [t.get("total_carbs_g", 0) for t in trends]
        fats = [t.get("total_fat_g", 0) for t in trends]
        
        avg_calories = sum(calories) / len(calories) if calories else 0
        avg_protein = sum(proteins) / len(proteins) if proteins else 0
        avg_carbs = sum(carbs) / len(carbs) if carbs else 0
        avg_fat = sum(fats) / len(fats) if fats else 0
        
        # Detect trends (simple linear trend detection)
        calorie_trend = self._detect_trend(calories)
        protein_trend = self._detect_trend(proteins)
        
        # Count consistent days (days with reasonable calorie intake)
        consistent_days = sum(1 for c in calories if 1000 <= c <= 3000)
        
        return {
            "avg_calories": round(avg_calories, 1),
            "avg_protein": round(avg_protein, 1),
            "avg_carbs": round(avg_carbs, 1),
            "avg_fat": round(avg_fat, 1),
            "calorie_trend": calorie_trend,
            "protein_trend": protein_trend,
            "consistent_days": consistent_days,
            "total_days": len(trends)
        }
    
    
    def _detect_trend(self, values: List[float]) -> str:
        """
        Simple trend detection
        
        Returns: "increasing", "decreasing", "stable"
        """
        if len(values) < 3:
            return "insufficient_data"
        
        # Split into halves and compare averages
        mid = len(values) // 2
        first_half = sum(values[:mid]) / mid
        second_half = sum(values[mid:]) / (len(values) - mid)
        
        change_percent = ((second_half - first_half) / first_half * 100) if first_half > 0 else 0
        
        if change_percent > 10:
            return "increasing"
        elif change_percent < -10:
            return "decreasing"
        else:
            return "stable"
    
    
    # ==========================================
    # RESPONSE PARSING
    # ==========================================
    
    def _parse_ai_insights(self, ai_response: str) -> Dict:
        """
        Parse AI-generated insights from text to structured format
        
        Args:
            ai_response: Raw AI response text
            
        Returns:
            Structured insights dict
        """
        import json
        import re
        
        try:
            # Try to extract JSON from response
            # Remove markdown code blocks if present
            cleaned = re.sub(r'```json\s*', '', ai_response)
            cleaned = re.sub(r'```\s*', '', cleaned)
            cleaned = cleaned.strip()
            
            # Parse JSON
            insights = json.loads(cleaned)
            
            return insights
            
        except json.JSONDecodeError as e:
            logger.warning(f"⚠️  Failed to parse AI insights as JSON: {e}")
            
            # Fallback: Return raw text
            return {
                "summary": ai_response[:200],
                "highlights": [],
                "concerns": [],
                "recommendations": []
            }
    
    
    def _parse_goal_insights(self, ai_response: str) -> Dict:
        """Parse goal-specific AI insights"""
        import json
        import re
        
        try:
            cleaned = re.sub(r'```json\s*', '', ai_response)
            cleaned = re.sub(r'```\s*', '', cleaned)
            cleaned = cleaned.strip()
            
            insights = json.loads(cleaned)
            return insights
            
        except json.JSONDecodeError:
            return {
                "status_message": ai_response[:100],
                "progress_assessment": ai_response,
                "recommendations": [],
                "motivation": "Tiếp tục phấn đấu!"
            }


# ==========================================
# SERVICE FACTORY
# ==========================================

_service_instance: Optional[AnalyticsInsightsService] = None


def get_analytics_insights_service() -> AnalyticsInsightsService:
    """Get singleton instance of Analytics Insights Service"""
    global _service_instance
    
    if _service_instance is None:
        _service_instance = AnalyticsInsightsService()
        logger.info("📊 AnalyticsInsightsService singleton created")
    
    return _service_instance
