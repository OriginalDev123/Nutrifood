"""
Nutrition Advice Prompt Templates
Prompt engineering for personalized nutrition advice based on analytics data
Dựa trên: Tổng quan dinh dưỡng + Cân nặng + Thay đổi theo ngày/tuần/tháng
"""

from typing import Dict, List, Optional, Literal


def build_nutrition_advice_prompt(
    user_context: Dict,
    nutrition_trends: List[Dict],
    weight_progress: Dict,
    daily_summary: Optional[Dict] = None,
    meal_patterns: Optional[Dict] = None,
    period: Literal["day", "week", "month"] = "week"
) -> str:
    """
    Build prompt cho AI tạo lời khuyên dinh dưỡng cá nhân hóa.

    Prompt structure:
    1. System role - Chuyên gia dinh dưỡng AI
    2. User profile - Thông tin cá nhân (cân nặng, mục tiêu, mục tiêu calo)
    3. Weight analysis - Phân tích cân nặng (theo ngày/tuần/tháng)
    4. Nutrition overview - Tổng quan dinh dưỡng (calories, protein, carbs, fat)
    5. Daily summary - Tổng quan hôm nay (nếu có)
    6. Meal patterns - Mẫu bữa ăn
    7. Analysis timeframe - Khung thời gian phân tích
    8. Output requirements - Yêu cầu đầu ra

    Args:
        user_context: {
            user_id, current_weight_kg, goal_type, target_weight_kg,
            daily_calorie_target, target_protein_g, target_carbs_g, target_fat_g,
            height_cm, age, gender, activity_level
        }
        nutrition_trends: Danh sách {date, total_calories, protein, carbs, fat, meal_count}
        weight_progress: {
            starting_weight, current_weight, target_weight, change_kg,
            change_percentage, trend, history: [{date, weight_kg}]
        }
        daily_summary: Tổng quan hôm nay (optional)
        meal_patterns: {patterns: {breakfast: {...}, lunch: {...}, dinner: {...}, snack: {...}}}
        period: "day" | "week" | "month"

    Returns:
        Complete prompt string for Gemini

    Example:
        >>> user_ctx = {
        ...     "current_weight_kg": 75,
        ...     "goal_type": "lose_weight",
        ...     "daily_calorie_target": 2000
        ... }
        >>> trends = [{"date": "2026-04-01", "total_calories": 1800, ...}]
        >>> weight = {"current_weight": 74, "change_kg": -1, "trend": "losing", ...}
        >>> prompt = build_nutrition_advice_prompt(user_ctx, trends, weight)
    """

    # ==========================================
    # 1. USER PROFILE
    # ==========================================
    goal_type_map = {
        "lose_weight": "Giảm cân",
        "weight_loss": "Giảm cân",
        "maintain": "Duy trì cân nặng",
        "gain_weight": "Tăng cân",
        "weight_gain": "Tăng cân",
        "build_muscle": "Tăng cơ",
        "healthy_lifestyle": "Lối sống lành mạnh"
    }

    activity_map = {
        "sedentary": " Ít vận động",
        "light": " Vận động nhẹ",
        "moderate": " Vận động vừa",
        "active": " Vận động nhiều",
        "very_active": " Rất nhiều vận động"
    }

    user_info_lines = [
        f"- **Cân nặng hiện tại**: {user_context.get('current_weight_kg', 'N/A')} kg"
    ]

    if user_context.get('height_cm'):
        user_info_lines.append(f"- **Chiều cao**: {user_context['height_cm']} cm")

    if user_context.get('age'):
        user_info_lines.append(f"- **Tuổi**: {user_context['age']}")

    if user_context.get('gender'):
        gender_map = {"male": "Nam", "female": "Nữ", "other": "Khác"}
        user_info_lines.append(f"- **Giới tính**: {gender_map.get(user_context['gender'], user_context['gender'])}")

    goal_type = user_context.get('goal_type', 'unknown')
    user_info_lines.append(f"- **Mục tiêu**: {goal_type_map.get(goal_type, goal_type)}")

    if user_context.get('target_weight_kg'):
        user_info_lines.append(f"- **Cân nặng mục tiêu**: {user_context['target_weight_kg']} kg")

    if user_context.get('activity_level'):
        user_info_lines.append(f"- **Mức độ vận động**: {activity_map.get(user_context['activity_level'], user_context['activity_level'])}")

    # Mục tiêu dinh dưỡng
    nutrition_targets = []
    if user_context.get('daily_calorie_target'):
        nutrition_targets.append(f"  • Calorie: {user_context['daily_calorie_target']} kcal/ngày")
    if user_context.get('target_protein_g'):
        nutrition_targets.append(f"  • Protein: {user_context['target_protein_g']}g/ngày")
    if user_context.get('target_carbs_g'):
        nutrition_targets.append(f"  • Carbs: {user_context['target_carbs_g']}g/ngày")
    if user_context.get('target_fat_g'):
        nutrition_targets.append(f"  • Fat: {user_context['target_fat_g']}g/ngày")

    user_profile_text = "\n".join(user_info_lines)
    nutrition_targets_text = "\n".join(nutrition_targets) if nutrition_targets else "Chưa có thông tin"

    # ==========================================
    # 2. WEIGHT ANALYSIS
    # ==========================================
    if weight_progress and weight_progress.get('current_weight'):
        starting = weight_progress.get('starting_weight', 'N/A')
        current = weight_progress.get('current_weight', 'N/A')
        target = weight_progress.get('target_weight', 'N/A')
        change = weight_progress.get('change_kg', 0)
        change_pct = weight_progress.get('change_percentage', 0)
        trend_map = {
            "gaining": "📈 Tăng cân",
            "losing": "📉 Giảm cân",
            "stable": "➡️ Ổn định",
            "no_data": "❓ Chưa đủ dữ liệu"
        }
        trend = trend_map.get(weight_progress.get('trend', 'no_data'), weight_progress.get('trend', 'no_data'))

        # Phân tích thay đổi cân nặng theo thời gian
        history = weight_progress.get('history', [])
        if history and len(history) >= 2:
            # So sánh cân nặng theo từng khoảng thời gian
            weight_changes_by_period = []
            recent_week_weight = None
            recent_month_weight = None

            # Tìm cân nặng 7 ngày trước và 30 ngày trước
            from datetime import datetime, timedelta
            today = datetime.now()
            week_ago = today - timedelta(days=7)
            month_ago = today - timedelta(days=30)

            for h in reversed(history):
                try:
                    h_date = datetime.strptime(h['date'], '%Y-%m-%d')
                    if h_date <= week_ago and recent_week_weight is None:
                        recent_week_weight = h['weight_kg']
                    if h_date <= month_ago and recent_month_weight is None:
                        recent_month_weight = h['weight_kg']
                except:
                    pass

            if recent_week_weight and current:
                weekly_change = current - recent_week_weight
                direction = "giảm" if weekly_change < 0 else "tăng"
                weight_changes_by_period.append(f"  • **7 ngày qua**: {direction} {abs(weekly_change):.2f} kg")

            if recent_month_weight and current:
                monthly_change = current - recent_month_weight
                direction = "giảm" if monthly_change < 0 else "tăng"
                weight_changes_by_period.append(f"  • **30 ngày qua**: {direction} {abs(monthly_change):.2f} kg")

            weight_changes_text = "\n".join(weight_changes_by_period) if weight_changes_by_period else ""
        else:
            weight_changes_text = ""

        # Lịch sử cân nặng gần đây (5 ngày gần nhất)
        recent_history = history[-5:] if history else []
        history_lines = []
        for h in reversed(recent_history):
            history_lines.append(f"    - {h['date']}: {h['weight_kg']} kg")

        weight_analysis_lines = [
            f"- **Cân nặng ban đầu**: {starting} kg",
            f"- **Cân nặng hiện tại**: {current} kg",
            f"- **Cân nặng mục tiêu**: {target} kg" if target else "- **Cân nặng mục tiêu**: Chưa đặt",
            f"- **Thay đổi**: {change:+.2f} kg ({change_pct:+.2f}%)",
            f"- **Xu hướng**: {trend}",
        ]

        if weight_changes_text:
            weight_analysis_lines.append(f"\n**📊 Thay đổi cân nặng theo thời gian:**\n{weight_changes_text}")

        if history_lines:
            weight_analysis_lines.append(f"\n**📋 Lịch sử cân nặng (5 ngày gần nhất):**\n" + "\n".join(history_lines))

        weight_analysis_text = "\n".join(weight_analysis_lines)
    else:
        weight_analysis_text = "⚠️ Chưa có dữ liệu cân nặng"

    # ==========================================
    # 3. NUTRITION TRENDS
    # ==========================================
    if nutrition_trends and len(nutrition_trends) > 0:
        # Tính toán thống kê
        total_days = len(nutrition_trends)

        avg_calories = sum(t.get('total_calories', 0) for t in nutrition_trends) / total_days
        avg_protein = sum(t.get('protein', 0) for t in nutrition_trends) / total_days
        avg_carbs = sum(t.get('carbs', 0) for t in nutrition_trends) / total_days
        avg_fat = sum(t.get('fat', 0) for t in nutrition_trends) / total_days
        avg_meals = sum(t.get('meal_count', 0) for t in nutrition_trends) / total_days

        # So sánh với mục tiêu
        calorie_target = user_context.get('daily_calorie_target', 2000)
        calorie_diff = avg_calories - calorie_target
        calorie_status = "thừa" if calorie_diff > 0 else "thiếu" if calorie_diff < 0 else "đạt"

        # Tính xu hướng (so sánh nửa đầu vs nửa sau)
        mid_point = total_days // 2
        if mid_point >= 1:
            first_half = nutrition_trends[:mid_point]
            second_half = nutrition_trends[mid_point:]

            first_half_avg = sum(t.get('total_calories', 0) for t in first_half) / len(first_half)
            second_half_avg = sum(t.get('total_calories', 0) for t in second_half) / len(second_half)
            calorie_trend = second_half_avg - first_half_avg
            trend_direction = "tăng" if calorie_trend > 50 else "giảm" if calorie_trend < -50 else "ổn định"
        else:
            trend_direction = "chưa đủ dữ liệu"

        # Protein ratio
        protein_target = user_context.get('target_protein_g', 0)
        protein_ratio = (avg_protein / protein_target * 100) if protein_target > 0 else 0

        nutrition_summary_lines = [
            f"- **Số ngày phân tích**: {total_days} ngày",
            f"- **Lượng tiêu thụ trung bình/ngày**:",
            f"    • Calo: {avg_calories:.0f} kcal (mục tiêu: {calorie_target} kcal → {calorie_status} {abs(calorie_diff):.0f} kcal)",
            f"    • Protein: {avg_protein:.1f}g (mục tiêu: {protein_target}g → {protein_ratio:.0f}%)" if protein_target else f"    • Protein: {avg_protein:.1f}g",
            f"    • Carbs: {avg_carbs:.1f}g",
            f"    • Fat: {avg_fat:.1f}g",
            f"- **Số bữa ăn trung bình/ngày**: {avg_meals:.1f}",
            f"- **Xu hướng calories**: {trend_direction}",
        ]

        # Chi tiết từng ngày (7 ngày gần nhất)
        recent_trends = nutrition_trends[-7:]
        trend_detail_lines = []
        for t in reversed(recent_trends):
            date_str = t.get('date', 'N/A')
            cal = t.get('total_calories', 0)
            prot = t.get('protein', 0)
            meals = t.get('meal_count', 0)
            diff = cal - calorie_target
            status_icon = "🔴" if diff > 200 else "🟡" if diff > 50 else "🟢"
            trend_detail_lines.append(f"    {status_icon} {date_str}: {cal:.0f} kcal, {prot:.0f}g protein, {meals} bữa")

        nutrition_summary_lines.append(f"\n**📅 Chi tiết 7 ngày gần nhất:**\n" + "\n".join(trend_detail_lines))
        nutrition_summary_text = "\n".join(nutrition_summary_lines)
    else:
        nutrition_summary_text = "⚠️ Chưa có dữ liệu dinh dưỡng"

    # ==========================================
    # 4. DAILY SUMMARY (HÔM NAY)
    # ==========================================
    if daily_summary:
        today_cal = daily_summary.get('total_calories', 0)
        today_protein = daily_summary.get('protein', 0)
        today_carbs = daily_summary.get('carbs', 0)
        today_fat = daily_summary.get('fat', 0)
        today_meals = daily_summary.get('meal_count', 0)
        cal_target = user_context.get('daily_calorie_target', 2000)
        cal_remaining = cal_target - today_cal
        cal_pct = (today_cal / cal_target * 100) if cal_target > 0 else 0

        daily_summary_lines = [
            f"- **Hôm nay ({daily_summary.get('date', 'N/A')})**:",
            f"    • Calo: {today_cal:.0f} / {cal_target} kcal ({cal_pct:.0f}%)",
            f"    • Còn lại: {cal_remaining:.0f} kcal",
            f"    • Protein: {today_protein:.0f}g | Carbs: {today_carbs:.0f}g | Fat: {today_fat:.0f}g",
            f"    • Số bữa ăn: {today_meals}",
        ]
        daily_summary_text = "\n".join(daily_summary_lines)
    else:
        daily_summary_text = "Chưa có dữ liệu hôm nay"

    # ==========================================
    # 5. MEAL PATTERNS
    # ==========================================
    if meal_patterns and meal_patterns.get('patterns'):
        meal_names = {
            "breakfast": "🍳 Bữa sáng",
            "lunch": "🍽️ Bữa trưa",
            "dinner": "🌙 Bữa tối",
            "snack": "🍪 Bữa phụ"
        }

        pattern_lines = []
        for meal_type, data in meal_patterns['patterns'].items():
            meal_name = meal_names.get(meal_type, meal_type)
            count = data.get('count', 0)
            avg_cal = data.get('avg_calories', 0)
            pct = data.get('avg_percentage', 0)
            pattern_lines.append(f"  • {meal_name}: {count} bữa, TB {avg_cal:.0f} kcal ({pct:.0f}%)")

        meal_patterns_text = "\n".join(pattern_lines)
    else:
        meal_patterns_text = "Chưa có dữ liệu mẫu bữa ăn"

    # ==========================================
    # 6. TIMEFRAME CONTEXT
    # ==========================================
    timeframe_text = {
        "day": "hôm nay",
        "week": "7 ngày qua",
        "month": "30 ngày qua"
    }.get(period, "thời gian phân tích")

    # ==========================================
    # BUILD COMPLETE PROMPT
    # ==========================================
    prompt = f"""
# NUTRIAI - CHUYÊN GIA DINH DƯỠNG AI

## Vai trò
Bạn là chuyên gia dinh dưỡng AI của **NutriAI** - ứng dụng theo dõi dinh dưỡng hàng đầu Việt Nam.
Nhiệm vụ của bạn: Phân tích dữ liệu dinh dưỡng và cân nặng của người dùng, đưa ra **lời khuyên cá nhân hóa** để cải thiện sức khỏe.

---

## 👤 THÔNG TIN NGƯỜI DÙNG

{user_profile_text}

### 🎯 Mục tiêu dinh dưỡng hàng ngày:
{nutrition_targets_text}

---

## ⚖️ PHÂN TÍCH CÂN NẶNG

{weight_analysis_text}

---

## 📊 TỔNG QUAN DINH DƯỠNG ({timeframe_text})

{nutrition_summary_text}

---

## 🍽️ TỔNG QUAN HÔM NAY

{daily_summary_text}

---

## 📋 MẪU BỮA ĂN

{meal_patterns_text}

---

## 📌 YÊU CẦU ĐẦU RA

Bạn phải phân tích TẤT CẢ dữ liệu trên và trả về JSON với cấu trúc sau:

```json
{{
    "summary": "Tổng kết ngắn gọn 2-3 câu về tình trạng dinh dưỡng hiện tại của người dùng",
    "highlights": [
        "Điểm sáng 1 (ví dụ: Đã kiểm soát tốt lượng carbs)",
        "Điểm sáng 2",
        "Điểm sáng 3"
    ],
    "concerns": [
        "Vấn đề cần lưu ý 1 (ví dụ: Calo vượt mục tiêu 300kcal)",
        "Vấn đề 2",
        "Vấn đề 3"
    ],
    "recommendations": [
        "💡 Lời khuyên cụ thể 1 (theo thứ tự ưu tiên)",
        "💡 Lời khuyên cụ thể 2",
        "💡 Lời khuyên cụ thể 3"
    ],
    "motivational_tip": "Động lực ngắn 1 câu để khuyến khích người dùng"
}}
```

### Tiêu chí quan trọng:

1. **Cá nhân hóa cao**: Mỗi lời khuyên phải dựa trên dữ liệu cụ thể của người dùng
2. **Thực tế**: Đưa ra gợi ý có thể thực hiện được trong cuộc sống hàng ngày
3. **Liên quan đến mục tiêu**: Lời khuyên phải hỗ trợ mục tiêu ({goal_type_map.get(goal_type, goal_type)})
4. **Cân bằng dinh dưỡng**: Nếu protein/carbs/fat không cân đối, đề xuất cách cải thiện
5. **Xu hướng cân nặng**: Phân tích xu hướng thay đổi cân nặng, đưa ra nhận xét
6. **Thời gian**: Phân tích theo từng ngày, tuần, tháng để nhận ra pattern
7. **Ngôn ngữ**: Sử dụng tiếng Việt tự nhiên, thân thiện, dễ hiểu
8. **Số liệu**: Khi đề cập calories/protein/etc, luôn trích dẫn số liệu cụ thể từ dữ liệu
9. **Giới hạn**: Tối đa 3 concerns và 3 recommendations (chỉ chọn quan trọng nhất)
10. **Định dạng**: KHÔNG thêm markdown code block, chỉ trả về JSON thuần

### Ví dụ về recommendations tốt:
- "⚠️ Calo hôm nay đã vượt mục tiêu 350kcal. Cân nhắc giảm 1 bữa phụ hoặc chọn thực phẩm ít calo hơn cho bữa tối."
- "📈 Protein chỉ đạt 60% mục tiêu. Thêm 1 nguồn protein nạc như ức gà (100g = 31g protein) vào bữa phụ."
- "✅ Bạn đã duy trì xu hướng giảm cân tốt trong 2 tuần. Tiếp tục với kế hoạch hiện tại!"

### Ví dụ về recommendations kém:
- ❌ "Hãy ăn nhiều rau xanh" (quá chung chung)
- ❌ "Tập thể dục nhiều hơn" (không liên quan đến dữ liệu)
- ❌ "Uống nhiều nước" (không có trong dữ liệu)

---

## Kết quả (JSON):
"""

    return prompt.strip()


# ==========================================
# ALTERNATIVE: Short advice prompt (for quick tips)
# ==========================================

def build_quick_advice_prompt(
    user_context: Dict,
    daily_summary: Dict,
    remaining_nutrients: Optional[Dict] = None
) -> str:
    """
    Build prompt cho AI tạo lời khuyên NHANH (dựa trên 1 ngày).

    Args:
        user_context: Thông tin người dùng cơ bản
        daily_summary: Tổng quan hôm nay
        remaining_nutrients: Dinh dưỡng còn lại (optional)

    Returns:
        Prompt ngắn gọn cho quick advice
    """

    goal_type_map = {
        "lose_weight": "giảm cân",
        "weight_loss": "giảm cân",
        "maintain": "duy trì cân nặng",
        "gain_weight": "tăng cân",
        "weight_gain": "tăng cân",
        "build_muscle": "tăng cơ",
        "healthy_lifestyle": "lối sống lành mạnh"
    }

    goal_type = user_context.get('goal_type', 'unknown')
    goal_text = goal_type_map.get(goal_type, goal_type)

    # Tổng quan hôm nay
    today_cal = daily_summary.get('total_calories', 0)
    today_protein = daily_summary.get('protein', 0)
    today_carbs = daily_summary.get('carbs', 0)
    today_fat = daily_summary.get('fat', 0)
    today_meals = daily_summary.get('meal_count', 0)
    cal_target = user_context.get('daily_calorie_target', 2000)
    cal_remaining = cal_target - today_cal
    protein_target = user_context.get('target_protein_g', 0)
    protein_remaining = protein_target - today_protein if protein_target else 0

    prompt = f"""
# NUTRIAI - LỜI KHUYÊN NHANH

Bạn là chuyên gia dinh dưỡng AI của NutriAI.

## Thông tin người dùng
- Mục tiêu: {goal_text}
- Cân nặng: {user_context.get('current_weight_kg', 'N/A')} kg
- Calo mục tiêu: {cal_target} kcal/ngày

## Hôm nay ({daily_summary.get('date', 'N/A')})
- Đã ăn: {today_cal} kcal ({today_cal/cal_target*100:.0f}% mục tiêu)
- Protein: {today_protein}g / {protein_target}g
- Carbs: {today_carbs}g | Fat: {today_fat}g
- Số bữa ăn: {today_meals}
- Còn lại: {cal_remaining} kcal | Protein còn thiếu: {protein_remaining}g

## Yêu cầu
Trả về JSON ngắn gọn cho 1 lời khuyên cụ thể:

```json
{{
    "quick_tip": "Lời khuyên 1 câu cực kỳ cụ thể cho bữa tiếp theo",
    "action": "Hành động cụ thể người dùng nên làm ngay",
    "why": "Tại sao nên làm điều này (dựa trên số liệu)"
}}
```

Ví dụ:
- Nếu calo còn nhiều nhưng protein thiếu: "Bữa tối ưu tiên protein: 150g cá hồi + rau trộn = 300kcal nhưng giàu protein"
- Nếu calo gần đạt: "Còn {cal_remaining}kcal - chọn bữa phụ nhẹ: 1 quả táo + 30g phô mai"
- Nếu protein đạt: "Protein hôm nay đã tốt! Tập trung vào rau xanh cho bữa còn lại"

Định dạng: Chỉ trả về JSON thuần, không markdown.
"""

    return prompt.strip()


# ==========================================
# PROGRESS REPORT PROMPT (Weekly/Monthly)
# ==========================================

def build_progress_report_prompt(
    user_context: Dict,
    weight_progress: Dict,
    nutrition_trends: List[Dict],
    weekly_summaries: Optional[List[Dict]] = None,
    period: Literal["week", "month"] = "week"
) -> str:
    """
    Build prompt cho AI tạo báo cáo tiến độ (tuần/tháng).

    Args:
        user_context: Thông tin người dùng
        weight_progress: Dữ liệu cân nặng
        nutrition_trends: Xu hướng dinh dưỡng
        weekly_summaries: Tổng quan từng tuần (optional)
        period: "week" hoặc "month"

    Returns:
        Prompt cho progress report
    """

    goal_type_map = {
        "lose_weight": "giảm cân",
        "weight_loss": "giảm cân",
        "maintain": "duy trì cân nặng",
        "gain_weight": "tăng cân",
        "weight_gain": "tăng cân",
        "build_muscle": "tăng cơ",
        "healthy_lifestyle": "lối sống lành mạnh"
    }

    goal_type = user_context.get('goal_type', 'unknown')
    goal_text = goal_type_map.get(goal_type, goal_type)
    period_text = "tuần" if period == "week" else "tháng"

    # Tính toán thống kê
    total_days = len(nutrition_trends) if nutrition_trends else 0
    calorie_target = user_context.get('daily_calorie_target', 2000)

    if nutrition_trends:
        avg_cal = sum(t.get('total_calories', 0) for t in nutrition_trends) / total_days
        avg_protein = sum(t.get('protein', 0) for t in nutrition_trends) / total_days
        adherence_days = sum(1 for t in nutrition_trends if abs(t.get('total_calories', 0) - calorie_target) <= calorie_target * 0.1)
        adherence_rate = (adherence_days / total_days * 100) if total_days > 0 else 0
    else:
        avg_cal = avg_protein = 0
        adherence_rate = 0

    # Cân nặng
    current_weight = weight_progress.get('current_weight', 'N/A')
    starting_weight = weight_progress.get('starting_weight', 'N/A')
    target_weight = weight_progress.get('target_weight', 'N/A')
    change_kg = weight_progress.get('change_kg', 0)
    trend = weight_progress.get('trend', 'unknown')

    prompt = f"""
# NUTRIAI - BÁO CÁO TIẾN ĐỘ {period_text.upper()}

Bạn là chuyên gia dinh dưỡng AI của NutriAI.

## Người dùng
- Mục tiêu: {goal_text}
- Cân nặng ban đầu: {starting_weight} kg → Hiện tại: {current_weight} kg
- Cân nặng mục tiêu: {target_weight} kg

## Thống kê {period_text}
- Số ngày theo dõi: {total_days}
- Calo TB/ngày: {avg_cal:.0f} kcal (mục tiêu: {calorie_target})
- Protein TB/ngày: {avg_protein:.0f}g
- Tỷ lệ tuân thủ: {adherence_rate:.0f}%
- Thay đổi cân nặng: {change_kg:+.2f} kg

## Xu hướng cân nặng
- Trend: {trend}
- Cần {abs(current_weight - target_weight):.1f}kg nữa để đạt mục tiêu

## Yêu cầu
Trả về JSON báo cáo tiến độ chi tiết:

```json
{{
    "period": "{period_text}",
    "overall_score": 85,
    "summary": "Tổng kết 2-3 câu về tiến độ {period_text}",
    "weight_analysis": {{
        "progress": "Mô tả tiến độ cân nặng",
        "on_track": true/false,
        "reasoning": "Giải thích tại sao đúng hay sai tiến độ"
    }},
    "nutrition_analysis": {{
        "calorie_adherence": "Mô tả",
        "protein_quality": "Mô tả",
        "consistency": "Mô tả"
    }},
    "achievements": [
        "Thành tựu 1",
        "Thành tựu 2"
    ],
    "areas_for_improvement": [
        "Cần cải thiện 1",
        "Cần cải thiện 2"
    ],
    "next_week_tips": [
        "Tip 1 cho tuần tới",
        "Tip 2 cho tuần tới"
    ],
    "motivation": "Động lực ngắn gọn 1-2 câu"
}}
```

Định dạng: Chỉ trả về JSON thuần.
"""

    return prompt.strip()
