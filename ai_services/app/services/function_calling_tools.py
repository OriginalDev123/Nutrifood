"""
Function Calling Tools - Production Implementation
6 tools for intelligent chatbot actions
"""

from typing import Dict, Any, Optional
import logging
import httpx
import os
from datetime import date, timedelta

logger = logging.getLogger(__name__)

# Backend API configuration
BACKEND_API_ROOT = os.getenv('BACKEND_API_URL', 'http://backend:8000').rstrip('/')
BACKEND_API = f"{BACKEND_API_ROOT}/api/v1"


# ============================================================================
# TOOL DECLARATIONS (for Gemini API)
# ============================================================================

TOOLS = {
    "function_declarations": [
        {
            "name": "search_food",
            "description": "Search NutriAI's database of 839 foods and recipes. Use when user asks about specific foods, nutrients, or ingredients. Examples: 'Find high protein foods', 'Tìm thực phẩm giàu vitamin C', 'Show me chicken recipes'",
            "parameters": {
                "type": "object",
                "properties": {
                    "criteria": {
                        "type": "string",
                        "description": "Search criteria: food name, nutrient (protein, vitamin C, iron), category (seafood, vegetables), or description"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of results to return (typical: 3-5)"
                    }
                },
                "required": ["criteria"]
            }
        },
        {
            "name": "log_food",
            "description": "Log food intake to user's daily nutrition tracker. ALWAYS call this function when user mentions eating/drinking something. Extract parameters from context. Examples: 'I just ate a bowl of phở' → log_food('phở', 1, 'bowl', 'snack'); 'Tôi vừa ăn 2 tô phở' → log_food('phở', 2, 'bowl', 'lunch'); 'I had chicken rice for lunch' → log_food('chicken rice', 1, 'plate', 'lunch'). If meal_type not specified, infer from time or use 'snack'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "food_name": {
                        "type": "string",
                        "description": "Name of food/drink consumed (Vietnamese or English)"
                    },
                    "amount": {
                        "type": "number",
                        "description": "Quantity consumed (extract from context, default: 1)"
                    },
                    "unit": {
                        "type": "string",
                        "description": "Unit of measurement: 'g', 'ml', 'bowl', 'plate', 'cup', 'piece', 'serving'"
                    },
                    "meal_type": {
                        "type": "string",
                        "description": "Meal type: 'breakfast', 'lunch', 'dinner', 'snack' (infer or default: 'snack')"
                    }
                },
                "required": ["food_name", "amount", "unit", "meal_type"]
            }
        },
        {
            "name": "find_alternatives",
            "description": "Find alternative foods that match specific criteria (lower calories, higher protein, less carbs, etc). Use when user asks to replace a food or find healthier options",
            "parameters": {
                "type": "object",
                "properties": {
                    "food_name": {
                        "type": "string",
                        "description": "Original food name to find alternatives for"
                    },
                    "criteria": {
                        "type": "string",
                        "description": "Criteria for alternatives: 'lower calories', 'higher protein', 'less carbs', 'more fiber', 'healthier'"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of alternatives (1-5)"
                    }
                },
                "required": ["food_name", "criteria"]
            }
        },
        {
            "name": "adjust_goal",
            "description": "Update user's nutrition goals (daily calories, protein, carbs, fat targets). Use when user wants to change their targets",
            "parameters": {
                "type": "object",
                "properties": {
                    "goal_type": {
                        "type": "string",
                        "description": "Type of goal: 'daily_calories', 'protein_target', 'carbs_target', 'fat_target'"
                    },
                    "target_value": {
                        "type": "number",
                        "description": "New target value (in appropriate units: kcal for calories, g for macros)"
                    }
                },
                "required": ["goal_type", "target_value"]
            }
        },
        {
            "name": "regenerate_meal_plan",
            "description": "Generate a new meal plan for N days. Use when user asks to create/regenerate meal plan",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "number",
                        "description": "Number of days for meal plan (1-14)"
                    },
                    "preferences": {
                        "type": "string",
                        "description": "Dietary preferences: 'vegetarian', 'vegan', 'low-carb', 'high-protein', etc"
                    }
                },
                "required": ["days"]
            }
        },
        {
            "name": "get_progress_insight",
            "description": "Get nutrition analytics and progress insights. Use when user asks about their progress, trends, or statistics",
            "parameters": {
                "type": "object",
                "properties": {
                    "timeframe": {
                        "type": "string",
                        "description": "Time period: 'today', 'this_week', 'this_month', 'last_7_days', 'last_30_days'"
                    }
                },
                "required": ["timeframe"]
            }
        },
        {
            "name": "get_weekly_insights",
            "description": "Get AI-powered weekly nutrition summary with highlights, concerns, and recommendations. Use when user asks 'How did I do this week?', 'Weekly summary', 'Tuần này thế nào?', 'Tổng kết tuần'",
            "parameters": {
                "type": "object",
                "properties": {
                    "language": {
                        "type": "string",
                        "description": "Language for insights: 'vi' (Vietnamese) or 'en' (English). Default: 'vi'"
                    }
                },
                "required": []
            }
        },
        {
            "name": "get_goal_analysis",
            "description": "Get AI-powered analysis of goal progress. Use when user asks about goal status: 'Am I reaching my goal?', 'Goal progress', 'Mục tiêu của mình thế nào?', 'Đã giảm được bao nhiêu?'",
            "parameters": {
                "type": "object",
                "properties": {
                    "language": {
                        "type": "string",
                        "description": "Language for insights: 'vi' or 'en'. Default: 'vi'"
                    }
                },
                "required": []
            }
        },
        {
            "name": "get_nutrition_trends",
            "description": "Get AI-powered nutrition trend analysis over time. Use when user asks about patterns: 'What are my eating patterns?', 'Nutrition trends', 'Xu hướng ăn uống', 'Tháng này ăn thế nào?'",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days to analyze (7-90). Default: 30"
                    },
                    "language": {
                        "type": "string",
                        "description": "Language for insights: 'vi' or 'en'. Default: 'vi'"
                    }
                },
                "required": []
            }
        }
    ]
}


# ============================================================================
# TOOL IMPLEMENTATIONS
# ============================================================================

class FunctionCallingTools:
    """Collection of function calling tool implementations"""
    
    def __init__(self, retrieval_service):
        """
        Initialize tools with necessary services
        
        Args:
            retrieval_service: RetrievalService for RAG operations
        """
        self.retrieval = retrieval_service
        logger.info("✅ Function Calling Tools initialized")
    
    def search_food(self, criteria: str, limit: int = 5) -> Dict[str, Any]:
        """
        Search nutrition database using RAG
        
        Args:
            criteria: Search criteria (food name, nutrient, category)
            limit: Maximum number of results
        
        Returns:
            Dict with success status and results list
        """
        try:
            logger.info(f"🔍 Tool: search_food('{criteria}', limit={limit})")
            
            results = self.retrieval.search(
                query=criteria,
                top_k=limit,
                score_threshold=0.20
            )
            
            formatted = []
            for r in results:
                formatted.append({
                    "title": r.get('title', ''),
                    "content": r.get('content', '')[:300],
                    "score": round(r.get('score', 0), 3)
                })
            
            logger.info(f"   Found {len(formatted)} results")
            return {
                "success": True,
                "results": formatted,
                "count": len(formatted)
            }
            
        except Exception as e:
            logger.error(f"❌ search_food error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def log_food(
        self,
        food_name: str,
        amount: float,
        unit: str,
        meal_type: str,
        user_id: Optional[str] = None,
        jwt_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Log food intake via backend API
        
        Args:
            food_name: Name of food/drink
            amount: Quantity
            unit: Unit of measurement
            meal_type: Meal type (breakfast/lunch/dinner/snack)
            user_id: User ID (optional, from JWT token)
        
        Returns:
            Dict with success status and logged item details
        """
        try:
            logger.info(f"📝 Tool: log_food('{food_name}', {amount}{unit}, {meal_type})")

            if not jwt_token:
                return {
                    "success": False,
                    "error": "Authentication required to log food"
                }

            headers = {"Authorization": f"Bearer {jwt_token}"}

            async with httpx.AsyncClient(timeout=15.0) as client:
                search_response = await client.get(
                    f"{BACKEND_API}/foods/search",
                    params={"q": food_name, "limit": 1},
                    headers=headers,
                )

                if search_response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"Food search failed ({search_response.status_code})"
                    }

                foods = search_response.json().get("foods", [])
                if not foods:
                    return {
                        "success": False,
                        "error": f"Không tìm thấy món '{food_name}' trong cơ sở dữ liệu"
                    }

                selected_food = foods[0]
                payload = {
                    "food_id": selected_food["food_id"],
                    "meal_type": meal_type,
                    "meal_date": date.today().isoformat(),
                    "quantity": max(0.5, float(amount)),
                    "notes": f"Logged via chatbot ({amount} {unit})"
                }

                log_response = await client.post(
                    f"{BACKEND_API}/food-logs/",
                    json=payload,
                    headers=headers,
                )

                if log_response.status_code not in (200, 201):
                    error_detail = log_response.text
                    return {
                        "success": False,
                        "error": f"Food log failed ({log_response.status_code}): {error_detail}"
                    }

                return {
                    "success": True,
                    "message": f"Đã ghi {amount} {unit} {selected_food.get('name_vi', food_name)} vào bữa {meal_type}",
                    "logged_item": log_response.json(),
                }

        except Exception as e:
            logger.error(f"❌ log_food error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def find_alternatives(
        self,
        food_name: str,
        criteria: str,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Find food alternatives using RAG
        
        Args:
            food_name: Original food to find alternatives for
            criteria: Search criteria (healthier, lower calories, etc)
            limit: Maximum number of alternatives
        
        Returns:
            Dict with success status and alternatives list
        """
        try:
            logger.info(f"🔄 Tool: find_alternatives('{food_name}', '{criteria}', limit={limit})")
            
            # Search with combined query
            search_query = f"{food_name} alternatives {criteria}"
            results = self.retrieval.search(
                query=search_query,
                top_k=limit,
                score_threshold=0.30
            )
            
            alternatives = []
            for r in results:
                alternatives.append({
                    "name": r.get('title', ''),
                    "info": r.get('content', '')[:200],
                    "relevance": round(r.get('score', 0), 3)
                })
            
            logger.info(f"   Found {len(alternatives)} alternatives")
            return {
                "success": True,
                "original_food": food_name,
                "criteria": criteria,
                "alternatives": alternatives,
                "count": len(alternatives)
            }
            
        except Exception as e:
            logger.error(f"❌ find_alternatives error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def adjust_goal(
        self,
        goal_type: str,
        target_value: float,
        user_id: Optional[str] = None,
        jwt_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update user nutrition goals via backend API
        
        Args:
            goal_type: Type of goal (daily_calories, protein_target, etc)
            target_value: New target value
            user_id: User ID (optional, from JWT token)
        
        Returns:
            Dict with success status and updated goal details
        """
        try:
            logger.info(f"🎯 Tool: adjust_goal('{goal_type}', {target_value})")

            if not jwt_token:
                return {
                    "success": False,
                    "error": "Authentication required to update goals"
                }

            goal_field_map = {
                "daily_calories": "daily_calorie_target",
                "protein_target": "protein_target_g",
                "carbs_target": "carbs_target_g",
                "fat_target": "fat_target_g",
            }
            update_field = goal_field_map.get(goal_type)
            if not update_field:
                return {
                    "success": False,
                    "error": f"Unsupported goal type: {goal_type}"
                }

            headers = {"Authorization": f"Bearer {jwt_token}"}

            async with httpx.AsyncClient(timeout=15.0) as client:
                active_goal_response = await client.get(
                    f"{BACKEND_API}/users/me/goals/active",
                    headers=headers,
                )

                if active_goal_response.status_code != 200:
                    return {
                        "success": False,
                        "error": "Không tìm thấy mục tiêu active để cập nhật"
                    }

                active_goal = active_goal_response.json()
                update_response = await client.patch(
                    f"{BACKEND_API}/users/me/goals/{active_goal['goal_id']}",
                    json={update_field: int(target_value)},
                    headers=headers,
                )

                if update_response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"Goal update failed ({update_response.status_code}): {update_response.text}"
                    }

                return {
                    "success": True,
                    "message": f"Đã cập nhật {goal_type} thành {target_value}",
                    "updated_goal": update_response.json(),
                }

        except Exception as e:
            logger.error(f"❌ adjust_goal error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def regenerate_meal_plan(
        self,
        days: int,
        preferences: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate new meal plan via backend API
        
        Args:
            days: Number of days for meal plan
            preferences: Dietary preferences (vegetarian, vegan, etc)
            user_id: User ID (optional, from JWT token)
        
        Returns:
            Dict with success status and plan details
        """
        try:
            logger.info(f"📅 Tool: regenerate_meal_plan(days={days}, preferences='{preferences}')")
            
            # TODO: Replace with actual backend API call
            # async with httpx.AsyncClient() as client:
            #     response = await client.post(
            #         f"{BACKEND_API}/meal-plan/generate",
            #         json={
            #             "days": days,
            #             "preferences": preferences,
            #             "user_id": user_id
            #         }
            #     )
            #     return response.json()
            
            # Mock response for now
            return {
                "success": True,
                "message": f"Generated new {days}-day meal plan",
                "plan": {
                    "days": days,
                    "preferences": preferences or "No specific preferences",
                    "status": "generated"
                }
            }
            
        except Exception as e:
            logger.error(f"❌ regenerate_meal_plan error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_progress_insight(
        self,
        timeframe: str,
        user_id: Optional[str] = None,
        jwt_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get nutrition analytics and insights via backend API
        
        Args:
            timeframe: Time period (today, this_week, this_month, etc)
            user_id: User ID (optional, from JWT token)
        
        Returns:
            Dict with success status and analytics data
        """
        try:
            logger.info(f"📊 Tool: get_progress_insight('{timeframe}')")

            if not jwt_token:
                return {
                    "success": False,
                    "error": "Authentication required to fetch progress"
                }

            headers = {"Authorization": f"Bearer {jwt_token}"}
            today = date.today()

            def resolve_range(period: str) -> tuple[str, str]:
                if period in ("today",):
                    start = today
                elif period in ("this_week", "last_7_days"):
                    start = today - timedelta(days=7)
                elif period in ("this_month", "last_30_days"):
                    start = today - timedelta(days=30)
                else:
                    start = today - timedelta(days=7)
                return start.isoformat(), today.isoformat()

            start_date, end_date = resolve_range(timeframe)

            async with httpx.AsyncClient(timeout=15.0) as client:
                weekly_summary_res = await client.get(
                    f"{BACKEND_API}/analytics/weekly-summary",
                    headers=headers,
                )
                calorie_comparison_res = await client.get(
                    f"{BACKEND_API}/analytics/calorie-comparison",
                    params={"start_date": start_date, "end_date": end_date},
                    headers=headers,
                )
                goal_progress_res = await client.get(
                    f"{BACKEND_API}/analytics/goal-progress",
                    headers=headers,
                )

                if weekly_summary_res.status_code != 200:
                    return {
                        "success": False,
                        "error": f"Weekly summary unavailable ({weekly_summary_res.status_code})"
                    }

                return {
                    "success": True,
                    "timeframe": timeframe,
                    "insights": {
                        "weekly_summary": weekly_summary_res.json(),
                        "calorie_comparison": calorie_comparison_res.json() if calorie_comparison_res.status_code == 200 else None,
                        "goal_progress": goal_progress_res.json() if goal_progress_res.status_code == 200 else None,
                    }
                }

        except Exception as e:
            logger.error(f"❌ get_progress_insight error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_weekly_insights(
        self,
        language: str = "vi",
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get AI-powered weekly nutrition summary (⭐ Task 11)
        
        Args:
            language: Language for insights (vi/en)
            user_id: User ID (for future token-based auth)
        
        Returns:
            Dict with weekly insights (summary, highlights, concerns, recommendations)
        """
        try:
            logger.info(f"📊 Tool: get_weekly_insights(language='{language}')")
            
            # TODO - Task 11: Implement JWT token auth
            # For now, return informative response about authentication
            return {
                "success": True,
                "period": "last_7_days",
                "summary": "Để xem phân tích chi tiết tuần qua, bạn cần đăng nhập và có dữ liệu ghi nhận." if language == "vi" else "To view detailed weekly analysis, please log in and ensure you have logged data.",
                "highlights": [
                    "Bạn đã hỏi về phân tích tuần qua - tính năng này cần authentication" if language == "vi" else "You asked about weekly analysis - this feature requires authentication"
                ],
                "concerns": [],
                "recommendations": [
                    "Đăng nhập vào hệ thống để xem insights chi tiết" if language == "vi" else "Log in to the system to view detailed insights",
                    "Ghi nhận ít nhất 3-5 ngày dữ liệu để có phân tích chính xác" if language == "vi" else "Log at least 3-5 days of data for accurate analysis"
                ],
                "note": "⚠️ JWT authentication required for full analytics - See /analytics/weekly-insights endpoint"
            }
            
        except Exception as e:
            logger.error(f"❌ get_weekly_insights error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "fallback": "Chưa có đủ dữ liệu để phân tích tuần này" if language == "vi" else "Insufficient data for weekly analysis"
            }
    
    async def get_goal_analysis(
        self,
        language: str = "vi",
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get AI-powered goal progress analysis (⭐ Task 11)
        
        Args:
            language: Language for insights (vi/en)
            user_id: User ID (for future token-based auth)
        
        Returns:
            Dict with goal analysis (status, progress, recommendations, motivation)
        """
        try:
            logger.info(f"🎯 Tool: get_goal_analysis(language='{language}')")
            
            # TODO - Task 11: Implement JWT token auth
            return {
                "success": True,
                "status_message": "Để xem tiến độ mục tiêu, bạn cần đăng nhập" if language == "vi" else "To view goal progress, please log in",
                "progress_assessment": "Chức năng phân tích mục tiêu cần xác thực người dùng để truy cập backend analytics API. Vui lòng sử dụng endpoint /analytics/goal-insights với JWT token." if language == "vi" else "Goal analysis requires user authentication to access backend analytics API. Please use /analytics/goal-insights endpoint with JWT token.",
                "recommendations": [
                    "Đăng nhập vào hệ thống" if language == "vi" else "Log in to the system",
                    "Thiết lập mục tiêu rõ ràng (cân nặng, calories)" if language == "vi" else "Set clear goals (weight, calories)",
                    "Ghi nhận tiến độ đều đặn" if language == "vi" else "Track progress consistently"
                ],
                "motivation": "Bạn đang quan tâm đến mục tiêu của mình - đó là bước đầu quan trọng!" if language == "vi" else "You're caring about your goals - that's an important first step!",
                "note": "⚠️ JWT authentication required - See /analytics/goal-insights endpoint"
            }
            
        except Exception as e:
            logger.error(f"❌ get_goal_analysis error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "fallback": "Chưa có mục tiêu hoặc dữ liệu để phân tích" if language == "vi" else "No active goal or insufficient data"
            }
    
    async def get_nutrition_trends(
        self,
        days: int = 30,
        language: str = "vi",
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get AI-powered nutrition trend analysis (⭐ Task 11)
        
        Args:
            days: Number of days to analyze (7-90)
            language: Language for insights (vi/en)
            user_id: User ID (for future token-based auth)
        
        Returns:
            Dict with trend analysis (patterns, statistics, recommendations)
        """
        try:
            logger.info(f"📈 Tool: get_nutrition_trends(days={days}, language='{language}')")
            
            # Validate days range
            days = max(7, min(90, days))
            
            # TODO - Task 11: Implement JWT token auth
            return {
                "success": True,
                "period_days": days,
                "analysis": {
                    "message": f"Để xem xu hướng {days} ngày, cần xác thực" if language == "vi" else f"To view {days}-day trends, authentication required"
                },
                "insights": f"Chức năng phân tích xu hướng dinh dưỡng {days} ngày cần JWT token để truy cập backend analytics. Bạn có thể sử dụng trực tiếp endpoint POST /analytics/nutrition-trend-insights?days={days}&language={language} với Authorization header." if language == "vi" else f"Nutrition trend analysis for {days} days requires JWT token to access backend analytics. You can use POST /analytics/nutrition-trend-insights?days={days}&language={language} endpoint directly with Authorization header.",
                "note": f"⚠️ JWT authentication required - See /analytics/nutrition-trend-insights?days={days} endpoint"
            }
            
        except Exception as e:
            logger.error(f"❌ get_nutrition_trends error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "fallback": "Chưa có đủ dữ liệu để phân tích xu hướng" if language == "vi" else "Insufficient data for trend analysis"
            }
    
    def get_function_map(self):
        """
        Get mapping of function names to implementations
        
        Returns:
            Dict mapping function names to callable methods (⭐ Updated - Task 11: 9 tools total)
        """
        return {
            "search_food": self.search_food,
            "log_food": self.log_food,
            "find_alternatives": self.find_alternatives,
            "adjust_goal": self.adjust_goal,
            "regenerate_meal_plan": self.regenerate_meal_plan,
            "get_progress_insight": self.get_progress_insight,
            # ⭐ NEW - Task 11: Analytics Integration
            "get_weekly_insights": self.get_weekly_insights,
            "get_goal_analysis": self.get_goal_analysis,
            "get_nutrition_trends": self.get_nutrition_trends
        }
