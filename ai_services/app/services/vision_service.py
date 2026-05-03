"""
Vision Service - Gemini 1.5 Flash Vision Integration
Business logic cho food recognition
"""

from google import genai
from google.genai import types
from PIL import Image
import json
import logging
import time
import asyncio
import re
import httpx
import hashlib
import redis
import os
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)


class VisionService:
    """
    Service gọi Gemini Vision API để nhận diện món ăn
    
    Features:
    - Vietnamese food optimized
    - JSON response guaranteed
    - Error handling & retry logic
    - Confidence scoring
    """
    
    # Prompt template cho Gemini (tối ưu cho món Việt)
    # Updated: Không còn estimate portion nữa - user sẽ chọn từ presets
    FOOD_ANALYSIS_PROMPT = """Analyze this food image (prioritize Vietnamese dishes):

IMPORTANT: Respond with ONLY a valid JSON object, no explanation, no markdown.

{
  "is_food": true,
  "food_name": "Dish name in Vietnamese (e.g., Cơm tấm sườn, Phở bò, Bánh mì thịt)",
  "food_type": "recipe",
  "components": ["ingredient 1", "ingredient 2"],
  "description": "Brief description"
}

RULES:
1. ALWAYS respond with valid JSON - never refuse
2. If definitely not food: {"is_food": false}
3. If uncertain: respond with is_food=true and best guess
4. food_type is always "recipe"
5. Be specific with food_name - include details (e.g., "Cơm tấm sườn" not just "Cơm tấm")

EXAMPLES:
{"is_food": true, "food_name": "Cơm tấm sườn", "food_type": "recipe", "components": ["cơm", "sườn", "bì", "trứng"], "description": "Cơm tấm với sườn nướng"}
{"is_food": true, "food_name": "Phở bò", "food_type": "recipe", "components": ["bánh phở", "thịt bò", "nước dùng"], "description": "Phở bò truyền thống"}"""

    MINIMAL_RECOVERY_PROMPT = """Bạn là API nhận diện món ăn từ ảnh.

Chỉ trả về DUY NHẤT một JSON object hợp lệ 1 dòng, KHÔNG markdown, KHÔNG text thêm.

Format bắt buộc:
{"is_food": true, "food_name": "Tên món", "food_type": "recipe"}

Quy tắc:
- Chỉ dùng 3 key: is_food, food_name, food_type
- food_type chỉ là recipe hoặc ingredient
- Nếu không chắc ảnh là món ăn thì đặt is_food=false và food_name=""
"""

    PLAINTEXT_RECOVERY_PROMPT = """Nhìn ảnh món ăn và trả lời DUY NHẤT một dòng:
- Nếu là món ăn: chỉ ghi tên món chính ngắn gọn (VD: Pho bo, Com tam, Banh mi thit)
- Nếu không phải món ăn: ghi đúng từ NOT_FOOD
Không thêm giải thích, không markdown, không JSON.
"""

    # Latency guardrails: prefer fast and stable responses over long multi-pass retries.
    MAX_TOTAL_PROCESSING_SECONDS = 6.8
    GEMINI_CALL_TIMEOUT_SECONDS = 5
    PRIMARY_MAX_ATTEMPTS = 2
    BACKEND_LOOKUP_TIMEOUT_SECONDS = 4.0
    
    def __init__(self):
        """Khởi tạo Gemini Vision + Redis Cache"""
        self.active_model_name = ""
        self.client = None
        
        # Validate API key
        if not settings.validate_api_key():
            logger.warning("⚠️  GOOGLE_API_KEY chưa được cấu hình!")
            self.client = None
            return

        self._initialize_model()
        self._initialize_redis()
    
    async def analyze_food_image(
        self,
        image_path: Path,
        user_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Phân tích ảnh món ăn bằng Gemini Vision + Backend Database
        
        New workflow (with portion presets):
        1. Gemini nhận diện món ăn
        2. Tìm kiếm trong backend database (recipes/foods)
        3. Lấy portion presets từ database
        4. Trả về kết quả + presets cho user chọn
        
        Args:
            image_path: Đường dẫn ảnh đã nén
            user_hint: Gợi ý từ user (VD: "phở bò")
        
        Returns:
            {
                "is_food": bool,
                "food_name": str,
                "food_type": str,  # "recipe" or "ingredient"
                "components": list,
                "confidence": float,
                "processing_time_ms": int,
                "database_match": {  # Primary match (best result)
                    "item_type": "recipe" | "food",
                    "item_id": str,
                    "name_vi": str,
                    "nutrition": {...}
                },
                "alternatives": [  # Other possible matches (Top-K)
                    {
                        "item_type": "recipe" | "food",
                        "item_id": str,
                        "name_vi": str,
                        "nutrition": {...},
                        "match_score": float
                    }
                ],
                "portion_presets": [  # Presets từ DB (primary match)
                    {
                        "preset_id": str,
                        "size_label": "small" | "medium" | "large",
                        "display_name_vi": str,
                        "grams": int,
                        "is_default": bool
                    }
                ]
            }
        
        Raises:
            ValueError: Nếu phân tích thất bại
        """
        
        start_time = time.time()
        deadline_ts = start_time + self.MAX_TOTAL_PROCESSING_SECONDS
        
        try:
            # === BƯỚC 0: Check cache ===
            cache_key = self._get_cache_key(image_path, user_hint)
            cached_result = self._get_from_cache(cache_key)
            
            if cached_result:
                processing_time_ms = int((time.time() - start_time) * 1000)
                cached_result["processing_time_ms"] = processing_time_ms
                cached_result["from_cache"] = True
                logger.info(f"✅ Cache hit! (time: {processing_time_ms}ms)")
                return cached_result
            
            # Ensure model is initialized
            self._ensure_model()

            # === BƯỚC 1: Load ảnh ===
            image = Image.open(image_path)
            logger.info(f"🔍 Đang phân tích ảnh: {image.size}")
            
            # === BƯỚC 2: Build prompt (thêm user hint nếu có) ===
            prompt = self.FOOD_ANALYSIS_PROMPT
            
            if user_hint:
                prompt += f"\n\nGỢI Ý TỪ NGƯỜI DÙNG: {user_hint}"
                logger.info(f"💡 User hint: {user_hint}")
            
            # === BƯỚC 3: Gọi Gemini Vision API ===
            logger.info("📡 Đang gọi Gemini Vision API...")

            result = None
            parse_error: Optional[Exception] = None
            has_user_hint = bool(user_hint and user_hint.strip())
            max_attempts = self.PRIMARY_MAX_ATTEMPTS if has_user_hint else 1
            retry_temperatures = [0.1, 0.0]

            for attempt in range(max_attempts):
                if not self._has_time_budget(deadline_ts, reserve_seconds=0.8):
                    logger.warning("⏱️ Time budget reached before primary attempt loop completed")
                    break

                if attempt > 0:
                    logger.warning("🔁 Retrying Gemini Vision due to malformed JSON response...")
                    await asyncio.sleep(0.35)

                temperature = retry_temperatures[min(attempt, len(retry_temperatures) - 1)]

                try:
                    response = self._call_vision_api(prompt, image, temperature=temperature)
                except Exception as model_error:
                    parse_error = model_error
                    if self._should_switch_to_fallback_model(model_error):
                        switched = self._switch_to_fallback_model()
                        if switched:
                            logger.warning("⚠️ Vision model unavailable, switched to fallback model and retrying")
                            continue
                    continue

                raw_text = (getattr(response, "text", "") or "").strip()
                logger.info(f"📄 Raw Gemini response length: {len(raw_text)} chars")
                logger.info(f"📄 Raw response: {raw_text[:500]}...")

                if not raw_text:
                    parse_error = ValueError("Empty response from Gemini")
                    continue

                try:
                    result = json.loads(raw_text)
                    break
                except json.JSONDecodeError:
                    logger.warning("⚠️ Response không phải pure JSON, đang extract...")
                    try:
                        result = self._extract_json_from_text(raw_text)
                        break
                    except ValueError as e:
                        parse_error = e

                    recovered_partial = self._recover_partial_result(raw_text, user_hint)
                    if recovered_partial is not None:
                        if recovered_partial.get("is_food") and recovered_partial.get("food_name"):
                            logger.warning("⚠️ Recovered partial JSON fields from malformed response")
                            result = recovered_partial
                            break

                        logger.warning("⚠️ Partial recovery thiếu dữ liệu, tiếp tục thử minimal recovery pass")

            if result is None and has_user_hint and self._has_time_budget(deadline_ts, reserve_seconds=1.4):
                recovered_result, recovery_error = self._attempt_minimal_recovery(image, user_hint)
                if recovered_result is not None:
                    logger.warning("⚠️ Using minimal recovery pass after repeated malformed JSON")
                    result = recovered_result

                if recovery_error is not None:
                    parse_error = recovery_error

            if result is None and self._has_time_budget(deadline_ts, reserve_seconds=0.8):
                label_result, label_error = self._attempt_plaintext_recovery(image, user_hint)
                if label_result is not None:
                    logger.warning("⚠️ Using plaintext label recovery after JSON recovery failures")
                    result = label_result

                if label_error is not None:
                    parse_error = label_error

            if result is None:
                processing_time_ms = int((time.time() - start_time) * 1000)
                logger.warning(f"⚠️ Gemini trả JSON không hợp lệ sau {max_attempts} lần thử: {parse_error}")

                if user_hint and user_hint.strip():
                    hint_name = user_hint.strip()
                    db_matches = await self._search_food_in_backend(hint_name, "recipe", top_k=3)
                    inferred_food_type = "recipe"

                    if not db_matches:
                        db_matches = await self._search_food_in_backend(hint_name, "ingredient", top_k=3)
                        inferred_food_type = "ingredient"

                    primary_match = db_matches[0] if db_matches else None
                    alternatives = db_matches[1:] if len(db_matches) > 1 else []
                    portion_presets: List[Dict[str, Any]] = []

                    if primary_match:
                        inferred_food_type = "recipe" if primary_match.get("item_type") == "recipe" else "ingredient"
                        portion_presets = await self._get_portion_presets(
                            primary_match["item_type"],
                            primary_match["item_id"]
                        )

                    return {
                        "is_food": True,
                        "food_name": hint_name,
                        "food_type": inferred_food_type,
                        "components": [],
                        "description": "AI trả JSON không ổn định, đang dùng gợi ý người dùng để suy luận tạm.",
                        "confidence": 0.45,
                        "database_match": primary_match,
                        "alternatives": alternatives,
                        "portion_presets": portion_presets,
                        "needs_retry": True,
                        "retry_suggestions": [
                            "📸 Chụp gần hơn để thấy rõ món ăn",
                            "💡 Tăng ánh sáng hoặc bật đèn flash",
                            "📐 Chụp từ trên xuống (góc bird's eye view)",
                            "🎯 Điền user_hint cụ thể hơn (VD: banh mi thit, bun bo)"
                        ],
                        "processing_time_ms": processing_time_ms,
                        "from_cache": False,
                        "inferred_from_user_hint": True,
                        "error": str(parse_error) if parse_error else "Invalid JSON response from Gemini"
                    }

                return {
                    "is_food": False,
                    "food_name": "",
                    "food_type": "recipe",
                    "components": [],
                    "description": "Không thể phân tích ổn định từ AI. Vui lòng thử lại với ảnh rõ nét hơn.",
                    "confidence": 0.0,
                    "database_match": None,
                    "alternatives": [],
                    "portion_presets": [],
                    "needs_retry": True,
                    "retry_suggestions": [
                        "📸 Chụp gần hơn để thấy rõ món ăn",
                        "💡 Tăng ánh sáng hoặc bật đèn flash",
                        "📐 Chụp từ trên xuống (góc bird's eye view)",
                        "🎯 Thêm gợi ý tên món ở ô 'user_hint'"
                    ],
                    "processing_time_ms": processing_time_ms,
                    "from_cache": False,
                    "error": str(parse_error) if parse_error else "Invalid JSON response from Gemini"
                }
            
            # === BƯỚC 5: Validate Gemini result ===
            recovery_mode = result.get("_recovery_mode") if isinstance(result, dict) else None
            validated_result = self._validate_and_enhance_result(
                result, 
                user_hint
            )

            # Initialize optional fields to keep response shape stable.
            validated_result.setdefault("database_match", None)
            validated_result.setdefault("alternatives", [])
            validated_result.setdefault("portion_presets", [])
            
            # === BƯỚC 6: Search database + Fetch portion presets ===
            skip_db_enrichment = bool(
                recovery_mode in {"plaintext", "partial", "minimal"} and not (user_hint and user_hint.strip())
            )

            if validated_result["is_food"] and skip_db_enrichment:
                logger.info("⚡ Skipping DB enrichment for low-confidence no-hint recovery to reduce latency")

            if validated_result["is_food"] and not skip_db_enrichment:
                food_name = validated_result.get("food_name", "")
                food_type = validated_result.get("food_type", "recipe")
                
                # Search backend database (Top-K results)
                db_matches = await self._search_food_in_backend(food_name, food_type, top_k=3)
                
                if db_matches:
                    # Primary match (best result)
                    primary = db_matches[0]
                    validated_result["database_match"] = primary
                    
                    # Alternatives (other matches)
                    validated_result["alternatives"] = db_matches[1:] if len(db_matches) > 1 else []
                    
                    # Fetch portion presets for primary match
                    presets = await self._get_portion_presets(
                        primary["item_type"],
                        primary["item_id"]
                    )
                    validated_result["portion_presets"] = presets
                    
                    logger.info(
                        f"✅ Database matches: primary='{primary['name_vi']}', "
                        f"alternatives={len(validated_result['alternatives'])}"
                    )
                else:
                    validated_result["database_match"] = None
                    validated_result["alternatives"] = []
                    validated_result["portion_presets"] = []
                    logger.warning(f"⚠️ '{food_name}' chưa có trong database")
            
            # === BƯỚC 7: Tính processing time ===
            processing_time_ms = int((time.time() - start_time) * 1000)
            validated_result["processing_time_ms"] = processing_time_ms
            
            # Log kết quả
            if validated_result["is_food"]:
                presets_count = len(validated_result.get("portion_presets", []))
                logger.info(
                    f"✅ Nhận diện: {validated_result['food_name']} "
                    f"(confidence: {validated_result['confidence']:.2f}, "
                    f"presets: {presets_count}, time: {processing_time_ms}ms)"
                )
            else:
                logger.info(f"⚠️ Không phải món ăn (time: {processing_time_ms}ms)")
            
            # === BƯỚC 8: Check confidence threshold & suggest retry ===
            validated_result = self.check_confidence_and_suggest_retry(validated_result)
            
            # === BƯỚC 9: Save to cache ===
            self._save_to_cache(cache_key, validated_result)
            validated_result["from_cache"] = False
            
            return validated_result
            
        except Exception as e:
            error_msg = str(e)
            
            # Special handling for quota errors
            if "429" in error_msg or "quota" in error_msg.lower():
                logger.error(f"❌ Gemini quota exceeded: {error_msg}")
                raise ValueError(
                    "Gemini API quota exceeded. Please try again in a few minutes. "
                    "Consider upgrading your API plan for higher limits."
                )
            
            logger.error(f"❌ Lỗi phân tích ảnh: {error_msg}", exc_info=True)
            raise ValueError(f"Gemini Vision error: {error_msg}")

    def _call_vision_api(self, prompt: str, image: Image.Image, temperature: float = 0.1):
        """Call Gemini Vision API with the new SDK"""
        # Convert PIL Image to bytes for the new SDK
        import io
        image_bytes = io.BytesIO()
        image.save(image_bytes, format='PNG')
        image_bytes = image_bytes.getvalue()
        
        image_part = types.Part(inline_data=types.Blob(
            mime_type='image/png',
            data=image_bytes
        ))
        text_part = types.Part(text=prompt)
        
        response = self.client.models.generate_content(
            model=self.active_model_name,
            contents=[types.Content(role="user", parts=[text_part, image_part])],
            config=types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=256
            )
        )
        return response

    def _attempt_minimal_recovery(
        self,
        image: Image.Image,
        user_hint: Optional[str]
    ) -> Tuple[Optional[Dict[str, Any]], Optional[Exception]]:
        """Second-pass recovery with minimal JSON schema to reduce malformed output risk."""
        prompt = self.MINIMAL_RECOVERY_PROMPT
        if user_hint and user_hint.strip():
            prompt += f"\n\nGỢI Ý NGƯỜI DÙNG: {user_hint.strip()}"

        try:
            try:
                response = self._call_vision_api(prompt, image, temperature=0.0)
            except Exception as model_error:
                if self._should_switch_to_fallback_model(model_error):
                    switched = self._switch_to_fallback_model()
                    if switched:
                        response = self._call_vision_api(prompt, image, temperature=0.0)
                    else:
                        return None, model_error
                else:
                    return None, model_error

            raw_text = (getattr(response, "text", "") or "").strip()
            logger.info(f"📄 Minimal recovery raw response length: {len(raw_text)} chars")
            if not raw_text:
                return None, ValueError("Empty response from minimal recovery pass")

            try:
                parsed = json.loads(raw_text)
            except json.JSONDecodeError:
                try:
                    parsed = self._extract_json_from_text(raw_text)
                except ValueError as e:
                    partial = self._recover_partial_result(raw_text, user_hint)
                    if partial is not None:
                        return partial, None
                    return None, e

            food_type = parsed.get("food_type", "recipe")
            if food_type not in ["recipe", "ingredient"]:
                food_type = "recipe"

            food_name = str(parsed.get("food_name", "")).strip()
            is_food = bool(parsed.get("is_food", False))

            if is_food and not food_name and user_hint and user_hint.strip():
                food_name = user_hint.strip()

            if is_food and not food_name:
                is_food = False

            return {
                "is_food": is_food,
                "food_name": food_name,
                "food_type": food_type,
                "components": [],
                "description": "Kết quả được khôi phục bằng chế độ JSON tối giản.",
                "_recovery_mode": "minimal"
            }, None
        except Exception as e:
            return None, e

    def _attempt_plaintext_recovery(
        self,
        image: Image.Image,
        user_hint: Optional[str]
    ) -> Tuple[Optional[Dict[str, Any]], Optional[Exception]]:
        """Last-pass recovery: request only a short dish label instead of JSON."""
        prompt = self.PLAINTEXT_RECOVERY_PROMPT
        if user_hint and user_hint.strip():
            prompt += f"\nGợi ý người dùng: {user_hint.strip()}"

        try:
            response = self._call_vision_api(prompt, image, temperature=0.0)
            raw_text = (getattr(response, "text", "") or "").strip()
            logger.info(f"📄 Plaintext recovery raw response: {raw_text[:120]}")

            if not raw_text:
                return None, ValueError("Empty response from plaintext recovery pass")

            normalized = raw_text.replace("`", "").replace("\n", " ").strip()
            upper = normalized.upper()
            if "NOT_FOOD" in upper:
                return None, ValueError("Plaintext recovery marked image as NOT_FOOD")

            # Handle common prefixes like 'Food:' or 'Tên món:'
            normalized = re.sub(r'^(food|dish|tên món|mon an)\s*[:\-]\s*', '', normalized, flags=re.IGNORECASE)
            normalized = normalized.strip(" .,;:\"'")

            if len(normalized) < 2:
                return None, ValueError("Plaintext recovery returned insufficient label")

            return {
                "is_food": True,
                "food_name": normalized,
                "food_type": "recipe",
                "components": [],
                "description": "Kết quả được khôi phục từ chế độ nhãn văn bản.",
                "_recovery_mode": "plaintext"
            }, None
        except Exception as e:
            return None, e

    def _recover_partial_result(
        self,
        raw_text: str,
        user_hint: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Best-effort recovery for truncated JSON that still contains key fields."""
        if not raw_text:
            return None

        bool_match = re.search(r'"is_food"\s*:\s*(true|false)', raw_text, flags=re.IGNORECASE)
        is_food: Optional[bool] = None
        if bool_match:
            is_food = bool_match.group(1).lower() == "true"

        name_match = re.search(r'"food_name"\s*:\s*"([^"\n\r}]*)', raw_text, flags=re.IGNORECASE)
        food_name = name_match.group(1).strip() if name_match else ""

        type_match = re.search(r'"food_type"\s*:\s*"(recipe|ingredient)"', raw_text, flags=re.IGNORECASE)
        food_type = type_match.group(1).lower() if type_match else "recipe"

        if is_food is None:
            is_food = bool(food_name)

        if is_food and not food_name and user_hint and user_hint.strip():
            food_name = user_hint.strip()

        if not is_food:
            return None

        if not food_name:
            return None

        return {
            "is_food": True,
            "food_name": food_name,
            "food_type": food_type,
            "components": [],
            "description": "Kết quả được suy luận từ phản hồi JSON chưa hoàn chỉnh.",
            "_recovery_mode": "partial"
        }

    def _initialize_model(self) -> None:
        """Initialize Gemini model if API key is configured"""
        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        vision_model_name = settings.GEMINI_VISION_MODEL or settings.GEMINI_MODEL
        self.active_model_name = vision_model_name
        logger.info(f"✅ Gemini Vision initialized: {vision_model_name}")

    def _should_switch_to_fallback_model(self, error: Exception) -> bool:
        """Detect unsupported model errors and decide whether fallback model should be used."""
        error_text = str(error).lower()
        if "not found" in error_text and "model" in error_text:
            fallback = settings.GEMINI_MODEL
            return bool(fallback and fallback != self.active_model_name)
        return False

    def _switch_to_fallback_model(self) -> bool:
        """Switch Vision model to configured fallback model when current model is unavailable."""
        fallback_model = settings.GEMINI_MODEL
        if not fallback_model or fallback_model == self.active_model_name:
            return False

        try:
            self.active_model_name = fallback_model
            logger.info(f"✅ Switched Vision model to fallback: {fallback_model}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to switch fallback model: {e}")
            return False
    
    def _initialize_redis(self) -> None:
        """Initialize Redis client for caching"""
        try:
            # 获取 Redis 连接配置 - 优先使用环境变量，否则使用 Docker 服务名 'redis'
            redis_host = os.environ.get('REDIS_HOST', 'redis')
            redis_port = int(os.environ.get('REDIS_PORT', '6379'))
            redis_db = int(os.environ.get('REDIS_DB', '0'))
            redis_password = os.environ.get('REDIS_PASSWORD') or None
            
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
                decode_responses=True,
                socket_connect_timeout=2
            )
            # Test connection
            self.redis_client.ping()
            logger.info(f"✅ Redis cache initialized: {redis_host}:{redis_port}")
        except Exception as e:
            logger.warning(f"⚠️ Redis not available: {e}")
            self.redis_client = None

    def _ensure_model(self) -> None:
        """Ensure Gemini model is available before making requests"""
        if not settings.validate_api_key():
            raise ValueError("GOOGLE_API_KEY chưa được cấu hình")

        if self.client is None:
            self._initialize_model()

    def _has_time_budget(self, deadline_ts: float, reserve_seconds: float = 0.0) -> bool:
        """Return True when there is enough remaining processing time for another expensive step."""
        return (time.time() + reserve_seconds) < deadline_ts
    
    async def _search_food_in_backend(
        self, 
        food_name: str, 
        food_type: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Tìm kiếm food/recipe trong backend database (Top-K results)
        
        Args:
            food_name: Tên món ăn từ Gemini
            food_type: "recipe" hoặc "ingredient"
            top_k: Số lượng kết quả trả về (default: 3)
        
        Returns:
            List of Food/Recipe info (sorted by relevance), empty list nếu không tìm thấy
        """
        results = []
        
        try:
            async with httpx.AsyncClient(timeout=self.BACKEND_LOOKUP_TIMEOUT_SECONDS) as client:
                # Priority: Recipes (món ăn) > Foods (nguyên liệu)
                if food_type == "recipe":
                    # Search recipes first
                    url = f"{settings.BACKEND_API_URL}/api/recipes/search"
                    params = {"q": food_name, "limit": top_k}
                    
                    logger.info(f"🔍 Searching recipes (top-{top_k}): {food_name}")
                    response = await client.get(url, params=params)
                    
                    if response.status_code == 200:
                        data = response.json()
                        recipes = data.get("recipes", [])
                        
                        for recipe in recipes:
                            results.append({
                                "item_type": "recipe",
                                "item_id": recipe["recipe_id"],
                                "name_vi": recipe["name_vi"],
                                "name_en": recipe.get("name_en"),
                                "category": recipe.get("category"),
                                "calories_per_serving": recipe.get("calories_per_serving"),
                                "protein_per_serving": recipe.get("protein_per_serving"),
                                "carbs_per_serving": recipe.get("carbs_per_serving"),
                                "fat_per_serving": recipe.get("fat_per_serving"),
                                "match_score": recipe.get("match_score", 0.0)  # From fuzzy search
                            })
                        
                        if results:
                            logger.info(f"✅ Found {len(results)} recipe matches")
                
                # Also search foods (nguyên liệu) for additional alternatives
                # Nếu đã có đủ results từ recipes thì không cần search foods
                remaining = top_k - len(results)
                if remaining > 0 or food_type == "ingredient":
                    url = f"{settings.BACKEND_API_URL}/api/foods/search"
                    params = {"q": food_name, "limit": remaining if remaining > 0 else top_k}
                    
                    logger.info(f"🔍 Searching foods (top-{params['limit']}): {food_name}")
                    response = await client.get(url, params=params)
                    
                    if response.status_code == 200:
                        data = response.json()
                        foods = data.get("foods", [])
                        
                        for food in foods:
                            results.append({
                                "item_type": "food",
                                "item_id": food["food_id"],
                                "name_vi": food["name_vi"],
                                "name_en": food.get("name_en"),
                                "category": food.get("category"),
                                "calories_per_100g": food.get("calories_per_100g"),
                                "protein_per_100g": food.get("protein_per_100g"),
                                "carbs_per_100g": food.get("carbs_per_100g"),
                                "fat_per_100g": food.get("fat_per_100g"),
                                "match_score": food.get("match_score", 0.0)
                            })
                        
                        if foods:
                            logger.info(f"✅ Found {len(foods)} food matches")
                
                if not results:
                    logger.warning(f"⚠️ No match found in database: {food_name}")
                
                return results
                
        except Exception as e:
            logger.error(f"❌ Backend search error: {str(e)}")
            return []
    
    async def _get_portion_presets(
        self,
        item_type: str,
        item_id: str
    ) -> List[Dict[str, Any]]:
        """
        Lấy portion presets từ backend
        
        Args:
            item_type: "recipe" hoặc "food"
            item_id: UUID của recipe/food
        
        Returns:
            List of portion presets (có thể empty nếu chưa có)
        """
        try:
            async with httpx.AsyncClient(timeout=self.BACKEND_LOOKUP_TIMEOUT_SECONDS) as client:
                # Endpoint: GET /api/recipes/{id}/portions hoặc /api/foods/{id}/portions
                if item_type == "recipe":
                    url = f"{settings.BACKEND_API_URL}/api/recipes/{item_id}/portions"
                else:
                    url = f"{settings.BACKEND_API_URL}/api/foods/{item_id}/portions"
                
                logger.info(f"📦 Fetching portion presets: {item_type}/{item_id}")
                response = await client.get(url)
                
                if response.status_code == 200:
                    presets = response.json()
                    logger.info(f"✅ Found {len(presets)} portion presets")
                    return presets
                elif response.status_code == 404:
                    logger.warning(f"⚠️ No portion presets found for {item_type}/{item_id}")
                    return []
                else:
                    logger.error(f"❌ Backend error: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"❌ Portion presets fetch error: {str(e)}")
            return []
    
    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extract JSON từ text response (fallback method)
        
        Xử lý trường hợp Gemini trả về text kèm JSON
        """
        cleaned = text.strip()

        # Remove markdown code blocks
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0]
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0]

        cleaned = cleaned.strip()

        # Try extracting the outermost JSON object
        first_brace = cleaned.find("{")
        last_brace = cleaned.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            cleaned = cleaned[first_brace:last_brace + 1]
        elif last_brace == -1:
            raise ValueError("Invalid JSON response: missing closing brace")

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            # Remove trailing commas before closing braces/brackets
            repaired = re.sub(r",\s*([}\]])", r"\1", cleaned)
            try:
                return json.loads(repaired)
            except json.JSONDecodeError:
                logger.error(f"❌ Không parse được JSON: {cleaned[:200]}...")
                raise ValueError(f"Invalid JSON response: {str(e)}")
    
    def _validate_and_enhance_result(
        self,
        result: Dict[str, Any],
        user_hint: Optional[str]
    ) -> Dict[str, Any]:
        """
        Validate kết quả từ Gemini và bổ sung confidence score
        
        Args:
            result: Raw result từ Gemini
            user_hint: User hint (dùng để tính confidence)
        
        Returns:
            Enhanced result với confidence score
        """
        
        # === VALIDATE REQUIRED FIELDS ===
        if "is_food" not in result:
            result["is_food"] = False
        
        # Nếu không phải món ăn, return luôn
        if not result["is_food"]:
            result.pop("_recovery_mode", None)
            result["confidence"] = 0.0
            return result
        
        # Validate các field bắt buộc (updated: food_type, description thay vì portion_estimate)
        required_fields = {
            "food_name": "",
            "food_type": "recipe",  # Default to recipe
            "components": [],
            "description": ""
        }
        
        for field, default_value in required_fields.items():
            if field not in result:
                logger.warning(f"⚠️ Missing field: {field}, using default")
                result[field] = default_value
        
        # === TÍNH CONFIDENCE SCORE ===
        confidence = 0.7  # Default confidence
        
        # Nếu food_name khớp với user_hint → confidence cao hơn
        if user_hint and result.get("food_name"):
            food_name_lower = result["food_name"].lower()
            hint_lower = user_hint.lower()
            
            if hint_lower in food_name_lower or food_name_lower in hint_lower:
                confidence = 0.95
                logger.info("✨ Food name khớp với user hint → confidence tăng")
        
        # Nếu có ít components → confidence thấp hơn
        if len(result.get("components", [])) < 2:
            confidence *= 0.9
        
        # Nếu food_type rõ ràng → confidence tăng
        if result.get("food_type") in ["recipe", "ingredient"]:
            confidence *= 1.05

        # Recovery outputs are useful but should remain conservative.
        if result.get("_recovery_mode"):
            confidence = min(confidence, 0.55)

        # Remove internal-only field from API response payload.
        result.pop("_recovery_mode", None)
        
        result["confidence"] = round(min(confidence, 1.0), 2)  # Cap at 1.0
        
        return result

    
    def check_confidence_and_suggest_retry(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Kiểm tra confidence threshold và suggest retry nếu cần
        
        Args:
            result: Result từ analyze_food_image
        
        Returns:
            Enhanced result với retry suggestions nếu confidence thấp
        """
        CONFIDENCE_THRESHOLD = 0.6
        
        if not result.get("is_food"):
            return result
        
        confidence = result.get("confidence", 0.0)
        
        # Nếu confidence thấp và không có database match
        if confidence < CONFIDENCE_THRESHOLD and not result.get("database_match"):
            result["needs_retry"] = True
            result["retry_suggestions"] = [
                "📸 Chụp gần hơn để thấy rõ món ăn",
                "💡 Tăng ánh sáng hoặc bật đèn flash",
                "📐 Chụp từ trên xuống (góc bird's eye view)",
                "✋ Đặt tay/điện thoại vào ảnh để làm scale reference",
                "🎯 Thêm gợi ý tên món ở ô 'user_hint'"
            ]
            logger.warning(
                f"⚠️ Low confidence ({confidence:.2f}) + No database match → Suggesting retry"
            )
        else:
            result["needs_retry"] = False
            result["retry_suggestions"] = []
        
        return result
    
    def _get_cache_key(self, image_path: Path, user_hint: Optional[str] = None) -> str:
        """Generate cache key from image hash + user hint"""
        try:
            with open(image_path, 'rb') as f:
                image_hash = hashlib.md5(f.read()).hexdigest()
            
            if user_hint:
                hint_hash = hashlib.md5(user_hint.encode()).hexdigest()[:8]
                return f"vision:{image_hash}:{hint_hash}"
            
            return f"vision:{image_hash}"
        except Exception as e:
            logger.warning(f"⚠️ Cache key generation failed: {e}")
            return None
    
    def _get_from_cache(self, cache_key: Optional[str]) -> Optional[Dict[str, Any]]:
        """Get result from Redis cache"""
        if not cache_key or not self.redis_client:
            return None
        
        try:
            cached = self.redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"⚠️ Cache read failed: {e}")
        
        return None
    
    def _save_to_cache(self, cache_key: Optional[str], result: Dict[str, Any]) -> None:
        """Save result to Redis cache (24h TTL)"""
        if not cache_key or not self.redis_client:
            return
        
        try:
            # Don't cache errors or uncertain results
            if not result.get("is_food") or result.get("needs_retry"):
                return
            
            # Remove non-cacheable fields
            cache_data = {k: v for k, v in result.items() 
                         if k not in ["processing_time_ms", "from_cache"]}
            
            self.redis_client.setex(
                cache_key,
                86400,  # 24 hours
                json.dumps(cache_data, ensure_ascii=False)
            )
            logger.info(f"💾 Saved to cache: {cache_key[:40]}...")
        except Exception as e:
            logger.warning(f"⚠️ Cache save failed: {e}")


# Singleton instance
vision_service = VisionService()
