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
import json
import re

from google import genai
from google.genai import types

from app.config import settings

logger = logging.getLogger(__name__)

# Configure Gemini client
client = genai.Client(api_key=settings.GOOGLE_API_KEY)


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
        self.model_name = settings.GEMINI_MODEL
        logger.info(f"✅ AnalyticsInsightsService initialized (backend: {backend_url})")

    async def _generate_content(self, prompt: str, max_tokens: int = 2048, temperature: float = 0.3) -> str:
        """Generate content using the new SDK"""
        response = client.models.generate_content(
            model=self.model_name,
            contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
            config=types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                top_p=0.95,
                top_k=40
            )
        )
        return response.text
    
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
        
        async with httpx.AsyncClient() as http_client:
            try:
                tasks = [
                    http_client.get(
                        f"{self.analytics_base_url}/nutrition-trends",
                        params={
                            "start_date": start_date.isoformat(),
                            "end_date": today.isoformat(),
                            "group_by": "day"
                        },
                        headers=headers
                    ),
                    http_client.get(
                        f"{self.analytics_base_url}/weight-progress",
                        params={"days": days},
                        headers=headers
                    ),
                    http_client.get(
                        f"{self.analytics_base_url}/goal-progress",
                        headers=headers
                    ),
                    http_client.get(
                        f"{self.analytics_base_url}/meal-patterns",
                        params={"days": days},
                        headers=headers
                    ),
                    http_client.get(
                        f"{self.analytics_base_url}/calorie-comparison",
                        params={
                            "start_date": start_date.isoformat(),
                            "end_date": today.isoformat()
                        },
                        headers=headers
                    )
                ]
                
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                
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
        """Generate comprehensive weekly insights using AI"""
        data = await self.fetch_analytics_data(user_token, days=7)
        prompt = self._build_insights_prompt(data, language)
        
        try:
            insights_text = await self._generate_content(prompt)
            insights = self._parse_ai_insights(insights_text)
            
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
        """Generate insights specifically for goal progress"""
        headers = {"Authorization": f"Bearer {user_token}"}
        
        async with httpx.AsyncClient() as http_client:
            try:
                response = await http_client.get(
                    f"{self.analytics_base_url}/goal-progress",
                    headers=headers
                )

                if response.status_code == 404:
                    return {
                        "status_message": "Bạn chưa có mục tiêu hoạt động",
                        "progress_assessment": "Hiện chưa có dữ liệu mục tiêu để phân tích tiến độ.",
                        "recommendations": ["Tạo mục tiêu cân nặng hoặc calories"],
                        "motivation": "Bắt đầu từ một mục tiêu nhỏ.",
                        "data": {},
                        "generated_at": datetime.now().isoformat()
                    }

                if response.status_code != 200:
                    raise ValueError(f"Failed to fetch goal progress: {response.status_code}")
                
                goal_data = response.json()
                prompt = self._build_goal_insights_prompt(goal_data, language)
                ai_response_text = await self._generate_content(prompt)
                insights = self._parse_goal_insights(ai_response_text)
                
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
        """Generate insights about nutrition trends over time"""
        today = date.today()
        start_date = today - timedelta(days=days)
        headers = {"Authorization": f"Bearer {user_token}"}
        
        async with httpx.AsyncClient() as http_client:
            try:
                response = await http_client.get(
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
                analysis = self._analyze_trends(trends_data.get("trends", []))
                prompt = self._build_trend_insights_prompt(trends_data, analysis, language)
                ai_response_text = await self._generate_content(prompt)
                
                return {
                    "period_days": days,
                    "analysis": analysis,
                    "insights": ai_response_text,
                    "data": trends_data,
                    "generated_at": datetime.now().isoformat()
                }
                
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
        
        nutrition = data.get("nutrition_trends", {}).get("trends", [])
        weight = data.get("weight_progress", {})
        goal = data.get("goal_progress", {})
        patterns = data.get("meal_patterns", {})
        comparison = data.get("calorie_comparison", {})
        
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

**3. Goal Progress:**
- Loại mục tiêu: {goal.get('goal_type', 'N/A')}
- Tiến độ: {goal.get('progress_percent', 0):.1f}%
- Mục tiêu calories hàng ngày: {goal.get('daily_calorie_target', 'N/A')} kcal

**YÊU CẦU TRẢ LỜI (định dạng STRICT JSON):**

{{
  "summary": "Tổng quan ngắn gọn về tuần qua (2-3 câu)",
  "highlights": ["Điểm nổi bật tích cực 1", "Điểm nổi bật tích cực 2"],
  "concerns": ["Vấn đề cần lưu ý 1"],
  "recommendations": ["Khuyến nghị cụ thể 1", "Khuyến nghị cụ thể 2"]
}}

Không thêm markdown, không thêm ```json.
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
- Tiến độ: {goal_data.get('progress_percent')}%
- Mục tiêu calories: {goal_data.get('daily_calorie_target')} kcal/ngày

**YÊU CẦU TRẢ LỜI (JSON format):**

{{
  "status_message": "Đánh giá tình trạng hiện tại (1 câu)",
  "progress_assessment": "Phân tích chi tiết tiến độ (2-3 câu)",
  "recommendations": ["Khuyến nghị 1", "Khuyến nghị 2"],
  "motivation": "Lời động viên (1 câu)"
}}

Không thêm markdown, không thêm ```json.
"""
        return prompt
    
    def _build_trend_insights_prompt(self, trends_data: Dict, analysis: Dict, language: str) -> str:
        """Build prompt for nutrition trend insights"""
        prompt = f"""
Bạn là chuyên gia dinh dưỡng AI. Phân tích xu hướng dinh dưỡng.

**Ngôn ngữ:** {"Tiếng Việt" if language == "vi" else "English"}

**PHÂN TÍCH XU HƯỚNG:**
- Tổng số ngày: {len(trends_data.get('trends', []))}
- Calories trung bình: {analysis.get('avg_calories', 0):.0f} kcal/ngày
- Protein trung bình: {analysis.get('avg_protein', 0):.0f}g/ngày

**YÊU CẦU:**

Tạo phân tích tự nhiên (2-4 đoạn văn) về:
1. Tổng quan xu hướng
2. Các pattern đáng chú ý
3. Khuyến nghị cải thiện

Trả lời trực tiếp bằng tự nhiên (KHÔNG dùng JSON, KHÔNG dùng markdown format).
"""
        return prompt
    
    # ==========================================
    # DATA ANALYSIS
    # ==========================================
    
    def _analyze_trends(self, trends: List[Dict]) -> Dict:
        """Analyze nutrition trends to detect patterns"""
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
        
        calories = [t.get("total_calories", 0) for t in trends]
        proteins = [t.get("total_protein_g", 0) for t in trends]
        carbs = [t.get("total_carbs_g", 0) for t in trends]
        fats = [t.get("total_fat_g", 0) for t in trends]
        
        avg_calories = sum(calories) / len(calories) if calories else 0
        avg_protein = sum(proteins) / len(proteins) if proteins else 0
        avg_carbs = sum(carbs) / len(carbs) if carbs else 0
        avg_fat = sum(fats) / len(fats) if fats else 0
        
        calorie_trend = self._detect_trend(calories)
        protein_trend = self._detect_trend(proteins)
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
        """Simple trend detection"""
        if len(values) < 3:
            return "insufficient_data"
        
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
        """Parse AI-generated insights from text to structured format"""
        try:
            cleaned = re.sub(r'```json\s*', '', ai_response)
            cleaned = re.sub(r'```\s*', '', cleaned)
            cleaned = cleaned.strip()
            insights = json.loads(cleaned)
            return insights
            
        except json.JSONDecodeError as e:
            logger.warning(f"⚠️  Failed to parse AI insights as JSON: {e}")
            return {
                "summary": ai_response[:200],
                "highlights": [],
                "concerns": [],
                "recommendations": []
            }
    
    def _parse_goal_insights(self, ai_response: str) -> Dict:
        """Parse goal-specific AI insights"""
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


_service_instance: Optional[AnalyticsInsightsService] = None


def get_analytics_insights_service() -> AnalyticsInsightsService:
    """Get singleton instance of Analytics Insights Service"""
    global _service_instance
    
    if _service_instance is None:
        _service_instance = AnalyticsInsightsService()
        logger.info("📊 AnalyticsInsightsService singleton created")
    
    return _service_instance
