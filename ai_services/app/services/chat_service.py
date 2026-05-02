"""
Chat Service - RAG Pipeline
Retrieval-Augmented Generation for nutrition Q&A
"""

import google.generativeai as genai
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
        
        Args:
            query: Original Vietnamese question
        
        Returns:
            Processed query with key terms only
        """
        processed = query
        
        # "có chứa X không" → "X"
        processed = re.sub(r'có\s+chứa\s+([\w\s]+?)\s+không', r'\1', processed)
        
        # Remove common question words
        patterns = [
            r'\bcó bao nhiêu\b', r'\bbao nhiêu\b', r'\bchứa\b',
            r'\bcó\b', r'\bkhông\b', r'\bgiá trị\b', r'\blượng\b', r'\bhàm lượng\b'
        ]
        for pattern in patterns:
            processed = re.sub(pattern, '', processed)
        
        # Remove punctuation and clean whitespace
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
        genai.configure(api_key=api_key)
        chat_model_name = settings.GEMINI_MODEL
        self.model = genai.GenerativeModel(model_name=chat_model_name)
        self.model_with_tools = genai.GenerativeModel(
            model_name=chat_model_name,
            tools=[TOOLS]
        )
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
        score_threshold: float = 0.35,
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
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": settings.GEMINI_TEMPERATURE,
                    "max_output_tokens": min(500, settings.GEMINI_MAX_TOKENS),
                    "top_p": 0.95,
                    "top_k": 40
                }
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
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": settings.GEMINI_TEMPERATURE,
                    "max_output_tokens": min(500, settings.GEMINI_MAX_TOKENS),
                    "top_p": 0.95,
                    "top_k": 40
                }
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
        1. Send query to Gemini with all 6 tools available
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
            # Step 1: Send query to Gemini with tools
            response = self.model_with_tools.generate_content(
                query,
                generation_config={
                    "temperature": settings.GEMINI_TEMPERATURE,
                    "max_output_tokens": min(1000, settings.GEMINI_MAX_TOKENS),
                    "top_p": 0.95,
                    "top_k": 40
                }
            )
            
            # Step 2: Check if function was called
            function_called = None
            function_result = None
            
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    fn_call = part.function_call
                    function_called = fn_call.name
                    fn_args = dict(fn_call.args)
                    
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
                        response = self.model_with_tools.generate_content(
                            [
                                {"role": "user", "parts": [{"text": query}]},
                                {
                                    "role": "model",
                                    "parts": [{"function_call": fn_call}]
                                },
                                {
                                    "role": "user",
                                    "parts": [{
                                        "function_response": {
                                            "name": function_called,
                                            "response": function_result
                                        }
                                    }]
                                }
                            ],
                            generation_config={
                                "temperature": settings.GEMINI_TEMPERATURE,
                                "max_output_tokens": min(1000, settings.GEMINI_MAX_TOKENS)
                            }
                        )
                    else:
                        logger.error(f"❌ Unknown function: {function_called}")
                        function_result = {"success": False, "error": f"Unknown function: {function_called}"}
                    
                    break
            
            # Extract final answer - safely handle both text and function_call responses
            answer_text = ""
            try:
                # Check if response has text parts
                if hasattr(response, 'text'):
                    answer_text = response.text
                elif hasattr(response, 'candidates') and response.candidates:
                    # Extract text from parts manually
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'text') and part.text:
                            answer_text += part.text
                
                # Fallback if no text found
                if not answer_text:
                    if function_called and function_result and function_result.get('success'):
                        answer_text = "Đã thực hiện xong!"
                    else:
                        answer_text = "Đã nhận được yêu cầu."
            except Exception as e:
                logger.warning(f"⚠️  Failed to extract response text: {str(e)}")
                answer_text = "Đã thực hiện xong!" if function_called else "Đã nhận được yêu cầu."
            
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
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": settings.GEMINI_TEMPERATURE,
                    "max_output_tokens": min(500, settings.GEMINI_MAX_TOKENS),
                    "top_p": 0.95,
                    "top_k": 40
                }
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
