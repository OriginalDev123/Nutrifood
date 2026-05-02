"""
Chat Routes - RAG Chatbot Endpoint
API endpoints for nutrition Q&A chatbot
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
import logging
import os
import re

from app.config import settings
from app.services.chat_service import ChatService, get_chat_service
from app.services.retrieval_service import RetrievalService, get_retrieval_service
from app.services.local_embedding_service import get_local_embedding_service
from app.services.memory_service import get_memory_service, ConversationMemoryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chatbot"])

ACTION_QUERY_PATTERN = re.compile(
    r"(vừa ăn|đã ăn|ăn .*trưa|ăn .*sáng|ăn .*tối|uống|log|ghi lại|thêm vào bữa|"
    r"đổi mục tiêu|cập nhật mục tiêu|goal|tiến độ|how am i doing|progress|weekly summary|tổng kết tuần)",
    re.IGNORECASE,
)

# Global service instances (initialized on startup)
_chat_service: Optional[ChatService] = None
_retrieval_service: Optional[RetrievalService] = None


def get_services():
    """
    Dependency to get initialized services
    
    Returns:
        ChatService instance
    
    Raises:
        HTTPException: If services not initialized
    """
    global _chat_service
    
    if _chat_service is None:
        raise HTTPException(
            status_code=503,
            detail="Chat service not initialized. Please check server startup logs."
        )
    
    return _chat_service


def initialize_chat_services():
    """
    Initialize all chat-related services on app startup
    
    This should be called once during FastAPI startup event
    
    Raises:
        ValueError: If required env variables missing
    """
    global _chat_service, _retrieval_service
    
    try:
        logger.info("🚀 Initializing chat services...")
        
        # Get config from settings/env
        api_key = settings.GOOGLE_API_KEY
        qdrant_url = os.getenv("QDRANT_URL", "http://qdrant:6333")

        if not api_key:
            raise ValueError("GOOGLE_API_KEY not set")
        
        # Initialize services with local embeddings
        embedding_service = get_local_embedding_service()
        _retrieval_service = get_retrieval_service(qdrant_url, embedding_service)
        _chat_service = get_chat_service(api_key, _retrieval_service)
        
        # Ensure collection exists
        _retrieval_service.create_collection(recreate=False)
        
        logger.info("✅ Chat services initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize chat services: {str(e)}")
        raise


# Request/Response Models

class UserContext(BaseModel):
    """Optional user context for personalized answers"""
    user_id: Optional[str] = Field(None, description="User ID")
    current_weight: Optional[float] = Field(None, description="Current weight in kg")
    goal_type: Optional[str] = Field(None, description="lose_weight, maintain, gain_weight, build_muscle")
    daily_target: Optional[int] = Field(None, description="Daily calorie target")
    consumed_today: Optional[int] = Field(None, description="Calories consumed today")


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    question: str = Field(..., description="Nutrition question", min_length=1, max_length=500)
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity (⭐ NEW - Task 9!)")
    user_context: Optional[UserContext] = Field(None, description="Optional user context")
    top_k: Optional[int] = Field(3, description="Number of documents to retrieve", ge=1, le=10)
    score_threshold: Optional[float] = Field(0.35, description="Minimum relevance score (optimized for Vietnamese)", ge=0.0, le=1.0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "Phở bò có bao nhiêu calo?",
                "session_id": "optional-session-uuid",
                "user_context": {
                    "user_id": "123e4567-e89b-12d3-a456-426614174000",
                    "current_weight": 70,
                    "goal_type": "lose_weight",
                    "daily_target": 2000,
                    "consumed_today": 1200
                },
                "top_k": 3,
                "score_threshold": 0.5
            }
        }


class SourceDocument(BaseModel):
    """Source document info"""
    title: str = Field(..., description="Document title")
    relevance_score: float = Field(..., description="Relevance score (0-1)")


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    answer: str = Field(..., description="Generated answer")
    session_id: str = Field(..., description="Session ID for continuing conversation (⭐ NEW - Task 9!)")
    sources: List[SourceDocument] = Field(default=[], description="Source documents used")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    retrieved_docs: int = Field(..., description="Number of documents retrieved")
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "Một tô phở bò (500g) có khoảng 450-550 calories. Trong đó protein từ thịt bò khoảng 30g, carbs từ bánh phở khoảng 70g, và chất béo khoảng 15g. Lưu ý phở có hàm lượng sodium cao (1200mg = 50% khuyến nghị hàng ngày).",
                "session_id": "abc-123-def-456",
                "sources": [
                    {
                        "title": "Phở Bò Thông Tin Dinh Dưỡng",
                        "relevance_score": 0.92
                    }
                ],
                "processing_time_ms": 2345,
                "retrieved_docs": 3
            }
        }


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    collection_info: Dict


# Endpoints

@router.post("/ask", response_model=ChatResponse)
async def ask_question(
    request: ChatRequest,
    authorization: Optional[str] = Header(None),
    chat_service: ChatService = Depends(get_services)
):
    """
    Ask nutrition question using RAG chatbot with conversation memory (⭐ UPDATED - Task 9!)
    
    **How it works:**
    1. Gets or creates conversation session
    2. Retrieves relevant documents from knowledge base
    3. Includes conversation history in context
    4. Generates answer using Gemini
    5. Saves conversation to memory
    
    **Conversation Memory (NEW!):**
    - Include `session_id` to continue previous conversation
    - System remembers recent Q&A (up to 5 turns)
    - Omit `session_id` to start new conversation
    
    **User Context:**
    - Provide user context for personalized recommendations
    - System considers user's weight, goals, and daily targets
    
    **Example Questions:**
    - "Phở bò có bao nhiêu calo?"
    - "Và protein thì sao?" (follow-up with session_id)
    - "Tôi cần ăn bao nhiêu protein mỗi ngày?"
    
    Returns:
        ChatResponse with answer, session_id, sources, and processing time
    """
    try:
        logger.info(f"📨 Received question: {request.question[:100]}")
        
        # Get memory service
        memory_service = get_memory_service()
        
        # Get or create session
        user_id = request.user_context.user_id if request.user_context else None
        session = memory_service.get_or_create_session(
            session_id=request.session_id,
            user_id=user_id,
            metadata={"source": "chat_ask"}
        )
        session_id = session.session_id
        
        logger.info(f"💬 Using session: {session_id} (messages: {len(session.messages)})")
        
        # Add user question to memory
        memory_service.add_message(session_id, "user", request.question)
        
        # Get conversation context for prompt
        conversation_context = memory_service.get_conversation_context(
            session_id, max_turns=8
        )

        # Convert user_context to dict
        user_ctx = None
        if request.user_context:
            user_ctx = request.user_context.model_dump(exclude_none=True)

        jwt_token = None
        if authorization and authorization.startswith("Bearer "):
            jwt_token = authorization.replace("Bearer ", "")

        should_use_functions = bool(
            ACTION_QUERY_PATTERN.search(request.question)
            and user_id
            and jwt_token
        )

        # Process question with conversation context
        if should_use_functions:
            function_result = await chat_service.answer_with_functions(
                query=request.question,
                user_context=user_ctx,
                user_id=user_id,
                jwt_token=jwt_token
            )
            result = {
                "answer": function_result["answer"],
                "sources": [],
                "processing_time_ms": function_result["processing_time_ms"],
                "retrieved_docs": 0
            }
        else:
            result = await chat_service.answer_question(
                question=request.question,
                user_context=user_ctx,
                top_k=request.top_k,
                score_threshold=request.score_threshold,
                conversation_context=conversation_context
            )
        
        # Add assistant answer to memory
        memory_service.add_message(session_id, "assistant", result["answer"])
        
        # Format response
        response = ChatResponse(
            answer=result["answer"],
            session_id=session_id,  # NEW!
            sources=[
                SourceDocument(title=src["title"], relevance_score=src["relevance_score"])
                for src in result["sources"]
            ],
            processing_time_ms=result["processing_time_ms"],
            retrieved_docs=result["retrieved_docs"]
        )
        
        logger.info(
            f"✅ Question answered in {result['processing_time_ms']}ms "
            f"(session: {session_id}, turn: {len(session.messages)//2})"
        )
        return response
        
    except Exception as e:
        logger.error(f"❌ Error in /chat/ask: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process question: {str(e)}")


@router.post("/rag")
async def rag_quick_test(
    question: str,
    chat_service: ChatService = Depends(get_services)
):
    """
    Quick RAG test endpoint for frontend demos
    
    Simplified endpoint that takes just a question string.
    Uses optimized settings (threshold 0.35, top_k 3).
    
    Args:
        question: Nutrition question (Vietnamese or English)
    
    Returns:
        Dict with answer and search details
    
    Example:
        POST /chat/rag?question=Thịt bò có bao nhiêu calories?
        
        Response:
        {
            "question": "Thịt bò có bao nhiêu calories?",
            "processed_query": "Thịt bò calories",
            "answer": "Thịt bò có 250.0 kcal trên 100g.",
            "sources": ["Thịt bò - Beef"],
            "retrieved": 3
        }
    """
    try:
        if not question or not question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        # Preprocess query
        processed = chat_service.preprocess_query(question)
        
        # Get answer
        result = await chat_service.answer_question(
            question=question,
            user_context=None,
            top_k=3,
            score_threshold=0.35
        )
        
        return {
            "question": question,
            "processed_query": processed,
            "answer": result["answer"],
            "sources": [src["title"] for src in result["sources"]],
            "retrieved": result["retrieved_docs"],
            "processing_ms": result["processing_time_ms"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in /chat/rag: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class FunctionCallingRequest(BaseModel):
    """Request model for function calling endpoint"""
    query: str = Field(..., description="User query or command", min_length=1, max_length=500)
    user_context: Optional[UserContext] = Field(None, description="Optional user context")
    user_id: Optional[str] = Field(None, description="User ID for backend API calls")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Find high protein foods",
                "user_context": {
                    "user_id": "123",
                    "current_weight": 70,
                    "goal_type": "build_muscle"
                },
                "user_id": "123"
            }
        }


class FunctionCallingResponse(BaseModel):
    """Response model for function calling endpoint"""
    answer: str = Field(..., description="Natural language answer")
    function_called: Optional[str] = Field(None, description="Name of function called")
    function_result: Optional[Dict] = Field(None, description="Result from function execution")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "Here are some high-protein foods: Rabbit Loin (24.5g), Greek Yogurt (9.0g)...",
                "function_called": "search_food",
                "function_result": {
                    "success": True,
                    "results": [
                        {"title": "Rabbit Loin", "content": "...", "score": 0.95}
                    ],
                    "count": 2
                },
                "processing_time_ms": 1850
            }
        }


@router.post("/function-calling", response_model=FunctionCallingResponse)
async def chat_with_functions(
    request: FunctionCallingRequest,
    authorization: Optional[str] = Header(None),
    chat_service: ChatService = Depends(get_services)
):
    """
    Chat with Function Calling capabilities (⭐ UPDATED - Task 11: 9 tools!)
    
    **Intelligent Actions:**
    - 🔍 **search_food**: Search 839 foods/recipes by name, nutrient, or criteria
    - 📝 **log_food**: Log food intake to daily tracker
    - 🔄 **find_alternatives**: Find healthier food alternatives
    - 🎯 **adjust_goal**: Update nutrition goals (calories, protein, etc)
    - 📅 **regenerate_meal_plan**: Generate new meal plans
    - 📊 **get_progress_insight**: Get nutrition analytics and insights
    - 📊 **get_weekly_insights**: AI-powered weekly summary (⭐ NEW!)
    - 🎯 **get_goal_analysis**: AI-powered goal progress analysis (⭐ NEW!)
    - 📈 **get_nutrition_trends**: AI-powered trend analysis (⭐ NEW!)
    
    **How it works:**
    1. Gemini analyzes your query and detects intent
    2. If action needed, calls appropriate function with extracted parameters
    3. Executes function (searches database, logs food, etc)
    4. Returns natural language answer with results
    
    **Example Queries:**
    - "Find high protein foods" → Calls search_food()
    - "I just ate a bowl of phở" → Calls log_food()
    - "Find healthier alternatives to white rice" → Calls find_alternatives()
    - "Change my daily calorie target to 2000" → Calls adjust_goal()
    - "Create a 7-day meal plan" → Calls regenerate_meal_plan()
    - "How am I doing this week?" → Calls get_progress_insight()
    - "Tuần này mình ăn uống thế nào?" → Calls get_weekly_insights() (⭐ NEW!)
    - "Mục tiêu của mình tiến độ ra sao?" → Calls get_goal_analysis() (⭐ NEW!)
    - "Xu hướng 30 ngày qua?" → Calls get_nutrition_trends() (⭐ NEW!)
    
    **Multi-language Support:**
    - Vietnamese: "Tôi vừa ăn 2 tô phở lúc trưa"
    - English: "I had chicken rice for lunch"
    
    Returns:
        FunctionCallingResponse with answer, function details, and timing
    """
    try:
        logger.info(f"📨 Function Calling Query: {request.query[:100]}")
        
        # Convert user_context to dict
        user_ctx = None
        if request.user_context:
            user_ctx = request.user_context.model_dump(exclude_none=True)
        
        jwt_token = None
        if authorization and authorization.startswith("Bearer "):
            jwt_token = authorization.replace("Bearer ", "")

        # Process with function calling
        result = await chat_service.answer_with_functions(
            query=request.query,
            user_context=user_ctx,
            user_id=request.user_id,
            jwt_token=jwt_token
        )
        
        # Format response
        response = FunctionCallingResponse(
            answer=result["answer"],
            function_called=result.get("function_called"),
            function_result=result.get("function_result"),
            processing_time_ms=result["processing_time_ms"]
        )
        
        logger.info(f"✅ Query processed in {result['processing_time_ms']}ms")
        if result.get("function_called"):
            logger.info(f"   Function used: {result['function_called']}")
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Error in /chat/function-calling: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process query: {str(e)}")


# === Vision + Chat Integration (Task 8) ===

class VisionChatRequest(BaseModel):
    """Request model for vision-based chat (⭐ NEW!)"""
    question: str = Field(..., description="Question about the analyzed food", min_length=1, max_length=500)
    vision_context: Dict = Field(..., description="Vision analysis result from /vision/analyze")
    user_context: Optional[UserContext] = Field(None, description="Optional user context")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "Món này bao nhiêu calories?",
                "vision_context": {
                    "is_food": True,
                    "food_name": "Phở bò",
                    "components": ["bánh phở", "thịt bò", "nước dùng"],
                    "database_match": {
                        "item_type": "recipe",
                        "name_vi": "Phở bò",
                        "nutrition": {
                            "calories_per_serving": 450,
                            "protein_g": 25,
                            "carbs_g": 60,
                            "fat_g": 10
                        }
                    }
                },
                "user_context": {
                    "user_id": "123",
                    "current_weight": 70
                }
            }
        }


class VisionChatResponse(BaseModel):
    """Response model for vision-based chat"""
    answer: str = Field(..., description="Natural language answer")
    vision_food: str = Field(..., description="Food identified from vision")
    sources: List[str] = Field(default_factory=list, description="Additional RAG sources")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")


@router.post("/with-vision", response_model=VisionChatResponse)
async def chat_with_vision(
    request: VisionChatRequest,
    chat_service: ChatService = Depends(get_services)
):
    """
    Chat with vision context - Ask questions about analyzed food image (⭐ NEW - Task 8!)
    
    **Complete Workflow:**
    1. User uploads image → POST /vision/analyze → Get vision_context
    2. User asks question → POST /chat/with-vision → Answer using vision + RAG
    3. Multi-turn: Keep vision_context for follow-up questions
    
    **Example Use Cases:**
    - Upload phở image → Ask: "Bao nhiêu calories?"
    - Upload chicken breast → Ask: "How much protein?"
    - Upload salad → Ask: "Is this healthy for weight loss?"
    
    **Vision Context Structure:**
    ```json
    {
      "is_food": true,
      "food_name": "Phở bò",
      "components": ["bánh phở", "thịt bò", "nước dùng"],
      "database_match": {
        "nutrition": {
          "calories_per_serving": 450,
          "protein_g": 25
        }
      }
    }
    ```
    
    **Request:**
    - **question**: Your question about the food
    - **vision_context**: Result from /vision/analyze
    - **user_context**: (Optional) Your weight, goals, etc.
    
    **Response:**
    - **answer**: Natural language answer combining vision + database info
    - **vision_food**: Food name from vision
    - **sources**: Additional database sources used
    - **processing_time_ms**: Response time
    
    **Performance:**
    - Typical response time: 1.5-2.5 seconds
    - Uses Gemini 2.5 Flash + RAG (839 documents)
    """
    try:
        # Validate vision context
        if not request.vision_context.get('is_food'):
            raise HTTPException(
                status_code=400,
                detail="Vision context indicates this is not food. Please upload a food image."
            )
        
        # Convert user_context to dict
        user_ctx = None
        if request.user_context:
            user_ctx = request.user_context.model_dump(exclude_none=True)
        
        logger.info(f"🖼️  Vision chat: '{request.question}' about '{request.vision_context.get('food_name')}'")
        
        # Process with vision context
        result = await chat_service.answer_with_vision(
            question=request.question,
            vision_context=request.vision_context,
            user_context=user_ctx,
            top_k=2,
            score_threshold=0.30
        )
        
        # Format response
        response = VisionChatResponse(
            answer=result["answer"],
            vision_food=result.get("vision_food", "N/A"),
            sources=[src["title"] for src in result.get("sources", [])],
            processing_time_ms=result["processing_time_ms"]
        )
        
        logger.info(f"✅ Vision chat processed in {result['processing_time_ms']}ms")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in /chat/with-vision: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process question: {str(e)}")


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(chat_service: ChatService = Depends(get_services)):
    """
    Check health of chat service and knowledge base
    
    Returns:
        Status and collection info
    """
    try:
        collection_info = chat_service.retrieval.get_collection_info()
        
        return HealthCheckResponse(
            status="healthy",
            collection_info=collection_info
        )
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


@router.get("/collection/info")
async def get_collection_info(chat_service: ChatService = Depends(get_services)):
    """
    Get information about the knowledge base collection
    
    Returns:
        Collection statistics
    """
    try:
        info = chat_service.retrieval.get_collection_info()
        return info
    except Exception as e:
        logger.error(f"❌ Failed to get collection info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
