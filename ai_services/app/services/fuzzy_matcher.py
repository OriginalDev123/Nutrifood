"""
Fuzzy Matching Service - Vietnamese Food Name Matching
FIXED VERSION với caching, type hints, và expand_query
"""

from rapidfuzz import fuzz, process
from typing import List, Tuple, Optional, TypeVar, Generic, Dict
import re
import unicodedata
import logging
import json
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

# Generic type for food objects
T = TypeVar('T')


def get_dynamic_threshold(query: str) -> int:
    """
    Calculate dynamic threshold based on query length
    
    Strategy:
    - Short queries (≤3 chars): High threshold (90) to avoid false positives
    - Medium queries (4-8 chars): Medium threshold (80)
    - Long queries (>8 chars): Lower threshold (70) for flexibility
    
    Args:
        query: Search query
    
    Returns:
        Threshold value (70-90)
    
    Examples:
        >>> get_dynamic_threshold("cá")
        90
        >>> get_dynamic_threshold("phở bò")
        80
        >>> get_dynamic_threshold("cơm tấm sườn bì chả")
        70
    """
    length = len(query.strip())
    
    if length <= 3:
        return 90  # Strict for short queries
    elif length <= 8:
        return 80  # Balanced
    else:
        return 70  # Relaxed for long queries


class SearchLogger:
    """
    Logger for tracking search queries and results
    Helps identify patterns, failures, and optimization opportunities
    """
    
    @staticmethod
    def log_search(
        query: str,
        matched: bool,
        similarity_score: Optional[float] = None,
        matched_name: Optional[str] = None,
        search_time_ms: Optional[int] = None,
        threshold: Optional[int] = None
    ):
        """
        Log search result in structured format
        
        Args:
            query: Original search query
            matched: Whether search found a match
            similarity_score: Match score (0-100)
            matched_name: Name of matched food
            search_time_ms: Search duration
            threshold: Threshold used
        """
        log_data = {
            "query": query,
            "matched": matched,
            "similarity_score": similarity_score,
            "matched_name": matched_name,
            "search_time_ms": search_time_ms,
            "threshold": threshold
        }
        
        if matched:
            logger.info(
                f"🔍 SEARCH SUCCESS: '{query}' → '{matched_name}' "
                f"(score: {similarity_score:.1f}, threshold: {threshold}, time: {search_time_ms}ms)"
            )
        else:
            logger.warning(
                f"🔍 SEARCH FAILED: '{query}' (threshold: {threshold}, time: {search_time_ms}ms) "
                f"- Consider adding synonyms or lowering threshold"
            )
        
        # Optional: Save to database for analytics
        # db.execute("INSERT INTO search_logs ...", log_data)


class VietnameseFoodMatcher:
    """
    Advanced fuzzy matching cho Vietnamese food names
    
    Features:
    - Vietnamese diacritics handling
    - Word order independence
    - Synonym expansion
    - Caching for performance
    
    Fixes from original:
    - ✅ Fixed type hints (any → TypeVar)
    - ✅ Added expand_query() method
    - ✅ Added caching with LRU
    - ✅ Added search_in_database() convenience method
    """
    
    def __init__(self):
        """Initialize matcher với caching và load synonyms từ JSON"""
        self._normalized_cache = {}
        self.SYNONYMS = self._load_synonyms()
        logger.info(f"✅ VietnameseFoodMatcher initialized with {len(self.SYNONYMS)} synonym entries")
    
    def _load_synonyms(self) -> Dict[str, List[str]]:
        """
        Load synonyms từ JSON file
        
        Returns:
        Flattened dict of {canonical: [synonyms]}
        """
        try:
            # Path to synonyms file
            synonyms_file = Path(__file__).parent.parent / "data" / "food_synonyms.json"
            
            if not synonyms_file.exists():
                logger.warning(f"⚠️ Synonyms file not found: {synonyms_file}. Using empty dict.")
                return {}
            
            with open(synonyms_file, 'r', encoding='utf-8') as f:
                synonyms_data = json.load(f)
            
            # Flatten nested structure: {category: {word: [synonyms]}} → {word: [synonyms]}
            flattened = {}
            for category, words in synonyms_data.items():
                for canonical, synonyms in words.items():
                    flattened[canonical] = synonyms
            
            logger.info(f"📚 Loaded {len(flattened)} synonym entries from {synonyms_file.name}")
            return flattened
            
        except Exception as e:
            logger.error(f"❌ Error loading synonyms: {str(e)}. Using empty dict.")
            return {}
    
    @staticmethod
    @lru_cache(maxsize=1000)
    def normalize(text: str) -> str:
        """
        Normalize Vietnamese text cho matching (với caching)
        
        Steps:
        1. Lowercase
        2. Remove extra whitespace
        3. Keep diacritics (better for Vietnamese)
        
        Args:
            text: Input text
        
        Returns:
            Normalized text
        """
        # Lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    @staticmethod
    @lru_cache(maxsize=1000)
    def remove_diacritics(text: str) -> str:
        """
        Remove Vietnamese diacritics (với caching)
        
        Example: "Phở bò" → "Pho bo"
        """
        # Normalize to NFD (decomposed form)
        nfd = unicodedata.normalize('NFD', text)
        
        # Remove combining characters (diacritics)
        without_diacritics = ''.join(
            char for char in nfd 
            if unicodedata.category(char) != 'Mn'
        )
        
        # Normalize back to NFC
        return unicodedata.normalize('NFC', without_diacritics)
    
    def expand_query(self, query: str) -> List[str]:
        """
        Expand query với synonyms để hỗ trợ English và Vietnamese
        
        Example:
            Input: "beef" → Output: ["beef", "bò", "thịt bò"]
            Input: "phở" → Output: ["phở", "pho"]
        
        Args:
            query: User's search query
        
        Returns:
            List of query variations (including original)
        """
        query_lower = query.lower()
        variations = [query]  # Always include original
        
        # Sort by length descending to match longer phrases first
        # Prevents "cá" from matching before "cá hồi"
        sorted_items = sorted(
            self.SYNONYMS.items(), 
            key=lambda x: len(x[0]), 
            reverse=True
        )
        
        # Check each synonym group
        for canonical, synonyms in sorted_items:
            canonical_lower = canonical.lower()
            
            # If query contains synonym, add canonical version
            for syn in synonyms:
                if syn in query_lower:
                    expanded = query_lower.replace(syn, canonical_lower)
                    if expanded not in variations:
                        variations.append(expanded)
            
            # If query contains canonical, add synonym versions
            if canonical_lower in query_lower:
                for syn in synonyms:
                    expanded = query_lower.replace(canonical_lower, syn)
                    if expanded not in variations:
                        variations.append(expanded)
        
        logger.debug(f"Query expanded: '{query}' → {len(variations)} variations")
        return variations
    
    def find_best_match(
        self,
        query: str,
        candidates: List[Tuple[str, T]],
        threshold: int = 80
    ) -> Optional[Tuple[T, float, str]]:
        """
        Find best matching food từ database
        
        Args:
            query: Food name từ AI (e.g., "Phở bò")
            candidates: List of (name, object) tuples từ database
            threshold: Minimum similarity score (0-100)
        
        Returns:
            (food_object, similarity_score, matched_name) hoặc None
        """
        
        if not candidates:
            return None
        
        # === STRATEGY 1: Exact Match (normalized) ===
        query_norm = self.normalize(query)
        
        for name, obj in candidates:
            if self.normalize(name) == query_norm:
                logger.info(f"✅ Exact match: '{query}' → '{name}'")
                return (obj, 100.0, name)
        
        # === STRATEGY 2: Expand Query & Fuzzy Match ===
        # Expand query với synonyms (English ↔ Vietnamese)
        query_variations = self.expand_query(query_norm)
        candidate_names = [name for name, _ in candidates]
        
        best_match = None
        best_score = 0
        
        for variation in query_variations:
            # Use token_sort_ratio for synonym expansion
            # More accurate than partial_ratio for avoiding false positives
            match = process.extractOne(
                variation,
                [self.normalize(name) for name in candidate_names],
                scorer=fuzz.token_sort_ratio
            )
            
            if match and match[1] > best_score:
                best_match = match
                best_score = match[1]
        
        if best_match and best_match[1] >= threshold:
            matched_idx = best_match[2]
            logger.info(
                f"✅ Fuzzy match: '{query}' → '{candidate_names[matched_idx]}' "
                f"(score: {best_match[1]})"
            )
            return (
                candidates[matched_idx][1],  # object
                best_match[1],                # score
                candidates[matched_idx][0]    # name
            )
            logger.info(
                f"✅ Token sort match: '{query}' → '{candidate_names[matched_idx]}' "
                f"(score: {best_match[1]})"
            )
            return (
                candidates[matched_idx][1],  # object
                best_match[1],                # score
                candidates[matched_idx][0]    # name
            )
        
        # === STRATEGY 3: Partial Ratio for Substring Matching ===
        # For queries like "cơm tấm" matching "Cơm tấm sườn bì chả"
        # Only use for queries >= 4 chars to avoid false positives
        if len(query_norm) >= 4:
            best_match = process.extractOne(
                query_norm,
                [self.normalize(name) for name in candidate_names],
                scorer=fuzz.partial_ratio
            )
            
            # Require higher threshold for partial matching
            partial_threshold = max(threshold, 85)
            
            if best_match and best_match[1] >= partial_threshold:
                matched_idx = best_match[2]
                logger.info(
                    f"✅ Partial match: '{query}' → '{candidate_names[matched_idx]}' "
                    f"(score: {best_match[1]})"
                )
                return (
                    candidates[matched_idx][1],
                    best_match[1],
                    candidates[matched_idx][0]
                )
        
        # === NO MATCH FOUND ===
        logger.warning(f"⚠️ No match found for: '{query}' (threshold: {threshold})")
        return None
    
    def get_top_matches(
        self,
        query: str,
        candidates: List[Tuple[str, T]],
        top_k: int = 3,
        threshold: int = 60
    ) -> List[Tuple[T, float, str]]:
        """
        Get top K matching foods (cho user confirmation UI)
        
        Returns:
            List of (food_object, similarity_score, matched_name)
        """
        
        if not candidates:
            return []
        
        query_norm = self.normalize(query)
        
        # Expand query
        query_variations = self.expand_query(query_norm)
        candidate_names = [name for name, _ in candidates]
        
        # Collect all matches from all variations
        all_matches = []
        
        for variation in query_variations:
            matches = process.extract(
                variation,
                [self.normalize(name) for name in candidate_names],
                scorer=fuzz.token_sort_ratio,
                limit=top_k * 2  # Get more than needed
            )
            all_matches.extend(matches)
        
        # Deduplicate và sort by score
        seen_indices = set()
        unique_matches = []
        
        for match_text, score, idx in sorted(all_matches, key=lambda x: x[1], reverse=True):
            if idx not in seen_indices and score >= threshold:
                seen_indices.add(idx)
                unique_matches.append((
                    candidates[idx][1],  # object
                    score,                # score
                    candidates[idx][0]    # name
                ))
                
                if len(unique_matches) >= top_k:
                    break
        
        logger.info(f"✅ Found {len(unique_matches)} top matches for '{query}'")
        return unique_matches
    
    def search_in_database(
        self,
        db,
        query: str,
        threshold: int = 80,
        return_top_k: bool = False,
        top_k: int = 3
    ) -> dict:
        """
        Convenience method: Search directly trong database
        
        Args:
            db: SQLAlchemy Session
            query: Search query
            threshold: Minimum similarity
            return_top_k: True = return top K, False = best match
            top_k: Number of results if return_top_k=True
        
        Returns:
            {
                "matched": bool,
                "food": dict (nếu best match),
                "candidates": list (nếu top_k)
            }
        """
        from app.database import Food
        
        # Query all active foods
        foods = db.query(Food).filter(
            Food.is_deleted == False
        ).all()
        
        if not foods:
            return {"matched": False, "error": "No foods in database"}
        
        # Prepare candidates
        candidates = [
            (f"{food.name_vi} / {food.name_en if food.name_en else ''}", food)
            for food in foods
        ]
        
        # Search
        if return_top_k:
            matches = self.get_top_matches(
                query, 
                candidates, 
                top_k=top_k, 
                threshold=threshold
            )
            
            return {
                "matched": len(matches) > 0,
                "candidates": [
                    {
                        "food": food.to_dict(),
                        "similarity_score": round(score, 1),
                        "matched_name": name
                    }
                    for food, score, name in matches
                ]
            }
        else:
            match = self.find_best_match(query, candidates, threshold=threshold)
            
            if match:
                food, score, name = match
                return {
                    "matched": True,
                    "food": food.to_dict(),
                    "similarity_score": round(score, 1),
                    "matched_name": name
                }
            else:
                return {"matched": False}


# Singleton instance
vietnamese_matcher = VietnameseFoodMatcher()