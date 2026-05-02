"""
Nutrition Service - Business Logic cho Nutrition Search
Kết hợp fuzzy matching với database để tìm món ăn
"""

from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging
import time

from app.database import Food
from app.services.fuzzy_matcher import vietnamese_matcher, get_dynamic_threshold, SearchLogger

logger = logging.getLogger(__name__)


class NutritionService:
    """
    Service xử lý nutrition search
    
    Features:
    - Fuzzy search foods trong database
    - Return best match hoặc top K candidates
    - Timing & logging
    """
    
    def search_food(
        self,
        db: Session,
        food_name: str,
        return_top_k: bool = False,
        threshold: Optional[int] = None,  # Now optional - uses dynamic if not provided
        top_k: int = 3
    ) -> Dict[str, Any]:
        """
        Search món ăn trong database bằng fuzzy matching
        
        Args:
            db: Database session
            food_name: Tên món ăn cần tìm
            return_top_k: True = return top K, False = best match only
            threshold: Minimum similarity score (0-100). If None, uses dynamic threshold
            top_k: Số lượng kết quả nếu return_top_k=True
        
        Returns:
            {
                "matched": bool,
                "food": dict (best match) hoặc
                "candidates": list (top K matches),
                "search_time_ms": int
            }
        """
        
        start_time = time.time()
        
        # Use dynamic threshold if not specified
        if threshold is None:
            threshold = get_dynamic_threshold(food_name)
            logger.info(f"🎯 Using dynamic threshold: {threshold} for query length {len(food_name)}")
        
        try:
            logger.info(
                f"🔍 Searching for: '{food_name}' "
                f"(top_k={return_top_k}, threshold={threshold})"
            )
            
            # === BƯỚC 1: Query all active foods ===
            foods = db.query(Food).filter(
                Food.is_deleted == False
            ).all()
            
            if not foods:
                logger.warning("⚠️ No foods in database")
                return {
                    "matched": False,
                    "error": "Database is empty",
                    "search_time_ms": int((time.time() - start_time) * 1000)
                }
            
            logger.debug(f"📊 Loaded {len(foods)} foods from database")
            
            # === BƯỚC 2: Prepare candidates ===
            # Format: "Tên Việt / Tên Anh" để tăng khả năng match
            candidates = []
            for food in foods:
                # Combine Vietnamese và English names
                combined_name = food.name_vi
                if food.name_en:
                    combined_name += f" / {food.name_en}"
                
                candidates.append((combined_name, food))
            
            # === BƯỚC 3: Fuzzy search ===
            if return_top_k:
                # Return top K matches
                matches = vietnamese_matcher.get_top_matches(
                    query=food_name,
                    candidates=candidates,
                    top_k=top_k,
                    threshold=threshold
                )
                
                search_time_ms = int((time.time() - start_time) * 1000)
                
                if matches:
                    result = {
                        "matched": True,
                        "candidates": [
                            {
                                "food": food.to_dict(),
                                "similarity_score": round(score, 1),
                                "matched_name": name
                            }
                            for food, score, name in matches
                        ],
                        "search_time_ms": search_time_ms
                    }
                    
                    # Log search success
                    SearchLogger.log_search(
                        query=food_name,
                        matched=True,
                        similarity_score=matches[0][1],  # Best match score
                        matched_name=matches[0][2],
                        search_time_ms=search_time_ms,
                        threshold=threshold
                    )
                    
                    logger.info(
                        f"✅ Found {len(matches)} candidates "
                        f"(time: {search_time_ms}ms)"
                    )
                else:
                    result = {
                        "matched": False,
                        "message": f"Không tìm thấy món ăn tương tự '{food_name}'",
                        "search_time_ms": search_time_ms
                    }
                    
                    # Log search failure
                    SearchLogger.log_search(
                        query=food_name,
                        matched=False,
                        search_time_ms=search_time_ms,
                        threshold=threshold
                    )
                    
                    logger.info(f"⚠️ No matches found (time: {search_time_ms}ms)")
                
                return result
            
            else:
                # Return best match only
                match = vietnamese_matcher.find_best_match(
                    query=food_name,
                    candidates=candidates,
                    threshold=threshold
                )
                
                search_time_ms = int((time.time() - start_time) * 1000)
                
                if match:
                    food, score, name = match
                    
                    result = {
                        "matched": True,
                        "food": food.to_dict(),
                        "similarity_score": round(score, 1),
                        "matched_name": name,
                        "search_time_ms": search_time_ms
                    }
                    
                    # Log search success
                    SearchLogger.log_search(
                        query=food_name,
                        matched=True,
                        similarity_score=score,
                        matched_name=name,
                        search_time_ms=search_time_ms,
                        threshold=threshold
                    )
                    
                    logger.info(
                        f"✅ Best match: '{food.name_vi}' "
                        f"(score: {score:.1f}, time: {search_time_ms}ms)"
                    )
                else:
                    result = {
                        "matched": False,
                        "message": f"Không tìm thấy món ăn tương tự '{food_name}' (threshold: {threshold})",
                        "suggestion": "Thử giảm threshold hoặc tìm với tên khác",
                        "search_time_ms": search_time_ms
                    }
                    
                    # Log search failure
                    SearchLogger.log_search(
                        query=food_name,
                        matched=False,
                        search_time_ms=search_time_ms,
                        threshold=threshold
                    )
                    
                    logger.info(f"⚠️ No match found (time: {search_time_ms}ms)")
                
                return result
        
        except Exception as e:
            search_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"❌ Search error: {str(e)}", exc_info=True)
            
            return {
                "matched": False,
                "error": str(e),
                "search_time_ms": search_time_ms
            }
    
    def get_food_by_id(
        self,
        db: Session,
        food_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Lấy thông tin món ăn theo ID
        
        Args:
            db: Database session
            food_id: UUID của món ăn
        
        Returns:
            Food dict hoặc None
        """
        try:
            from uuid import UUID
            
            food = db.query(Food).filter(
                Food.food_id == UUID(food_id),
                Food.is_deleted == False
            ).first()
            
            if food:
                return food.to_dict()
            else:
                return None
        
        except Exception as e:
            logger.error(f"❌ Error getting food by ID: {str(e)}")
            return None
    
    def calculate_nutrition_for_portion(
        self,
        food_dict: Dict[str, Any],
        portion_grams: float
    ) -> Dict[str, Any]:
        """
        Tính nutrition cho portion cụ thể
        
        Args:
            food_dict: Food data (từ to_dict())
            portion_grams: Khối lượng món ăn (grams)
        
        Returns:
            Nutrition values scaled cho portion
        """
        try:
            nutrition = food_dict["nutrition"]
            serving_size = nutrition.get("serving_size_g", 100)
            
            # Scale factor
            scale = portion_grams / serving_size
            
            # Calculate scaled nutrition
            scaled_nutrition = {
                "portion_grams": round(portion_grams, 1),
                "calories": round(nutrition["calories_per_100g"] * scale, 1),
                "protein_g": round(nutrition["protein_per_100g"] * scale, 1),
                "carbs_g": round(nutrition["carbs_per_100g"] * scale, 1),
                "fat_g": round(nutrition["fat_per_100g"] * scale, 1),
                "fiber_g": round(nutrition["fiber_per_100g"] * scale, 1),
                "sugar_g": round(nutrition["sugar_per_100g"] * scale, 1),
                "sodium_mg": round(nutrition["sodium_per_100g"] * scale, 1)
            }
            
            return scaled_nutrition
        
        except Exception as e:
            logger.error(f"❌ Error calculating nutrition: {str(e)}")
            return {}


# Singleton instance
nutrition_service = NutritionService()