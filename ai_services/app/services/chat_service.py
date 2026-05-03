"""
Chat Service - RAG Pipeline
Retrieval-Augmented Generation for nutrition Q&A
"""

from google import genai
from google.genai import types
from typing import Dict, Optional, List
import logging
import time
import re
import inspect

from app.config import settings
from app.services.retrieval_service import RetrievalService
from app.prompts.chatbot_prompt import build_chatbot_prompt, build_prompt_with_vision
from app.services.function_calling_tools import FunctionCallingTools, TOOLS

logger = logging.getLogger(__name__)


class ChatService:
    """Service for answering nutrition questions using RAG"""
    
    @staticmethod
    def preprocess_query(query: str) -> str:
        """
        Extract key terms from Vietnamese question for better semantic search
        
        Removes question words and patterns to improve search relevance.
        
        Examples:
            "Thịt bò có bao nhiêu calories?" → "Thịt bò calories"
            "Cam có chứa vitamin C không?" → "Cam vitamin C"
            "Cơm trắng carbs bao nhiêu?" → "Cơm trắng carbs"
            "Gợi ý bữa ăn sáng" → "bánh mì xôi phở bún bữa sáng"
            "Món ăn giảm cân" → "salad rau ít calories"
        
        Args:
            query: Original Vietnamese question
        
        Returns:
            Processed query with key terms only
        """
        processed = query.lower().strip()
        
        # === Handle "gợi ý" patterns ===
        breakfast_foods = "bánh mì xôi phở bún cháo bánh bao bánh cuốn mì"
        lunch_dinner_foods = "cơm phở bún miến mì bánh tráng"

        # Check for breakfast
        if 'sáng' in processed:
            processed = re.sub(r'gợi ý|bữa', '', processed) + ' ' + breakfast_foods
        # Check for lunch
        elif 'trưa' in processed:
            processed = re.sub(r'gợi ý|bữa', '', processed) + ' ' + lunch_dinner_foods
        # Check for dinner
        elif 'tối' in processed:
            processed = re.sub(r'gợi ý|bữa', '', processed) + ' ' + lunch_dinner_foods
        elif 'gợi ý' in processed:
            # "gợi ý món ăn nào", "món ăn gì" - keep the food-related part
            processed = re.sub(r'gợi ý|món\s*ăn\s*nào|món\s*ăn\s*gì|nào|gì', '', processed)
        
        # === Handle "nấu với" patterns ===
        # "nấu với thịt bò" → "thịt bò"
        if 'nấu với' in processed:
            processed = re.sub(r'nấu\s*với\s*', '', processed)
        
        # === Handle nutrition/goals patterns ===
        if 'giảm cân' in processed:
            processed = re.sub(r'giảm\s*cân', 'ít calories salad rau xanh protein', processed)
        if 'tăng cơ' in processed or 'tăng cân' in processed:
            processed = re.sub(r'tăng\s*cơ|tăng\s*cân', 'protein cao calories cao', processed)
        
        # === "có chứa X không" → "X" ===
        processed = re.sub(r'có\s+chứa\s+([\w\s]+?)\s+không', r'\1', processed)
        
        # === Remove common question words ===
        patterns = [
            r'\bcó bao nhiêu\b', r'\bbao nhiêu\b', r'\bchứa\b',
            r'\bcó\b', r'\bkhông\b', r'\bgiá trị\b', r'\blượng\b', r'\bhàm lượng\b',
            r'\bcho\s*tôi\b', r'\blà\s*món\s*gì\b', r'\blà\s*gì\b', r'\bở\s*đâu\b'
        ]
        for pattern in patterns:
            processed = re.sub(pattern, '', processed)
        
        # === Remove punctuation and clean whitespace ===
        processed = re.sub(r'[?!,.]', '', processed)
        processed = ' '.join(processed.split())
        
        return processed.strip()
    
    def __init__(self, api_key: str, retrieval_service: RetrievalService):
        """
        Initialize chat service
        
        Args:
            api_key: Google AI API key
            retrieval_service: RetrievalService for document retrieval
        """
        self.client = genai.Client(api_key=api_key)
        chat_model_name = settings.GEMINI_MODEL
        self.model_name = chat_model_name
        self.retrieval = retrieval_service
        self.function_tools = FunctionCallingTools(retrieval_service)
        
        logger.info(
            f"✅ ChatService initialized with {chat_model_name} + 9 Function Calling tools (⭐ Updated - Task 11)"
        )
    
    async def answer_question(
        self,
        question: str,
        user_context: Optional[Dict] = None,
        top_k: int = 3,
        score_threshold: float = 0.20,
        conversation_context: Optional[str] = None
    ) -> Dict:
        """
        Answer nutrition question using RAG pipeline (⭐ UPDATED - Task 9!)
        
        Pipeline:
        1. Retrieve relevant documents from knowledge base
        2. Build prompt with context, user info, and conversation history
        3. Generate answer using Gemini
        
        Args:
            question: User's nutrition question
            user_context: Optional user info (weight, goals, etc.)
            top_k: Number of documents to retrieve
            score_threshold: Minimum relevance score for documents
            conversation_context: Optional conversation history (NEW!)
        
        Returns:
            Dict with keys:
                - answer: Generated answer text
                - sources: List of source documents used
                - processing_time_ms: Total processing time
                - retrieved_docs: Number of docs retrieved
        
        Example:
            >>> chat = ChatService(api_key="...", retrieval=...)
            >>> result = await chat.answer_question("Phở bò có bao nhiêu calo?")
            >>> print(result['answer'])
            'Một tô phở bò (500g) có khoảng 450-550 calories...'
        """
        start_time = time.time()
        
        if not question or not question.strip():
            logger.warning("Empty question provided")
            return {
                "answer": "Xin lỗi, tôi cần một câu hỏi cụ thể để trả lời.",
                "sources": [],
                "processing_time_ms": 0,
                "retrieved_docs": 0
            }
        
        logger.info(f"🤖 Processing question: {question[:100]}...")
        if conversation_context:
            logger.debug(f"   With conversation context ({len(conversation_context)} chars)")
        
        try:
            # Step 1: Preprocess query for better search
            processed_query = self.preprocess_query(question)
            if processed_query != question:
                logger.debug(f"   Processed: {processed_query}")
            
            # Step 2: Retrieve relevant documents
            logger.debug(f"📚 Retrieving top {top_k} documents (threshold: {score_threshold})...")
            docs = self.retrieval.search(
                query=processed_query,
                top_k=top_k,
                score_threshold=score_threshold
            )
            
            logger.info(f"   Retrieved {len(docs)} relevant documents")
            
            # Step 3: Build prompt with context and conversation history
            prompt = build_chatbot_prompt(
                question=question,
                context_docs=docs,
                user_context=user_context,
                conversation_context=conversation_context  # NEW!
            )
            
            logger.debug(f"   Prompt length: {len(prompt)} chars")
            
            # Step 3: Generate answer
            logger.debug("🧠 Generating answer with Gemini...")
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
                config=types.GenerateContentConfig(
                    temperature=settings.GEMINI_TEMPERATURE,
                    max_output_tokens=2048,  # Increased for full answers
                    top_p=0.95,
                    top_k=40
                )
            )
            
            answer_text = response.text
            
            # Calculate processing time
            processing_time = int((time.time() - start_time) * 1000)
            
            logger.info(f"✅ Answer generated in {processing_time}ms")
            
            return {
                "answer": answer_text,
                "sources": [
                    {
                        "title": doc["title"],
                        "relevance_score": doc["score"]
                    }
                    for doc in docs
                ],
                "processing_time_ms": processing_time,
                "retrieved_docs": len(docs)
            }
            
        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            logger.error(f"❌ Failed to answer question: {str(e)}")
            
            # Graceful fallback
            return {
                "answer": f"Xin lỗi, tôi gặp vấn đề khi xử lý câu hỏi của bạn. Lỗi: {str(e)}",
                "sources": [],
                "processing_time_ms": processing_time,
                "retrieved_docs": 0,
                "error": str(e)
            }
    
    def answer_question_sync(
        self,
        question: str,
        user_context: Optional[Dict] = None,
        top_k: int = 3,
        score_threshold: float = 0.5
    ) -> Dict:
        """
        Synchronous version of answer_question (for non-async contexts)
        
        Args:
            Same as answer_question
        
        Returns:
            Same as answer_question
        """
        start_time = time.time()
        
        if not question or not question.strip():
            logger.warning("Empty question provided")
            return {
                "answer": "Xin lỗi, tôi cần một câu hỏi cụ thể để trả lời.",
                "sources": [],
                "processing_time_ms": 0,
                "retrieved_docs": 0
            }
        
        logger.info(f"🤖 Processing question: {question[:100]}...")
        
        try:
            # Step 1: Retrieve
            docs = self.retrieval.search(
                query=question,
                top_k=top_k,
                score_threshold=score_threshold
            )
            
            logger.info(f"   Retrieved {len(docs)} relevant documents")
            
            # Step 2: Build prompt
            prompt = build_chatbot_prompt(
                question=question,
                context_docs=docs,
                user_context=user_context
            )
            
            # Step 3: Generate
            logger.debug("🧠 Generating answer with Gemini...")
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
                config=types.GenerateContentConfig(
                    temperature=settings.GEMINI_TEMPERATURE,
                    max_output_tokens=2048,  # Increased for full answers
                    top_p=0.95,
                    top_k=40
                )
            )
            
            answer_text = response.text
            processing_time = int((time.time() - start_time) * 1000)
            
            logger.info(f"✅ Answer generated in {processing_time}ms")
            
            return {
                "answer": answer_text,
                "sources": [
                    {
                        "title": doc["title"],
                        "relevance_score": doc["score"]
                    }
                    for doc in docs
                ],
                "processing_time_ms": processing_time,
                "retrieved_docs": len(docs)
            }
            
        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            logger.error(f"❌ Failed to answer question: {str(e)}")
            
            return {
                "answer": f"Xin lỗi, tôi gặp vấn đề khi xử lý câu hỏi của bạn. Lỗi: {str(e)}",
                "sources": [],
                "processing_time_ms": processing_time,
                "retrieved_docs": 0,
                "error": str(e)
            }
    
    async def answer_with_functions(
        self,
        query: str,
        user_context: Optional[Dict] = None,
        user_id: Optional[str] = None,
        jwt_token: Optional[str] = None
    ) -> Dict:
        """
        Answer question with Function Calling capabilities
        
        Workflow:
        1. Send query to Gemini with all tools available
        2. If Gemini calls a function, execute it
        3. Send results back to Gemini for final answer
        4. Return natural language response
        
        Args:
            query: User's question or command
            user_context: Optional user info (weight, goals, etc.)
            user_id: User ID for backend API calls
        
        Returns:
            Dict with keys:
                - answer: Generated answer text
                - function_called: Name of function called (if any)
                - function_result: Result from function execution
                - processing_time_ms: Total processing time
        
        Example:
            >>> chat = ChatService(api_key="...", retrieval=...)
            >>> result = await chat.answer_with_functions("Find high protein foods")
            >>> print(result['answer'])
            'Here are some high-protein foods: Rabbit Loin (24.5g)...'
        """
        start_time = time.time()
        
        if not query or not query.strip():
            logger.warning("Empty query provided")
            return {
                "answer": "Xin lỗi, tôi cần một câu hỏi cụ thể để trả lời.",
                "function_called": None,
                "function_result": None,
                "processing_time_ms": 0
            }
        
        logger.info(f"🤖 Function Calling Query: {query[:100]}...")
        
        try:
            # Build tools list from TOOLS definition
            tools = []
            for func_decl in TOOLS.get("function_declarations", []):
                tools.append(types.Tool(function_declarations=[func_decl]))
            
            # Step 1: Send query to Gemini with tools
            # Enhanced system instruction for better Vietnamese query understanding
            system_instr = """Bạn là trợ lý dinh dưỡng NutriAI. Trả lời bằng tiếng Việt.

KHI TÌM KIẾM MÓN ĂN:
- "Gợi ý bữa sáng" → search_food với criteria là các món sáng phổ biến: "bánh mì, xôi, phở, bún, cháo"
- "Món ăn nhiều protein" → search_food với criteria là "protein cao"
- "Món giảm cân" → search_food với criteria là "ít calories, rau, salad"
- "Nấu với thịt bò" → search_food với criteria là "thịt bò"
- LUÔN tìm TÊN MÓN CỤ THỂ, không tìm cụm từ trừu tượng như "bữa sáng", "dinh dưỡng"

HÃY SUY NGHĨ: User muốn ăn gì? Tìm tên món cụ thể phù hợp."""

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[types.Content(role="user", parts=[types.Part(text=query)])],
                config=types.GenerateContentConfig(
                    temperature=settings.GEMINI_TEMPERATURE,
                    max_output_tokens=min(1000, settings.GEMINI_MAX_TOKENS),
                    tools=tools,
                    system_instruction=types.Content(parts=[types.Part(text=system_instr)])
                )
            )
            
            # Step 2: Check if function was called
            function_called = None
            function_result = None
            fn_call = None
            
            # Check for function calls in response
            for candidate in response.candidates:
                for part in candidate.content.parts:
                    if part.function_call:
                        fn_call = part.function_call
                        function_called = fn_call.name
                        fn_args = {k: v for k, v in fn_call.args.items()}
                        
                        logger.info(f"   🔧 Function Called: {function_called}()")
                        logger.debug(f"   Arguments: {fn_args}")
                        
                        # Step 3: Execute the function
                        function_map = self.function_tools.get_function_map()
                        
                        if function_called in function_map:
                            func = function_map[function_called]
                            
                            # Add user_id / jwt token to args if function accepts it
                            sig = inspect.signature(func)
                            if 'user_id' in sig.parameters:
                                fn_args['user_id'] = user_id
                            if 'jwt_token' in sig.parameters:
                                fn_args['jwt_token'] = jwt_token

                            # Call async or sync function
                            if inspect.iscoroutinefunction(func):
                                function_result = await func(**fn_args)
                            else:
                                function_result = func(**fn_args)
                            
                            logger.info(f"   ✅ Function executed: {function_result.get('success', 'N/A')}")
                            
                            # Step 4: Send results back to Gemini for final answer
                            # The original fn_call already has thought_signature from the model
                            # We need to use Part with thought=True for tool calls
                            thought_part = types.Part(
                                function_call=fn_call,
                                thought=True
                            )
                            
                            # Enhanced system instruction for second response
                            second_system_instr = """Bạn là trợ lý dinh dưỡng NutriAI. 
TRẢ LỜI BẰNG TIẾNG VIỆT TỰ NHIÊN.
TRẢ LỜI ĐẦY ĐỦ, không cắt ngắn.
KHÔNG viết internal thoughts, reasoning, hay meta-comments.
Chỉ viết câu trả lời TRỰC TIẾP cho người dùng."""
                            
                            response = self.client.models.generate_content(
                                model=self.model_name,
                                contents=[
                                    types.Content(role="user", parts=[types.Part(text=query)]),
                                    types.Content(role="model", parts=[thought_part]),
                                    types.Content(role="user", parts=[
                                        types.Part.from_function_response(
                                            name=function_called,
                                            response=function_result
                                        )
                                    ])
                                ],
                                config=types.GenerateContentConfig(
                                    temperature=settings.GEMINI_TEMPERATURE,
                                    max_output_tokens=2048,  # Increased for full answers
                                    tools=tools,
                                    system_instruction=types.Content(parts=[types.Part(text=second_system_instr)])
                                )
                            )
                        else:
                            logger.error(f"❌ Unknown function: {function_called}")
                            function_result = {"success": False, "error": f"Unknown function: {function_called}"}
                        
                        break
                if function_called:
                    break
            
            # Extract final answer
            answer_text = ""
            try:
                if hasattr(response, 'text') and response.text:
                    answer_text = response.text
                else:
                    for candidate in response.candidates:
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                answer_text += part.text
                
                if not answer_text:
                    # Gemini did not produce a text response - format from function_result
                    if function_called and function_result:
                        answer_text = self._format_function_result_as_answer(
                            function_called, function_result
                        )
                    else:
                        answer_text = "Tôi đã nhận được yêu cầu nhưng chưa thể tạo câu trả lời chi tiết. Bạn có thể thử hỏi theo cách khác không?"
            except Exception as e:
                logger.warning(f"⚠️  Failed to extract response text: {str(e)}")
                # Format from function_result on error
                if function_called and function_result:
                    answer_text = self._format_function_result_as_answer(
                        function_called, function_result
                    )
                else:
                    answer_text = "Đã xảy ra lỗi khi xử lý phản hồi. Vui lòng thử lại."
            
            processing_time = int((time.time() - start_time) * 1000)
            logger.info(f"✅ Answer generated in {processing_time}ms")
            
            return {
                "answer": answer_text,
                "function_called": function_called,
                "function_result": function_result,
                "processing_time_ms": processing_time
            }
            
        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            logger.error(f"❌ Failed to process with functions: {str(e)}")
            
            return {
                "answer": f"Xin lỗi, tôi gặp vấn đề khi xử lý câu hỏi của bạn. Lỗi: {str(e)}",
                "function_called": None,
                "function_result": None,
                "processing_time_ms": processing_time,
                "error": str(e)
            }
    
    async def answer_with_vision(
        self,
        question: str,
        vision_context: Dict,
        user_context: Optional[Dict] = None,
        top_k: int = 2,
        score_threshold: float = 0.30
    ) -> Dict:
        """
        Answer question about food from vision analysis (⭐ NEW - Task 8!)
        
        Workflow:
        1. User uploads image → Vision identifies food
        2. User asks follow-up question → Uses vision context + RAG
        3. Generate answer combining both sources
        
        Args:
            question: User's question about the analyzed food
            vision_context: Vision analysis result from /vision/analyze
            user_context: Optional user info (weight, goals, etc.)
            top_k: Number of additional documents to retrieve (default: 2)
            score_threshold: Lower threshold since vision provides main context
        
        Returns:
            Dict with keys:
                - answer: Generated answer text
                - vision_food: Food name from vision
                - sources: Additional RAG sources
                - processing_time_ms: Total processing time
        
        Example:
            >>> vision_result = {"food_name": "Phở bò", "database_match": {...}}
            >>> result = await chat.answer_with_vision("Bao nhiêu calo?", vision_result)
            >>> print(result['answer'])
            'Phở bò có khoảng 450 calories cho một tô vừa (500g)...'
        """
        start_time = time.time()
        
        if not question or not question.strip():
            logger.warning("Empty question provided")
            return {
                "answer": "Xin lỗi, tôi cần một câu hỏi cụ thể để trả lời.",
                "vision_food": vision_context.get('food_name', 'N/A'),
                "sources": [],
                "processing_time_ms": 0
            }
        
        logger.info(f"🖼️  Processing question with vision context: {question[:100]}...")
        logger.info(f"   Vision food: {vision_context.get('food_name', 'N/A')}")
        
        try:
            # Step 1: Get food name from vision for additional RAG search
            food_name = vision_context.get('food_name', '')
            
            # Step 2: Retrieve additional documents (optional, lower priority)
            # Vision already provides main info, RAG supplements with details
            docs = []
            if food_name:
                processed_query = self.preprocess_query(f"{food_name} {question}")
                logger.debug(f"📚 Retrieving additional context for: {processed_query}")
                
                docs = self.retrieval.search(
                    query=processed_query,
                    top_k=top_k,
                    score_threshold=score_threshold
                )
                
                logger.info(f"   Retrieved {len(docs)} supplementary documents")
            
            # Step 3: Build prompt with vision context
            prompt = build_prompt_with_vision(
                question=question,
                vision_context=vision_context,
                context_docs=docs,
                user_context=user_context
            )
            
            logger.debug(f"   Prompt length: {len(prompt)} chars")
            
            # Step 4: Generate answer
            logger.debug("🧠 Generating answer with Gemini (vision mode)...")
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
                config=types.GenerateContentConfig(
                    temperature=settings.GEMINI_TEMPERATURE,
                    max_output_tokens=2048,  # Increased for full answers
                    top_p=0.95,
                    top_k=40
                )
            )
            
            answer_text = response.text
            
            # Calculate processing time
            processing_time = int((time.time() - start_time) * 1000)
            
            logger.info(f"✅ Answer with vision generated in {processing_time}ms")
            
            return {
                "answer": answer_text,
                "vision_food": food_name,
                "sources": [
                    {
                        "title": doc["title"],
                        "relevance_score": doc["score"]
                    }
                    for doc in docs
                ],
                "processing_time_ms": processing_time,
                "retrieved_docs": len(docs)
            }
            
        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            logger.error(f"❌ Failed to answer with vision: {str(e)}")
            
            # Graceful fallback
            return {
                "answer": f"Xin lỗi, tôi gặp vấn đề khi xử lý câu hỏi của bạn. Lỗi: {str(e)}",
                "vision_food": vision_context.get('food_name', 'N/A'),
                "sources": [],
                "processing_time_ms": processing_time,
                "error": str(e)
            }

    def _format_function_result_as_answer(
        self,
        function_name: str,
        result: Dict
    ) -> str:
        """
        Format function execution result into a natural language answer.
        
        This ensures that even when Gemini doesn't produce a good text response,
        the user still gets meaningful information from the function execution.
        
        Args:
            function_name: Name of the function that was called
            result: Result dictionary from the function execution
        
        Returns:
            Formatted answer string in Vietnamese
        """
        if not result:
            return "Không có kết quả từ chức năng này."
        
        success = result.get("success", False)
        if not success:
            error_msg = result.get("error", "Lỗi không xác định")
            return f"Xin lỗi, đã xảy ra lỗi: {error_msg}"
        
        # Route to specific formatter based on function name
        formatter_map = {
            "search_food": self._format_search_food_result,
            "log_food": self._format_log_food_result,
            "find_alternatives": self._format_find_alternatives_result,
            "adjust_goal": self._format_adjust_goal_result,
            "regenerate_meal_plan": self._format_meal_plan_result,
            "get_progress_insight": self._format_progress_insight_result,
            "get_weekly_insights": self._format_weekly_insights_result,
            "get_goal_analysis": self._format_goal_analysis_result,
            "get_nutrition_trends": self._format_nutrition_trends_result,
        }
        
        formatter = formatter_map.get(function_name)
        if formatter:
            return formatter(result)
        
        # Generic formatter for unknown functions
        return self._format_generic_result(result)
    
    def _format_search_food_result(self, result: Dict) -> str:
        """Format search_food result into natural language"""
        foods = result.get("results", [])
        count = result.get("count", 0)
        
        if count == 0:
            return "Không tìm thấy món ăn nào phù hợp với từ khóa của bạn."
        
        lines = [f"Tôi tìm thấy {count} kết quả:\n"]
        for i, food in enumerate(foods[:5], 1):
            title = food.get("title", "Không có tên")
            content = food.get("content", "")
            # Extract first 150 chars of content
            snippet = content[:150] + "..." if len(content) > 150 else content
            lines.append(f"{i}. **{title}**")
            if snippet:
                lines.append(f"   {snippet}")
        
        return "\n".join(lines)
    
    def _format_log_food_result(self, result: Dict) -> str:
        """Format log_food result into natural language"""
        message = result.get("message", "")
        logged_item = result.get("logged_item", {})
        
        answer_parts = []
        if message:
            answer_parts.append(message)
        
        # Add nutrition info if available
        if logged_item:
            nutrition = logged_item.get("nutrition", {})
            if nutrition:
                cal = nutrition.get("calories", 0)
                protein = nutrition.get("protein_g", 0)
                carbs = nutrition.get("carbs_g", 0)
                fat = nutrition.get("fat_g", 0)
                answer_parts.append(
                    f"\n📊 Giá trị dinh dưỡng: {cal} kcal, "
                    f"Protein: {protein}g, Carbs: {carbs}g, Fat: {fat}g"
                )
        
        return "\n".join(answer_parts) if answer_parts else "Đã ghi nhận thành công!"
    
    def _format_find_alternatives_result(self, result: Dict) -> str:
        """Format find_alternatives result into natural language"""
        original = result.get("original_food", "")
        criteria = result.get("criteria", "")
        alternatives = result.get("alternatives", [])
        count = result.get("count", 0)
        
        if count == 0:
            return f"Không tìm thấy alternatives cho '{original}' phù hợp với '{criteria}'."
        
        lines = [f"🥗 **Alternatives cho '{original}'** ({criteria}):\n"]
        for i, alt in enumerate(alternatives[:5], 1):
            name = alt.get("name", "Không có tên")
            info = alt.get("info", "")[:100]
            lines.append(f"{i}. **{name}**")
            if info:
                lines.append(f"   {info}...")
        
        return "\n".join(lines)
    
    def _format_adjust_goal_result(self, result: Dict) -> str:
        """Format adjust_goal result into natural language"""
        message = result.get("message", "")
        updated_goal = result.get("updated_goal", {})
        
        answer = message if message else "Đã cập nhật mục tiêu thành công!"
        
        if updated_goal:
            goal_type = updated_goal.get("goal_type", "")
            target = updated_goal.get("target_value", "")
            if goal_type and target:
                answer += f"\n📋 Mục tiêu mới: {goal_type} = {target}"
        
        return answer
    
    def _format_meal_plan_result(self, result: Dict) -> str:
        """Format regenerate_meal_plan result into natural language"""
        plan = result.get("plan", {})
        message = result.get("message", "")
        
        if message:
            return message
        
        days = plan.get("days", 0)
        preferences = plan.get("preferences", "")
        
        return (
            f"✅ Đã tạo meal plan cho {days} ngày"
            + (f" với preferences: {preferences}" if preferences else "")
        )
    
    def _format_progress_insight_result(self, result: Dict) -> str:
        """Format get_progress_insight result into natural language"""
        insights = result.get("insights", {})
        timeframe = result.get("timeframe", "")
        
        weekly_summary = insights.get("weekly_summary", {})
        if weekly_summary:
            avg_cal = weekly_summary.get("average_calories", 0)
            total_days = weekly_summary.get("total_days", 0)
            
            return (
                f"📊 **Tiến độ {timeframe}:**\n"
                f"- Trung bình calories/ngày: {avg_cal} kcal\n"
                f"- Số ngày đã ghi nhận: {total_days}"
            )
        
        return f"📊 Đã lấy thông tin tiến độ cho {timeframe}"
    
    def _format_weekly_insights_result(self, result: Dict) -> str:
        """Format get_weekly_insights result into natural language"""
        summary = result.get("summary", "")
        highlights = result.get("highlights", [])
        concerns = result.get("concerns", [])
        recommendations = result.get("recommendations", [])
        
        lines = []
        
        if summary:
            lines.append(f"📝 **Tóm tắt tuần qua:**\n{summary}\n")
        
        if highlights:
            lines.append("✨ **Điểm sáng:**")
            for h in highlights[:3]:
                lines.append(f"   • {h}")
            lines.append("")
        
        if concerns:
            lines.append("⚠️ **Cần lưu ý:**")
            for c in concerns[:3]:
                lines.append(f"   • {c}")
            lines.append("")
        
        if recommendations:
            lines.append("💡 **Khuyến nghị:**")
            for r in recommendations[:3]:
                lines.append(f"   • {r}")
        
        return "\n".join(lines) if lines else "Không có dữ liệu để phân tích tuần này."
    
    def _format_goal_analysis_result(self, result: Dict) -> str:
        """Format get_goal_analysis result into natural language"""
        status = result.get("status_message", "")
        assessment = result.get("progress_assessment", "")
        recommendations = result.get("recommendations", [])
        motivation = result.get("motivation", "")
        
        lines = []
        
        if status:
            lines.append(f"🎯 {status}\n")
        
        if assessment:
            lines.append(assessment)
            lines.append("")
        
        if recommendations:
            lines.append("💡 **Gợi ý:**")
            for r in recommendations[:3]:
                lines.append(f"   • {r}")
            lines.append("")
        
        if motivation:
            lines.append(f"🌟 {motivation}")
        
        return "\n".join(lines) if lines else "Không có thông tin về mục tiêu."
    
    def _format_nutrition_trends_result(self, result: Dict) -> str:
        """Format get_nutrition_trends result into natural language"""
        analysis = result.get("analysis", {})
        insights = result.get("insights", "")
        period = result.get("period_days", 30)
        
        lines = [f"📈 **Xu hướng dinh dưỡng {period} ngày:**\n"]
        
        if insights:
            lines.append(insights)
        
        message = analysis.get("message", "")
        if message:
            lines.append(f"\n{message}")
        
        return "\n".join(lines) if lines else f"Không có dữ liệu xu hướng cho {period} ngày."
    
    def _format_generic_result(self, result: Dict) -> str:
        """Generic formatter for unknown function results"""
        # Try to extract meaningful info from the result
        if "message" in result:
            return result["message"]
        if "data" in result:
            return str(result["data"])
        
        # Last resort: pretty print the result
        import json
        try:
            return json.dumps(result, ensure_ascii=False, indent=2)[:500]
        except:
            return str(result)[:500]


def get_chat_service(
    api_key: str,
    retrieval_service: RetrievalService
) -> ChatService:
    """
    Factory function to get ChatService instance
    
    Args:
        api_key: Google AI API key
        retrieval_service: Configured RetrievalService
    
    Returns:
        Configured ChatService instance
    """
    return ChatService(api_key, retrieval_service)
