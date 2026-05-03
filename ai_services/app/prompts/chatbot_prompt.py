"""
Chatbot Prompt Templates
Prompt engineering for nutrition Q&A with RAG
"""

from typing import List, Dict, Optional


def build_chatbot_prompt(
    question: str,
    context_docs: List[Dict],
    user_context: Optional[Dict] = None,
    conversation_context: Optional[str] = None
) -> str:
    """
    Build prompt for RAG-based nutrition chatbot (⭐ UPDATED - Task 9!)
    
    Prompt structure:
    1. System role definition
    2. Conversation history (if available) - NEW!
    3. User context (if available)
    4. Retrieved knowledge context
    5. User's question
    6. Answer requirements
    
    Args:
        question: User's nutrition question
        context_docs: Retrieved documents (list of dicts with title, content, score)
        user_context: Optional user info (weight, goals, daily targets, etc.)
        conversation_context: Optional conversation history (NEW!)
    
    Returns:
        Complete prompt string for Gemini
    
    Example:
        >>> docs = [{"title": "Phở Bò", "content": "...", "score": 0.92}]
        >>> user_ctx = {"current_weight": 70, "goal_type": "lose_weight"}
        >>> conv_ctx = "User: Phở bò có bao nhiêu calo?\nAssistant: Phở bò có 450 kcal..."
        >>> prompt = build_chatbot_prompt("Và protein thì sao?", docs, user_ctx, conv_ctx)
    """
    
    # Format conversation history - NEW!
    conversation_text = ""
    if conversation_context:
        conversation_text = f"\n**Lịch sử trò chuyện:**\n{conversation_context}\n"
    
    # Format context documents
    if context_docs:
        context_text = "\n\n".join([
            f"[Tài liệu {i+1}] {doc['title']}\n{doc['content']}"
            for i, doc in enumerate(context_docs)
        ])
    else:
        context_text = "(Không có tài liệu liên quan trong cơ sở dữ liệu)"
    
    # Format user information
    user_info = ""
    if user_context:
        user_info_parts = []
        
        if user_context.get('current_weight'):
            user_info_parts.append(f"- Cân nặng: {user_context['current_weight']} kg")
        
        if user_context.get('goal_type'):
            goal_map = {
                'lose_weight': 'Giảm cân',
                'weight_loss': 'Giảm cân',
                'maintain': 'Duy trì',
                'gain_weight': 'Tăng cân',
                'weight_gain': 'Tăng cân',
                'build_muscle': 'Tăng cơ',
                'healthy_lifestyle': 'Lối sống lành mạnh'
            }
            goal = goal_map.get(user_context['goal_type'], user_context['goal_type'])
            user_info_parts.append(f"- Mục tiêu: {goal}")
        
        if user_context.get('daily_target'):
            user_info_parts.append(f"- Calorie mục tiêu: {user_context['daily_target']} kcal/ngày")
        
        if user_context.get('consumed_today') is not None:
            consumed = user_context['consumed_today']
            remaining = user_context.get('daily_target', 0) - consumed
            user_info_parts.append(f"- Đã ăn hôm nay: {consumed} kcal")
            if user_context.get('daily_target'):
                user_info_parts.append(f"- Còn lại hôm nay: {remaining} kcal")
        
        if user_info_parts:
            user_info = "\n**Thông tin người dùng:**\n" + "\n".join(user_info_parts) + "\n"
    
    # Build complete prompt
    prompt = f"""
Bạn là chuyên gia dinh dưỡng AI của NutriAI, chuyên tư vấn về calories và dinh dưỡng Việt Nam.
{conversation_text}
{user_info}
**Ngữ cảnh từ kiến thức:**
{context_text}

**Câu hỏi:**
{question}

**YÊU CẦU QUAN TRỌNG:**
1. Chỉ trả lời bằng tiếng Việt tự nhiên
2. Trả lời đầy đủ, không cắt ngắn (tối thiểu 3-5 câu)
3. Ưu tiên thông tin từ "Ngữ cảnh" nếu có
4. Nếu không có thông tin, nói rõ và gợi ý câu hỏi khác
5. KHÔNG trả lời bằng tiếng Anh
6. KHÔNG viết internal thoughts, reasoning, hay meta-comments
7. KHÔNG viết như "The user is asking...", "Based on the context..."
8. Trả lời TRỰC TIẾP như đang nói chuyện với người dùng

**Trả lời (chỉ nội dung trả lời, không thêm gì khác):**
"""
    
    return prompt.strip()


def build_no_context_prompt(question: str, user_context: Optional[Dict] = None) -> str:
    """
    Build prompt when no relevant documents found
    
    This prompt guides the model to politely decline and suggest similar topics
    
    Args:
        question: User's question
        user_context: Optional user info
    
    Returns:
        Prompt for handling out-of-scope questions
    """
    
    user_info = ""
    if user_context and user_context.get('current_weight'):
        user_info = f"\n**Thông tin người dùng:** Cân nặng {user_context['current_weight']} kg\n"
    
    prompt = f"""
Bạn là chuyên gia dinh dưỡng AI của NutriAI.

{user_info}
**Câu hỏi:**
{question}

**Tình huống:**
Không tìm thấy thông tin liên quan trong cơ sở dữ liệu.

**Yêu cầu trả lời:**
1. Xin lỗi lịch sự về việc không có thông tin
2. Giải thích ngắn gọn tại sao (chưa có trong cơ sở dữ liệu)
3. Gợi ý 2-3 câu hỏi liên quan mà bạn CÓ THỂ trả lời (về calories, dinh dưỡng Việt Nam)
4. Sử dụng tiếng Việt thân thiện

**Trả lời:**
"""
    
    return prompt.strip()


def build_prompt_with_vision(
    question: str,
    vision_context: Dict,
    context_docs: List[Dict],
    user_context: Optional[Dict] = None
) -> str:
    """
    Build prompt with vision analysis context (NEW for Task 8!)
    
    This enables follow-up questions about analyzed food images:
    - User uploads image → Vision identifies "Phở bò"
    - User asks: "Bao nhiêu calories?" → Answer using vision context
    
    Args:
        question: User's follow-up question about the food
        vision_context: Vision analysis result from /vision/analyze
        context_docs: Retrieved documents from RAG
        user_context: Optional user info
    
    Returns:
        Prompt with vision analysis included
    
    Example:
        >>> vision_result = {"food_name": "Phở bò", "database_match": {...}}
        >>> prompt = build_prompt_with_vision("Bao nhiêu calo?", vision_result, docs)
    """
    
    # Format vision analysis context
    vision_text = ""
    if vision_context and vision_context.get('is_food'):
        food_name = vision_context.get('food_name', 'món ăn')
        components = vision_context.get('components', [])
        
        vision_text = f"\n**📸 Ảnh món ăn vừa phân tích:**\n"
        vision_text += f"- Tên món: {food_name}\n"
        
        if components:
            vision_text += f"- Thành phần: {', '.join(components)}\n"
        
        # Include database match if available
        db_match = vision_context.get('database_match')
        if db_match:
            nutrition = db_match.get('nutrition', {})
            vision_text += f"- Loại: {db_match.get('item_type', 'N/A')}\n"
            
            if nutrition:
                if 'calories_per_serving' in nutrition:
                    vision_text += f"- Calories: {nutrition['calories_per_serving']} kcal/phần\n"
                if 'protein_g' in nutrition:
                    vision_text += f"- Protein: {nutrition['protein_g']}g\n"
                if 'carbs_g' in nutrition:
                    vision_text += f"- Carbs: {nutrition['carbs_g']}g\n"
                if 'fat_g' in nutrition:
                    vision_text += f"- Fat: {nutrition['fat_g']}g\n"
        
        # Include portion presets if available
        presets = vision_context.get('portion_presets', [])
        if presets:
            vision_text += f"- Khẩu phần có sẵn: "
            preset_names = [p.get('display_name_vi', p.get('size_label', '')) for p in presets]
            vision_text += ", ".join(preset_names) + "\n"
    
    # Format RAG context documents
    if context_docs:
        context_text = "\n\n".join([
            f"[Tài liệu {i+1}] {doc['title']}\n{doc['content']}"
            for i, doc in enumerate(context_docs)
        ])
    else:
        context_text = "(Không có tài liệu bổ sung)"
    
    # Format user information
    user_info = ""
    if user_context:
        user_info_parts = []
        
        if user_context.get('current_weight'):
            user_info_parts.append(f"- Cân nặng: {user_context['current_weight']} kg")
        
        if user_context.get('goal_type'):
            goal_map = {
                'lose_weight': 'Giảm cân',
                'weight_loss': 'Giảm cân',
                'maintain': 'Duy trì',
                'gain_weight': 'Tăng cân',
                'weight_gain': 'Tăng cân',
                'build_muscle': 'Tăng cơ',
                'healthy_lifestyle': 'Lối sống lành mạnh'
            }
            goal = goal_map.get(user_context['goal_type'], user_context['goal_type'])
            user_info_parts.append(f"- Mục tiêu: {goal}")
        
        if user_context.get('daily_target'):
            user_info_parts.append(f"- Calorie mục tiêu: {user_context['daily_target']} kcal/ngày")
        
        if user_info_parts:
            user_info = "\n**Thông tin người dùng:**\n" + "\n".join(user_info_parts) + "\n"
    
    # Build complete prompt
    prompt = f"""
Bạn là chuyên gia dinh dưỡng AI của NutriAI.

{vision_text}
{user_info}
**Ngữ cảnh từ cơ sở dữ liệu:**
{context_text}

**Câu hỏi về món ăn:**
{question}

**Yêu cầu trả lời:**
1. SỬ DỤNG thông tin từ "📸 Ảnh món ăn vừa phân tích" làm nguồn chính
2. Bổ sung từ "Ngữ cảnh từ cơ sở dữ liệu" nếu cần
3. Trả lời ngắn gọn, rõ ràng (2-4 câu)
4. Nếu hỏi về calories/dinh dưỡng, trích dẫn số liệu cụ thể
5. Nếu liên quan đến mục tiêu người dùng, đưa ra gợi ý
6. Sử dụng tiếng Việt tự nhiên, thân thiện

**Trả lời:**
"""
    
    return prompt.strip()


def build_followup_prompt(
    question: str,
    previous_qa: List[Dict],
    context_docs: List[Dict],
    user_context: Optional[Dict] = None
) -> str:
    """
    Build prompt for follow-up questions with conversation history
    
    Args:
        question: Current question
        previous_qa: List of {"question": "...", "answer": "..."}
        context_docs: Retrieved documents
        user_context: Optional user info
    
    Returns:
        Prompt with conversation context
    """
    
    # Format conversation history
    history_text = "\n\n".join([
        f"Q: {qa['question']}\nA: {qa['answer']}"
        for qa in previous_qa[-3:]  # Last 3 exchanges only
    ])
    
    # Format context
    context_text = "\n\n".join([
        f"[Tài liệu {i+1}] {doc['title']}\n{doc['content']}"
        for i, doc in enumerate(context_docs)
    ])
    
    # Format user info
    user_info = ""
    if user_context:
        parts = []
        if user_context.get('current_weight'):
            parts.append(f"Cân nặng: {user_context['current_weight']} kg")
        if user_context.get('goal_type'):
            parts.append(f"Mục tiêu: {user_context['goal_type']}")
        if parts:
            user_info = f"\n**Thông tin người dùng:** {', '.join(parts)}\n"
    
    prompt = f"""
Bạn là chuyên gia dinh dưỡng AI của NutriAI, đang trò chuyện với người dùng.

{user_info}
**Lịch sử trò chuyện:**
{history_text}

**Ngữ cảnh từ kiến thức:**
{context_text}

**Câu hỏi tiếp theo:**
{question}

**Yêu cầu trả lời:**
1. Tham khảo lịch sử trò chuyện để hiểu ngữ cảnh
2. Trả lời ngắn gọn, tự nhiên như đang trò chuyện
3. Sử dụng thông tin từ "Ngữ cảnh" ưu tiên
4. Nếu câu hỏi liên quan đến câu trả lời trước, đề cập ngắn gọn

**Trả lời:**
"""
    
    return prompt.strip()
