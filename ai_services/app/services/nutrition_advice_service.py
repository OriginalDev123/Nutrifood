"""
Nutrition Advice Service
AI-powered personalized nutrition advice based on analytics data.

Sử dụng prompt từ nutrition_advice_prompt.py để:
1. Phân tích toàn diện dinh dưỡng + cân nặng (ngày/tuần/tháng)
2. Tạo lời khuyên cá nhân hóa dựa trên dữ liệu thực tế
3. Tạo báo cáo tiến độ (weekly/monthly)
4. Tạo quick tips cho bữa ăn tiếp theo
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Literal
from datetime import datetime, date, timedelta
from decimal import Decimal
import httpx
import json
import re

from google import genai
from google.genai import types

from app.config import settings
from app.prompts.nutrition_advice_prompt import (
    build_nutrition_advice_prompt,
    build_quick_advice_prompt,
    build_progress_report_prompt
)

logger = logging.getLogger(__name__)

# Configure Gemini client
client = genai.Client(api_key=settings.GOOGLE_API_KEY)


class NutritionAdviceService:
    """
    AI-powered nutrition advice service.

    Features:
    - Full personalized nutrition advice (dựa trên trends + weight + meal patterns)
    - Quick advice (cho bữa ăn tiếp theo trong ngày)
    - Progress reports (weekly/monthly)
    - Weight trend analysis (theo ngày/tuần/tháng)
    """

    def __init__(self, backend_url: str = "http://backend:8000"):
        """
        Initialize Nutrition Advice Service.

        Args:
            backend_url: URL của backend API
        """
        self.backend_url = backend_url.rstrip("/")
        self.analytics_base_url = f"{self.backend_url}/api/v1/analytics"
        self.model_name = settings.GEMINI_MODEL
        logger.info(f"✅ NutritionAdviceService initialized (backend: {backend_url})")

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

    async def fetch_user_profile(self, user_token: str) -> Dict:
        """
        Lấy thông tin user profile từ backend.

        Args:
            user_token: JWT token

        Returns:
            User profile data
        """
        headers = {"Authorization": f"Bearer {user_token}"}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.backend_url}/api/v1/users/me/profile",
                    headers=headers,
                    timeout=10.0
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"⚠️ Failed to fetch profile: {response.status_code}")
                    return {}

            except Exception as e:
                logger.error(f"❌ Error fetching profile: {e}")
                return {}

    async def fetch_daily_summary(
        self,
        user_token: str,
        target_date: Optional[date] = None
    ) -> Dict:
        """
        Lấy tổng quan dinh dưỡng hôm nay.

        Args:
            user_token: JWT token
            target_date: Ngày cần lấy (default: hôm nay)

        Returns:
            Daily summary data
        """
        target_date = target_date or date.today()
        headers = {"Authorization": f"Bearer {user_token}"}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.backend_url}/api/v1/analytics/daily-summary",
                    params={"date": target_date.isoformat()},
                    headers=headers,
                    timeout=10.0
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    return {}

            except Exception as e:
                logger.error(f"❌ Error fetching daily summary: {e}")
                return {}

    async def fetch_nutrition_trends(
        self,
        user_token: str,
        days: int = 7,
        group_by: str = "day"
    ) -> List[Dict]:
        """
        Lấy xu hướng dinh dưỡng.

        Args:
            user_token: JWT token
            days: Số ngày phân tích
            group_by: "day", "week", "month"

        Returns:
            List of daily nutrition data
        """
        today = date.today()
        start_date = today - timedelta(days=days)
        headers = {"Authorization": f"Bearer {user_token}"}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.analytics_base_url}/nutrition-trends",
                    params={
                        "start_date": start_date.isoformat(),
                        "end_date": today.isoformat(),
                        "group_by": group_by
                    },
                    headers=headers,
                    timeout=10.0
                )

                if response.status_code == 200:
                    data = response.json()
                    # Backend trả về {"trends": [...]} hoặc list trực tiếp
                    if isinstance(data, dict) and "trends" in data:
                        return data["trends"]
                    return data if isinstance(data, list) else []
                else:
                    return []

            except Exception as e:
                logger.error(f"❌ Error fetching nutrition trends: {e}")
                return []

    async def fetch_weight_progress(
        self,
        user_token: str,
        days: int = 30
    ) -> Dict:
        """
        Lấy tiến độ cân nặng.

        Args:
            user_token: JWT token
            days: Số ngày phân tích

        Returns:
            Weight progress data
        """
        headers = {"Authorization": f"Bearer {user_token}"}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.analytics_base_url}/weight-progress",
                    params={"days": days},
                    headers=headers,
                    timeout=10.0
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    return {}

            except Exception as e:
                logger.error(f"❌ Error fetching weight progress: {e}")
                return {}

    async def fetch_meal_patterns(
        self,
        user_token: str,
        days: int = 7
    ) -> Dict:
        """
        Lấy mẫu bữa ăn.

        Args:
            user_token: JWT token
            days: Số ngày phân tích

        Returns:
            Meal patterns data
        """
        headers = {"Authorization": f"Bearer {user_token}"}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.analytics_base_url}/meal-patterns",
                    params={"days": days},
                    headers=headers,
                    timeout=10.0
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    return {}

            except Exception as e:
                logger.error(f"❌ Error fetching meal patterns: {e}")
                return {}

    async def fetch_remaining_nutrients(
        self,
        user_token: str,
        target_date: Optional[date] = None
    ) -> Dict:
        """
        Lấy dinh dưỡng còn lại trong ngày.

        Args:
            user_token: JWT token
            target_date: Ngày cần lấy

        Returns:
            Remaining nutrients data
        """
        target_date = target_date or date.today()
        headers = {"Authorization": f"Bearer {user_token}"}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.analytics_base_url}/daily-remaining",
                    params={"date": target_date.isoformat()},
                    headers=headers,
                    timeout=10.0
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    return {}

            except Exception as e:
                logger.error(f"❌ Error fetching remaining nutrients: {e}")
                return {}

    # ==========================================
    # FULL ANALYTICS DATA FETCH
    # ==========================================

    async def fetch_full_analytics_data(
        self,
        user_token: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Lấy tất cả dữ liệu analytics cần thiết cho advice.

        Args:
            user_token: JWT token
            days: Số ngày phân tích

        Returns:
            Combined analytics data
        """
        # Fetch tất cả data song song
        tasks = [
            self.fetch_user_profile(user_token),
            self.fetch_daily_summary(user_token),
            self.fetch_nutrition_trends(user_token, days=days),
            self.fetch_weight_progress(user_token, days=days),
            self.fetch_meal_patterns(user_token, days=days)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            "user_profile": results[0] if not isinstance(results[0], Exception) else {},
            "daily_summary": results[1] if not isinstance(results[1], Exception) else {},
            "nutrition_trends": results[2] if not isinstance(results[2], Exception) else [],
            "weight_progress": results[3] if not isinstance(results[3], Exception) else {},
            "meal_patterns": results[4] if not isinstance(results[4], Exception) else {}
        }

    # ==========================================
    # BUILD USER CONTEXT
    # ==========================================

    def _build_user_context(self, data: Dict) -> Dict:
        """
        Build user context từ raw data.

        Args:
            data: Combined analytics data

        Returns:
            User context for prompt
        """
        profile = data.get("user_profile", {})
        weight = data.get("weight_progress", {})

        # Normalize profile data
        user_profile = profile.get("data", profile) if isinstance(profile, dict) else profile

        # Get current weight từ weight progress
        current_weight = weight.get("current_weight") or user_profile.get("current_weight_kg")

        # Build context
        context = {
            "user_id": user_profile.get("user_id") or user_profile.get("id"),
            "current_weight_kg": current_weight,
            "height_cm": user_profile.get("height_cm"),
            "age": user_profile.get("age"),
            "gender": user_profile.get("gender"),
            "goal_type": user_profile.get("goal_type") or weight.get("goal_type"),
            "target_weight_kg": weight.get("target_weight") or user_profile.get("target_weight_kg"),
            "daily_calorie_target": user_profile.get("daily_calorie_target"),
            "target_protein_g": user_profile.get("target_protein_g"),
            "target_carbs_g": user_profile.get("target_carbs_g"),
            "target_fat_g": user_profile.get("target_fat_g"),
            "activity_level": user_profile.get("activity_level")
        }

        return context

    # ==========================================
    # ADVICE GENERATION
    # ==========================================

    async def generate_full_advice(
        self,
        user_token: str,
        days: int = 7,
        period: Literal["day", "week", "month"] = "week",
        language: str = "vi"
    ) -> Dict[str, Any]:
        """
        Tạo lời khuyên dinh dưỡng đầy đủ dựa trên analytics.

        Đây là endpoint chính - phân tích:
        - Tổng quan dinh dưỡng (calories, protein, carbs, fat)
        - Cân nặng + thay đổi theo ngày/tuần/tháng
        - Mẫu bữa ăn
        - Xu hướng

        Args:
            user_token: JWT token
            days: Số ngày phân tích (7 = tuần, 30 = tháng)
            period: "day" | "week" | "month"
            language: "vi" | "en"

        Returns:
            {
                "summary": "Tổng kết ngắn",
                "highlights": ["Điểm sáng 1", ...],
                "concerns": ["Vấn đề 1", ...],
                "recommendations": ["Lời khuyên 1", ...],
                "motivational_tip": "Động lực"
            }
        """
        logger.info(f"📊 Generating full nutrition advice ({days} days, period={period})")

        # 1. Fetch all data
        data = await self.fetch_full_analytics_data(user_token, days=days)

        # 2. Build user context
        user_context = self._build_user_context(data)

        # Log data availability for debugging
        nutrition_trends = data.get("nutrition_trends", [])
        weight_progress = data.get("weight_progress", {})
        logger.info(f"📊 Data available - nutrition trends: {len(nutrition_trends)} days, weight history: {len(weight_progress.get('history', []))} entries")

        # 3. Build prompt (handles empty data gracefully)
        prompt = build_nutrition_advice_prompt(
            user_context=user_context,
            nutrition_trends=data.get("nutrition_trends", []),
            weight_progress=data.get("weight_progress", {}),
            daily_summary=data.get("daily_summary", {}),
            meal_patterns=data.get("meal_patterns", {}),
            period=period
        )

        # 4. Generate with AI
        try:
            advice_text = await self._generate_content(
                prompt,
                max_tokens=2048,
                temperature=0.3
            )

            # 5. Parse JSON response
            advice = self._parse_advice_response(advice_text)

            # 6. Add metadata
            advice["period"] = period
            advice["days_analyzed"] = days
            advice["generated_at"] = datetime.now().isoformat()
            advice["raw_data"] = {
                "nutrition_trends_count": len(data.get("nutrition_trends", [])),
                "weight_history_count": len(data.get("weight_progress", {}).get("history", []))
            }

            logger.info(f"✅ Generated full advice successfully")
            return advice

        except Exception as e:
            logger.error(f"❌ Error generating full advice: {e}")
            return self._error_response(str(e))

    async def generate_quick_advice(
        self,
        user_token: str,
        target_date: Optional[date] = None,
        language: str = "vi"
    ) -> Dict[str, Any]:
        """
        Tạo lời khuyên NHANH cho bữa ăn tiếp theo trong ngày.

        Args:
            user_token: JWT token
            target_date: Ngày cần advice (default: hôm nay)
            language: "vi" | "en"

        Returns:
            {
                "quick_tip": "Lời khuyên 1 câu",
                "action": "Hành động cụ thể",
                "why": "Tại sao"
            }
        """
        logger.info(f"⚡ Generating quick advice for {target_date or date.today()}")

        target_date = target_date or date.today()

        # 1. Fetch data
        tasks = [
            self.fetch_user_profile(user_token),
            self.fetch_daily_summary(user_token, target_date),
            self.fetch_remaining_nutrients(user_token, target_date)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        user_profile = results[0] if not isinstance(results[0], Exception) else {}
        daily_summary = results[1] if not isinstance(results[1], Exception) else {}
        remaining = results[2] if not isinstance(results[2], Exception) else {}

        # Log data availability
        logger.info(f"⚡ Quick advice data - daily summary: {bool(daily_summary)}, remaining: {bool(remaining)}")

        # Build user context
        user_context = {
            "current_weight_kg": user_profile.get("data", user_profile).get("current_weight_kg") if isinstance(user_profile, dict) else None,
            "goal_type": user_profile.get("data", user_profile).get("goal_type") if isinstance(user_profile, dict) else None,
            "daily_calorie_target": user_profile.get("data", user_profile).get("daily_calorie_target") if isinstance(user_profile, dict) else None,
            "target_protein_g": user_profile.get("data", user_profile).get("target_protein_g") if isinstance(user_profile, dict) else None,
        }

        # Add date to daily summary
        daily_summary["date"] = target_date.isoformat()

        # 2. Build prompt
        prompt = build_quick_advice_prompt(
            user_context=user_context,
            daily_summary=daily_summary,
            remaining_nutrients=remaining
        )

        # 3. Generate
        try:
            advice_text = await self._generate_content(
                prompt,
                max_tokens=512,
                temperature=0.4
            )

            # 4. Parse
            advice = self._parse_quick_advice_response(advice_text)
            advice["date"] = target_date.isoformat()
            advice["generated_at"] = datetime.now().isoformat()

            logger.info(f"✅ Generated quick advice successfully")
            return advice

        except Exception as e:
            logger.error(f"❌ Error generating quick advice: {e}")
            return self._error_quick_response(str(e))

    async def generate_progress_report(
        self,
        user_token: str,
        period: Literal["week", "month"] = "week",
        language: str = "vi"
    ) -> Dict[str, Any]:
        """
        Tạo báo cáo tiến độ (weekly/monthly).

        Args:
            user_token: JWT token
            period: "week" | "month"
            language: "vi" | "en"

        Returns:
            Progress report với achievements, areas_for_improvement, etc.
        """
        logger.info(f"📈 Generating progress report ({period})")

        days = 7 if period == "week" else 30

        # 1. Fetch data
        tasks = [
            self.fetch_user_profile(user_token),
            self.fetch_weight_progress(user_token, days=days),
            self.fetch_nutrition_trends(user_token, days=days)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        user_profile = results[0] if not isinstance(results[0], Exception) else {}
        weight_progress = results[1] if not isinstance(results[1], Exception) else {}
        nutrition_trends = results[2] if not isinstance(results[2], Exception) else []

        # Log data availability
        logger.info(f"📈 Progress report data - weight history: {len(weight_progress.get('history', []))}, nutrition days: {len(nutrition_trends)}")

        # Build user context
        user_context = {
            "current_weight_kg": weight_progress.get("current_weight"),
            "goal_type": user_profile.get("data", user_profile).get("goal_type") if isinstance(user_profile, dict) else None,
            "daily_calorie_target": user_profile.get("data", user_profile).get("daily_calorie_target") if isinstance(user_profile, dict) else None,
            "target_protein_g": user_profile.get("data", user_profile).get("target_protein_g") if isinstance(user_profile, dict) else None,
            "target_weight_kg": weight_progress.get("target_weight")
        }

        # 2. Build prompt
        prompt = build_progress_report_prompt(
            user_context=user_context,
            weight_progress=weight_progress,
            nutrition_trends=nutrition_trends,
            period=period
        )

        # 3. Generate
        try:
            report_text = await self._generate_content(
                prompt,
                max_tokens=1536,
                temperature=0.3
            )

            # 4. Parse
            report = self._parse_progress_report_response(report_text)
            report["period"] = period
            report["days_analyzed"] = days
            report["generated_at"] = datetime.now().isoformat()

            logger.info(f"✅ Generated progress report successfully")
            return report

        except Exception as e:
            logger.error(f"❌ Error generating progress report: {e}")
            return self._error_progress_response(str(e))

    # ==========================================
    # RESPONSE PARSING
    # ==========================================

    def _parse_advice_response(self, text: str) -> Dict:
        """Parse AI response thành structured advice."""
        try:
            # Clean markdown
            cleaned = self._clean_json_text(text)

            # Parse JSON
            advice = json.loads(cleaned)

            # Validate required fields
            required = ["summary", "highlights", "concerns", "recommendations"]
            for field in required:
                if field not in advice:
                    advice[field] = []

            # Ensure motivational_tip
            if "motivational_tip" not in advice:
                advice["motivational_tip"] = "Tiếp tục cố gắng! Bạn đang làm rất tốt!"

            return advice

        except json.JSONDecodeError as e:
            logger.warning(f"⚠️ Failed to parse advice JSON: {e}")
            return {
                "summary": text[:300] if text else "Không thể phân tích dữ liệu",
                "highlights": [],
                "concerns": [],
                "recommendations": ["Vui lòng thử lại sau"],
                "motivational_tip": "Hãy tiếp tục theo dõi dinh dưỡng!"
            }

    def _parse_quick_advice_response(self, text: str) -> Dict:
        """Parse AI response thành quick advice."""
        try:
            cleaned = self._clean_json_text(text)
            advice = json.loads(cleaned)

            required = ["quick_tip", "action", "why"]
            for field in required:
                if field not in advice:
                    advice[field] = ""

            return advice

        except json.JSONDecodeError:
            return {
                "quick_tip": text[:200] if text else "Tạm thời không có lời khuyên",
                "action": "Thử lại sau",
                "why": ""
            }

    def _parse_progress_report_response(self, text: str) -> Dict:
        """Parse AI response thành progress report."""
        try:
            cleaned = self._clean_json_text(text)
            report = json.loads(cleaned)

            # Ensure all required fields
            defaults = {
                "overall_score": 0,
                "summary": "",
                "weight_analysis": {"progress": "", "on_track": False, "reasoning": ""},
                "nutrition_analysis": {"calorie_adherence": "", "protein_quality": "", "consistency": ""},
                "achievements": [],
                "areas_for_improvement": [],
                "next_week_tips": [],
                "motivation": ""
            }

            for key, value in defaults.items():
                if key not in report:
                    report[key] = value

            return report

        except json.JSONDecodeError:
            return {
                "overall_score": 0,
                "summary": text[:400] if text else "Không thể tạo báo cáo",
                "weight_analysis": {"progress": "", "on_track": False, "reasoning": ""},
                "nutrition_analysis": {"calorie_adherence": "", "protein_quality": "", "consistency": ""},
                "achievements": [],
                "areas_for_improvement": ["Vui lòng thử lại sau"],
                "next_week_tips": [],
                "motivation": "Hãy tiếp tục phấn đấu!"
            }

    def _clean_json_text(self, text: str) -> str:
        """Clean text để parse JSON."""
        # Remove markdown code blocks
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        text = text.strip()
        return text

    def _error_response(self, error: str) -> Dict:
        """Error response cho full advice."""
        return {
            "summary": "Xin lỗi, không thể phân tích dữ liệu lúc này",
            "highlights": [],
            "concerns": [f"Lỗi: {error}"],
            "recommendations": ["Vui lòng thử lại sau hoặc liên hệ hỗ trợ"],
            "motivational_tip": "Đừng nản lòng, hãy tiếp tục theo dõi!"
        }

    def _error_quick_response(self, error: str) -> Dict:
        """Error response cho quick advice."""
        return {
            "quick_tip": "Tạm thời không có lời khuyên",
            "action": "Thử lại sau",
            "why": f"Lỗi: {error}"
        }

    def _error_progress_response(self, error: str) -> Dict:
        """Error response cho progress report."""
        return {
            "overall_score": 0,
            "summary": "Không thể tạo báo cáo tiến độ",
            "weight_analysis": {"progress": "", "on_track": False, "reasoning": f"Lỗi: {error}"},
            "nutrition_analysis": {"calorie_adherence": "", "protein_quality": "", "consistency": ""},
            "achievements": [],
            "areas_for_improvement": ["Vui lòng thử lại sau"],
            "next_week_tips": [],
            "motivation": "Hãy tiếp tục phấn đấu!"
        }


# ==========================================
# SERVICE FACTORY
# ==========================================

_service_instance: Optional[NutritionAdviceService] = None


def get_nutrition_advice_service() -> NutritionAdviceService:
    """Get singleton instance của NutritionAdviceService."""
    global _service_instance

    if _service_instance is None:
        _service_instance = NutritionAdviceService()
        logger.info("🍎 NutritionAdviceService singleton created")

    return _service_instance
