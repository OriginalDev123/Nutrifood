# 📱 Frontend Development Plan - NutriAI Project
## 🚀 3-WEEK SPRINT TO 80% COMPLETION

> **Version:** 2.0.0 - FAST TRACK EDITION  
> **Timeline:** 3 weeks (15 working days per person)  
> **Goal:** 80% MVP Complete  
> **Last Updated:** March 5, 2026  

---

## ⏱️ CRITICAL CONSTRAINTS

- **Total Time:** 3 weeks = 15 working days each
- **Target:** 80% core features (NOT 100%)
- **Team Size:** 2 people (1 Web + 1 Mobile)
- **Work Schedule:** 8-10 hours/day focused work

---

## 🎯 80% MVP SCOPE

### ✅ MUST HAVE (Core 80%)
1. ✅ Authentication (Login/Register)
2. ✅ Dashboard (basic summary)
3. ✅ Food Database (search + basic list)
4. ✅ Food Logging (add/view/delete)
5. ✅ Food Diary (daily view with progress)
6. ✅ Profile & Goals (basic edit)
7. ✅ Recipes (list + detail + favorites)
8. ✅ Basic Analytics (2-3 charts only)
9. ✅ Basic AI Chatbot (text chat, 3-4 tools)
10. ✅ **Camera + AI Vision** (Mobile only - KEY SELLING POINT)

### ❌ CUT FROM 3-WEEK SPRINT (Do later)
- ❌ Advanced analytics (7+ charts)
- ❌ All 9 chatbot function tools (only implement 3-4 critical ones)
- ❌ Meal planning AI (complex, time-consuming)
- ❌ Admin dashboard
- ❌ Recipe shopping list
- ❌ Ingredient substitutions
- ❌ Social features
- ❌ Dark mode
- ❌ Advanced filters

---

## 👥 TEAM SETUP

### **Developer 1: Web App (React)**
**Stack:**
- React 19 + TypeScript + Vite
- TailwindCSS v4
- React Router v7
- TanStack Query
- Zustand
- Axios

**Starting Point:** 20% done (routing + API clients exist)

### **Developer 2: Mobile App (Flutter)**
**Stack:**
- Flutter 3.16+
- Provider (state management)
- Dio (HTTP)
- Image Picker (camera)
- FL Chart (charts)

**Starting Point:** 0% (need to create from scratch)

---

## � 3-WEEK SPRINT BREAKDOWN

---

# 🌐 WEB DEVELOPER - 15 DAY PLAN

---

## **WEEK 1: Foundation + Core Features** (Days 1-5)

### **Day 1 (Wed): Project Foundation**
**Goal:** Setup complete, ready to build features
**Tasks:**
- ✅ Create folder structure (components/, pages/, hooks/, utils/)
- ✅ Build 8 basic UI components (Button, Input, Card, Modal, Alert, Badge, Spinner, SearchBar)
- ✅ Create Layout components (Header, Sidebar for desktop, MobileNav for mobile)
- ✅ Setup routing with ProtectedRoute wrapper
- ✅ Test components render correctly

**Time:** 8-10 hours  
**Deliverables:** Component library + Layout working

---

### **Day 2 (Thu): Authentication**
**Goal:** Users can login/register
**Tasks:**
- ✅ Build Login page (email + password form)
- ✅ Build Register page (email + password + full name)
- ✅ Form validation (email format, password length 6+)
- ✅ API integration (POST /auth/login, /auth/register)
- ✅ JWT token storage in localStorage
- ✅ Update authStore (Zustand)
- ✅ Protected route redirect working
- ✅ Test: Login → Dashboard, Logout → Login

**Time:** 8-10 hours  
**Deliverables:** Complete auth flow working

---

### **Day 3 (Fri): Dashboard + API Expansion**
**Goal:** Landing page after login with summary
**Tasks:**
- ✅ Create API clients: `foodLog.ts`, `recipe.ts`, `goal.ts`, `analytics.ts`, `ai.ts`
- ✅ Build Dashboard page:
  - Welcome card with user name
  - Today's nutrition summary (calories, protein, carbs, fat)
  - Progress bars toward goals
  - Quick action buttons (Log Food, Browse Foods, Open Chat)
  - Recent logs (last 5 items)
- ✅ API integration: GET /food-logs/daily/today, GET /goals/active
- ✅ Test: Data loads correctly, actions navigate correctly

**Time:** 8-10 hours  
**Deliverables:** Dashboard working with real data

---

### **Day 4 (Sat): Food Database**
**Goal:** Browse and search foods
**Tasks:**
- ✅ Build Food List page:
  - Paginated list (20 per page)
  - Search bar (debounced 300ms)
  - Category filter dropdown
  - Grid view with food cards (name, category, calories)
  - Pagination controls
  - Loading skeleton
- ✅ Build Food Detail page:
  - Nutrition table (per 100g)
  - Serving sizes list
  - "Add to Diary" button → opens modal
- ✅ API integration: GET /foods?page=..., GET /foods/{id}
- ✅ Test: Search, pagination, view detail, modal opens

**Time:** 8-10 hours  
**Deliverables:** Food browsing working

---

### **Day 5 (Sun): Food Diary**
**Goal:** Log and view daily food intake
**Tasks:**
- ✅ Build Food Logging Modal:
  - Food name (read-only)
  - Serving size dropdown
  - Quantity input
  - Meal type selector (Breakfast/Lunch/Dinner/Snack)
  - Date picker (default: today)
  - **Real-time nutrition calculation**
  - Save button
- ✅ Build Food Diary page:
  - Date picker (default: today)
  - 4 meal sections (Breakfast, Lunch, Dinner, Snack)
  - Food cards with edit/delete buttons
  - Daily summary at top (total calories, macros, progress bars)
  - "Add food" button per meal
- ✅ API integration: POST /food-logs, GET /food-logs/daily/{date}, DELETE /food-logs/{id}
- ✅ Test: Log food, view diary, delete log, change date

**Time:** 10-12 hours (longer day)  
**Deliverables:** Complete food logging system

---

## **WEEK 2: Core Features + Recipes** (Days 6-10)

### **Day 6 (Mon): Profile & Goals**
**Goal:** User can edit profile and set goals
**Tasks:**
- ✅ Build Profile page:
  - Avatar upload (use placeholder if no time)
  - Edit form (full name, date of birth, gender, height, activity level)
  - BMI auto-calculation display
  - Save button
- ✅ Build Goals page (simple version):
  - Show active goal (goal type, current weight, target weight, calorie target)
  - Edit goal form (basic fields only)
  - Save button
- ✅ API integration: GET /users/profile, PATCH /users/profile, GET /goals/active, PATCH /goals/{id}
- ✅ Test: Update profile, update goal

**Time:** 6-8 hours  
**Deliverables:** Profile + Goals working

---

### **Day 7 (Tue): Recipes - List**
**Goal:** Browse and search recipes
**Tasks:**
- ✅ Build Recipe List page:
  - Grid view with recipe cards (image, name, cooking time, calories, favorite icon)
  - Search bar
  - Category filter
  - Sort by (Popular, Recent)
  - Pagination
  - Click card → navigate to detail
- ✅ API integration: GET /recipes?page=..., GET /recipes/search, GET /recipes/popular
- ✅ Favorite toggle: POST /recipes/{id}/favorite, DELETE /recipes/{id}/favorite
- ✅ Test: Search, filter, favorite works, navigate to detail

**Time:** 6-8 hours  
**Deliverables:** Recipe browsing working

---

### **Day 8 (Wed): Recipes - Detail**
**Goal:** View recipe details
**Tasks:**
- ✅ Build Recipe Detail page:
  - Recipe image (large)
  - Name + description
  - Favorite button (heart icon)
  - Recipe info (cooking time, servings - adjustable with dropdown)
  - Nutrition per serving (table)
  - Ingredients list (quantities adjust based on servings)
  - Instructions (step-by-step)
  - Back button
- ✅ API integration: GET /recipes/{id}
- ✅ Test: Servings adjustment recalculates ingredients, favorite toggle

**Time:** 6-8 hours  
**Deliverables:** Recipe detail working

---

### **Day 9 (Thu): Basic Analytics**
**Goal:** 2-3 essential charts only
**Tasks:**
- ✅ Install chart library (Recharts or Chart.js)
- ✅ Build Analytics page (SIMPLIFIED):
  - Date range selector (7/30 days only)
  - **Chart 1:** Calorie trend (line chart)
  - **Chart 2:** Macro distribution (pie chart: protein/carbs/fat %)
  - **Chart 3:** Weight progress (line chart if time allows)
- ✅ API integration: GET /analytics/nutrition-trends, GET /analytics/macro-distribution
- ✅ Test: Charts render, date range changes data

**Time:** 8-10 hours  
**Deliverables:** Basic analytics dashboard

---

### **Day 10 (Fri): Basic AI Chatbot**
**Goal:** Text chat with 3-4 function tools only
**Tasks:**
- ✅ Build Chatbot page:
  - Chat interface (message list, scrollable)
  - User messages (right, blue)
  - Bot messages (left, gray)
  - Input box + send button
  - Loading indicator when bot thinking
  - Suggested questions (3-4 chips)
- ✅ API integration: POST http://localhost:8001/chat/function-calling
- ✅ Implement detection for 3-4 critical function tools:
  1. **search_food** - Search food database
  2. **log_food** - Log food to diary
  3. **get_daily_insights** - Get progress summary
  4. **find_food_alternatives** - Find food alternatives
- ✅ Show function call results in special cards
- ✅ Test: Chat works, function calling detected, results displayed

**Time:** 8-10 hours  
**Deliverables:** Basic chatbot working with 3-4 tools

---

## **WEEK 3: Polish + Testing** (Days 11-15)

### **Day 11 (Sat): Responsive Design**
**Goal:** Works on mobile, tablet, desktop
**Tasks:**
- ✅ Test all pages on 3 screen sizes:
  - Mobile (375px - 767px)
  - Tablet (768px - 1023px)
  - Desktop (1024px+)
- ✅ Fix layout issues (use TailwindCSS breakpoints: sm:, md:, lg:)
- ✅ Test navigation (mobile hamburger menu, desktop sidebar)
- ✅ Ensure touch targets are 44px+ on mobile
- ✅ Test all forms on mobile

**Time:** 6-8 hours  
**Deliverables:** App responsive on all screens

---

### **Day 12 (Sun): Error Handling + Loading States**
**Goal:** Professional error handling
**Tasks:**
- ✅ Add try/catch to all API calls
- ✅ Show error messages using Alert/Toast component
- ✅ Add loading spinners to all async operations
- ✅ Add empty states ("No data yet" with icons)
- ✅ Add network error page (offline mode message)
- ✅ Add 404 page (route not found)
- ✅ Test: Disconnect network, trigger errors, check all states

**Time:** 4-6 hours  
**Deliverables:** Robust error handling

---

### **Day 13 (Mon): Performance + Optimization**
**Goal:** Fast and smooth app
**Tasks:**
- ✅ Use React.lazy() for code splitting (lazy load heavy pages)
- ✅ Debounce search inputs (already done Day 4)
- ✅ Optimize images (use lazy loading with loading="lazy")
- ✅ Use TanStack Query caching (configure staleTime, cacheTime)
- ✅ Test performance with Chrome DevTools (Lighthouse score)
- ✅ Fix any performance bottlenecks

**Time:** 4-6 hours  
**Deliverables:** Performance optimized

---

### **Day 14 (Tue): Testing + Bug Fixes**
**Goal:** Everything working smoothly
**Tasks:**
- ✅ Manual testing of all features:
  - Login → Dashboard → Log food → View diary → Edit goal → Search recipes → Favorite recipe → View analytics → Chat
- ✅ Test edge cases (empty states, no data, invalid inputs)
- ✅ Fix all bugs found
- ✅ Test on different browsers (Chrome, Firefox, Safari)
- ✅ Write test cases document (optional: automated tests with Vitest)

**Time:** 8-10 hours  
**Deliverables:** Stable app with no critical bugs

---

### **Day 15 (Wed): Deployment**
**Goal:** Web app live in production
**Tasks:**
- ✅ Build production version: `npm run build`
- ✅ Test production build locally: `npm run preview`
- ✅ Deploy to hosting:
  - **Option 1:** Vercel (easiest - connect GitHub, auto-deploy)
  - **Option 2:** Netlify (similar to Vercel)
  - **Option 3:** Nginx on server (manual)
- ✅ Configure environment variables (API URLs)
- ✅ Test production build (all features working)
- ✅ Share production URL

**Time:** 4-6 hours  
**Deliverables:** ✅ **Web app live at production URL**

---

# 📱 MOBILE DEVELOPER - 15 DAY PLAN

---

## **WEEK 1: Setup + Authentication + Core** (Days 1-5)

### **Day 1 (Wed): Flutter Project Setup**
**Goal:** Project initialized and running
**Tasks:**
- ✅ Initialize Flutter project: `flutter create nutriai_mobile`
- ✅ Add all dependencies to `pubspec.yaml`:
  - provider (state management)
  - dio (HTTP client)
  - shared_preferences (storage)
  - image_picker (camera)
  - fl_chart (charts)
  - json_annotation + build_runner (JSON serialization)
  - cached_network_image, shimmer, flutter_spinkit (UI)
  - go_router (navigation)
  - intl (date formatting)
- ✅ Run `flutter pub get`
- ✅ Create folder structure: models/, services/, providers/, screens/, widgets/, utils/, routes/
- ✅ Setup Dio client with interceptors (JWT token auto-attach)
- ✅ Create StorageService (SharedPreferences wrapper for tokens)
- ✅ Test: App runs on emulator/device

**Time:** 6-8 hours  
**Deliverables:** Flutter project setup complete

---

### **Day 2 (Thu): Data Models + Auth API**
**Goal:** Models and API clients ready
**Tasks:**
- ✅ Create data models (with JSON serialization):
  - User, UserProfile, UserGoal
  - Food, FoodLog
  - Recipe
  - (Others as needed)
- ✅ Run code generation: `flutter pub run build_runner build`
- ✅ Create API clients:
  - `auth_api.dart` (login, register, getMe, refresh)
  - `food_api.dart` (getFoods, getFoodById, searchFoods)
  - `food_log_api.dart` (logFood, getDailyLogs, updateLog, deleteLog)
  - `recipe_api.dart` (getRecipes, getRecipeById, favoriteRecipe)
  - `goal_api.dart` (getActiveGoal, updateGoal)
- ✅ Test: API calls work (use Postman/curl to verify)

**Time:** 8-10 hours  
**Deliverables:** Models + API clients complete

---

### **Day 3 (Fri): Authentication**
**Goal:** Users can login/register
**Tasks:**
- ✅ Create AuthProvider (state management):
  - login(), register(), logout(), checkAuth()
  - Store user + token
- ✅ Build Login screen:
  - Email + Password form
  - Form validation
  - Loading state
  - Error messages
  - "Register" link
- ✅ Build Register screen:
  - Email + Password + Confirm Password + Full Name
  - Validation
  - Success → navigate to login
- ✅ Test: Login → store token → navigate to home, Logout → clear token

**Time:** 8-10 hours  
**Deliverables:** Authentication working

---

### **Day 4 (Sat): Navigation + Dashboard**
**Goal:** Bottom nav + landing page
**Tasks:**
- ✅ Create Bottom Navigation Bar (5 tabs):
  - Home (Dashboard)
  - Foods
  - Diary
  - Chat
  - Profile
- ✅ Build Dashboard screen (simple version):
  - Welcome card with user name
  - Today's nutrition summary (calories, protein, carbs, fat)
  - Progress bars toward goals (LinearProgressIndicator)
  - Quick action buttons (Log Food, Browse Foods, Camera)
  - Recent logs (last 5, ListView)
- ✅ Create custom widgets: CustomCard, NutritionBar, QuickActionButton
- ✅ API integration: GET /food-logs/daily/today, GET /goals/active
- ✅ Test: Navigation works, dashboard loads data

**Time:** 8-10 hours  
**Deliverables:** Navigation + Dashboard working

---

### **Day 5 (Sun): Food Database**
**Goal:** Browse and search foods
**Tasks:**
- ✅ Build Food List screen:
  - ListView with InfiniteScroll (load more on scroll)
  - Search bar at top
  - Category filter (DropdownButton)
  - Food cards (name, category badge, calories)
  - Pull to refresh
  - Loading skeleton (Shimmer)
  - Tap card → navigate to detail
- ✅ Build Food Detail screen:
  - Food name (large title)
  - Category badge
  - Nutrition table (DataTable or custom table)
  - Serving sizes (if available)
  - "Add to Diary" button → navigate to logging screen
- ✅ API integration: GET /foods?page=..., GET /foods/{id}
- ✅ Test: Search, scroll load more, view detail, navigate back

**Time:** 8-10 hours  
**Deliverables:** Food browsing working

---

## **WEEK 2: Food Diary + Camera (Priority)** (Days 6-10)

### **Day 6 (Mon): Food Diary**
**Goal:** View daily food logs
**Tasks:**
- ✅ Build Food Diary screen:
  - Date picker at top (default: today)
  - 4 meal sections (Breakfast, Lunch, Dinner, Snack)
  - ExpansionTile for each meal
  - Food cards in each meal (food name, quantity, calories)
  - Swipe to delete (Dismissible widget)
  - Daily summary card at top (total calories, macros, progress bars)
  - FloatingActionButton to add food
- ✅ API integration: GET /food-logs/daily/{date}, DELETE /food-logs/{id}
- ✅ Test: View logs, change date, delete log

**Time:** 8-10 hours  
**Deliverables:** Food diary viewing working

---

### **Day 7 (Tue): Food Logging**
**Goal:** Add food to diary
**Tasks:**
- ✅ Build Food Logging screen (form):
  - Food name (passed from previous screen or search)
  - Serving size dropdown
  - Quantity input (TextField with number keyboard)
  - Meal type selector (4 chips: Breakfast/Lunch/Dinner/Snack)
  - Date picker (default: today)
  - **Real-time nutrition calculation** (display calories, protein, carbs, fat)
  - Save button
- ✅ API integration: POST /food-logs
- ✅ Test: Log food, nutrition calculates correctly, save, navigate back to diary

**Time:** 6-8 hours  
**Deliverables:** Food logging complete

---

### **Day 8 (Wed): Camera Integration - Part 1** ⭐
**Goal:** Camera working, capture photos
**Tasks:**
- ✅ Add permissions to AndroidManifest.xml and Info.plist:
  - Camera permission
  - Storage permission
- ✅ Build Vision screen:
  - Camera icon button on Dashboard
  - Option 1: Camera (take photo)
  - Option 2: Gallery (pick photo)
  - Show image preview after selection
  - "Analyze" button
  - Back button
- ✅ Implement image picker:
  ```dart
  final ImagePicker _picker = ImagePicker();
  XFile? image = await _picker.pickImage(source: ImageSource.camera);
  ```
- ✅ Test: Camera opens, photo captured, image displayed

**Time:** 6-8 hours  
**Deliverables:** Camera capture working

---

### **Day 9 (Thu): AI Vision Integration - Part 2** ⭐
**Goal:** AI analyzes food from photo
**Tasks:**
- ✅ Create AI API client (`ai_api.dart`):
  ```dart
  Future<VisionResult> analyzeFood(File image) async {
    final formData = FormData.fromMap({
      'image': await MultipartFile.fromFile(image.path),
    });
    final response = await dio.post(
      'http://10.0.2.2:8001/vision/analyze',
      data: formData,
    );
    return VisionResult.fromJson(response.data);
  }
  ```
- ✅ Update Vision screen:
  - Show loading indicator during analysis (5-10s)
  - Display result:
    - Food name (large text)
    - Nutrition table (calories, protein, carbs, fat)
    - Confidence score (optional)
  - Action buttons:
    - "Add to Diary" → navigate to food logging screen (pre-fill food info)
    - "Analyze Another" → reset screen
- ✅ API integration: POST /vision/analyze
- ✅ Test: Upload image, wait for result, result displays correctly, add to diary

**Time:** 8-10 hours  
**Deliverables:** ✅ **AI Vision working (KEY FEATURE)**

---

### **Day 10 (Fri): Recipes**
**Goal:** Browse and view recipes
**Tasks:**
- ✅ Build Recipe List screen:
  - GridView with recipe cards (image, name, cooking time, calories, favorite icon)
  - Search bar
  - Category filter
  - Tap card → navigate to detail
- ✅ Build Recipe Detail screen:
  - Recipe image (large)
  - Name + description
  - Favorite button
  - Recipe info (cooking time, servings)
  - Nutrition per serving
  - Ingredients list (simple ListView)
  - Instructions (step-by-step, numbered)
  - Back button
- ✅ API integration: GET /recipes, GET /recipes/{id}, POST /recipes/{id}/favorite
- ✅ Test: Browse, search, favorite, view detail

**Time:** 8-10 hours  
**Deliverables:** Recipes working

---

## **WEEK 3: Profile + Analytics + Polish** (Days 11-15)

### **Day 11 (Sat): Profile & Goals**
**Goal:** User can edit profile and goals
**Tasks:**
- ✅ Build Profile screen:
  - User avatar (CircleAvatar with placeholder)
  - Edit form (full name, date of birth, gender, height, activity level)
  - BMI display (auto-calculated)
  - Save button
- ✅ Build Goals screen (simple):
  - Show active goal (current weight, target weight, calorie target)
  - Edit button → open form sheet
  - Save button
- ✅ API integration: GET /users/profile, PATCH /users/profile, GET /goals/active, PATCH /goals/{id}
- ✅ Test: Update profile, update goal

**Time:** 6-8 hours  
**Deliverables:** Profile + Goals working

---

### **Day 12 (Sun): Basic Analytics**
**Goal:** 2-3 charts only
**Tasks:**
- ✅ Build Analytics screen (SIMPLIFIED):
  - Date range selector (7/30 days)
  - **Chart 1:** Calorie trend (LineChart from fl_chart)
  - **Chart 2:** Macro distribution (PieChart)
  - **Chart 3:** Weight progress (LineChart, if time allows)
- ✅ API integration: GET /analytics/nutrition-trends, GET /analytics/macro-distribution
- ✅ Test: Charts render, date range changes data

**Time:** 8-10 hours  
**Deliverables:** Basic analytics working

---

### **Day 13 (Mon): Basic Chatbot**
**Goal:** Text chat with 3-4 function tools
**Tasks:**
- ✅ Build Chatbot screen:
  - ListView for messages (reversed, scroll to bottom)
  - User message bubbles (right, blue)
  - Bot message bubbles (left, gray)
  - Input TextField + send button at bottom
  - Loading indicator when bot thinking
  - Suggested question chips (3-4)
- ✅ API integration: POST http://10.0.2.2:8001/chat/function-calling
- ✅ Implement detection for 3-4 critical tools:
  1. search_food
  2. log_food
  3. get_daily_insights
  4. find_food_alternatives
- ✅ Show function call results in special cards
- ✅ Test: Chat works, function calling detected

**Time:** 8-10 hours  
**Deliverables:** Basic chatbot working

---

### **Day 14 (Tue): Testing + Bug Fixes**
**Goal:** Everything working smoothly
**Tasks:**
- ✅ Manual testing of all features:
  - Login → Dashboard → Browse foods → Log food → View diary → Camera → Analyze food → Add to diary → View recipes → Edit profile → View analytics → Chat
- ✅ Test on real device (not just emulator)
- ✅ Test edge cases (no network, empty states, invalid inputs)
- ✅ Fix all bugs found
- ✅ Test permissions work (camera, storage)
- ✅ Polish UI (colors, spacing, fonts)

**Time:** 8-10 hours  
**Deliverables:** Stable app with no critical bugs

---

### **Day 15 (Wed): Build & Deploy**
**Goal:** APK ready for distribution
**Tasks:**
- ✅ Update app icon and splash screen
- ✅ Update app name in `android/app/src/main/AndroidManifest.xml`
- ✅ Build release APK:
  ```bash
  flutter build apk --release
  ```
- ✅ Test release build on real device
- ✅ Share APK file (located in `build/app/outputs/flutter-apk/app-release.apk`)
- ✅ (Optional) Build iOS if Mac available: `flutter build ios`
- ✅ Document installation instructions

**Time:** 4-6 hours  
**Deliverables:** ✅ **APK ready for testing/distribution**

---

## 📊 PROGRESS TRACKING

### **Daily Check-ins (Both Developers):**
- **Morning (9 AM):** What will you complete today?
- **Evening (6 PM):** What did you complete? Any blockers?
- **Use:** Shared Trello board or GitHub Projects

### **Weekly Demos:**
- **End of Week 1 (Day 5):** Demo auth + dashboard + food browsing
- **End of Week 2 (Day 10):** Demo diary + camera/vision + recipes
- **End of Week 3 (Day 15):** Demo complete app + analytics + chat

---

## 🚨 RISK MANAGEMENT

### **If Falling Behind:**
**Priority Cuts (in order):**
1. ❌ Skip analytics (Days 9, 12) → Use time for core features
2. ❌ Skip chatbot (Days 10, 13) → Save 1-2 days
3. ❌ Simplify recipes (no favorites, just list + detail)
4. ❌ Skip profile picture upload
5. ❌ Skip goals editing (just show active goal read-only)

**Non-Negotiable (Cannot Cut):**
- ✅ Authentication
- ✅ Food database
- ✅ Food logging & diary
- ✅ Camera + AI Vision (mobile)
- ✅ Dashboard

### **If Ahead of Schedule:**
**Add Back (in order):**
1. ✅ All 9 chatbot function tools (not just 3-4)
2. ✅ More analytics charts (7 charts instead of 2-3)
3. ✅ Favorite foods feature
4. ✅ Recipe shopping list
5. ✅ Meal planning AI

---

## � API ENDPOINTS QUICK REFERENCE

### **Backend API (http://localhost:8000/api/v1)**

**Authentication:**
```
POST   /auth/register     - Register new user
POST   /auth/login        - Login (returns JWT tokens)
POST   /auth/refresh      - Refresh access token
GET    /auth/me           - Get current user info
```

**Users & Profile:**
```
GET    /users/profile     - Get user profile
PATCH  /users/profile     - Update profile (name, height, gender, etc.)
```

**Foods:**
```
GET    /foods?page=1&limit=20&category=...&search=...  - List foods (paginated)
GET    /foods/{food_id}                                - Get food details
GET    /foods/search?q=...                             - Search foods
GET    /foods/{food_id}/servings                       - Get serving sizes
```

**Recipes:**
```
GET    /recipes?page=1&category=...        - List recipes
GET    /recipes/{recipe_id}                - Get recipe details
GET    /recipes/search?q=...               - Search recipes
GET    /recipes/popular                    - Get popular recipes
POST   /recipes/{recipe_id}/favorite       - Favorite recipe
DELETE /recipes/{recipe_id}/favorite       - Unfavorite recipe
GET    /recipes/favorites/my               - Get my favorites
```

**Food Logs:**
```
POST   /food-logs                      - Log food to diary
GET    /food-logs/daily/{date}         - Get all logs for date (YYYY-MM-DD)
GET    /food-logs/summary/{date}       - Get daily nutrition summary
PATCH  /food-logs/{log_id}             - Update log
DELETE /food-logs/{log_id}             - Delete log
```

**Goals:**
```
GET    /goals                  - Get all goals
GET    /goals/active           - Get active goal
POST   /goals                  - Create new goal
PATCH  /goals/{goal_id}        - Update goal
```

**Analytics:**
```
GET    /analytics/nutrition-trends?days=30         - Nutrition trends (line chart data)
GET    /analytics/macro-distribution?days=30       - Macro % distribution (pie chart)
GET    /analytics/weight-progress                  - Weight history (line chart)
GET    /analytics/meal-patterns?days=30            - Meal type patterns
GET    /analytics/food-frequency?days=30           - Top consumed foods
GET    /analytics/goal-progress                    - Goal progress %
```

### **AI Services (http://localhost:8001)**

**Vision (Food Recognition):**
```
POST   /vision/analyze         - Analyze food image (multipart/form-data)
                                 Body: { image: File }
                                 Response: { food_name, nutrition, confidence }
```

**Chat (Chatbot with Function Calling):**
```
POST   /chat/function-calling  - Chat with function tools
                                 Body: { query: "...", user_id: "..." }
                                 Response: { answer, function_called, function_result }
                                 
POST   /chat/with-vision       - Chat about food image
                                 Body: { query: "...", vision_context: {...} }
```

**Analytics (AI Insights):**
```
POST   /analytics/weekly-insights              - Get AI-generated weekly summary
       Body: { user_id: "..." }
       
POST   /analytics/goal-insights                - Get goal progress insights
       Body: { user_id: "..." }
```

**Nutrition (AI Search):**
```
POST   /nutrition/search                       - AI-powered food search
       Body: { query: "...", top_k: 10 }
```

---

## 🛠️ TECHNICAL TIPS

### **For Web Developer:**

**1. Environment Variables (.env):**
```
VITE_API_URL=http://localhost:8000/api/v1
VITE_AI_API_URL=http://localhost:8001
```

**2. API Client Example:**
```typescript
// src/api/client.ts
import axios from 'axios';

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
});

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default client;
```

**3. TanStack Query Usage:**
```typescript
// In component
const { data, isLoading, error } = useQuery({
  queryKey: ['foods', page, category],
  queryFn: () => foodAPI.getFoods({ page, category }),
  staleTime: 5 * 60 * 1000, // 5 minutes
});
```

**4. Form Validation Example:**
```typescript
const validateEmail = (email: string) => {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
};
```

### **For Mobile Developer:**

**1. API Base URLs (Android Emulator):**
```dart
// lib/utils/constants.dart
class ApiConstants {
  static const String baseUrl = 'http://10.0.2.2:8000/api/v1';  // Android emulator
  static const String aiBaseUrl = 'http://10.0.2.2:8001';
  
  // For iOS Simulator (if using):
  // static const String baseUrl = 'http://localhost:8000/api/v1';
}
```

**2. Dio Setup with JWT:**
```dart
// lib/services/api/dio_client.dart
class DioClient {
  final Dio dio = Dio(BaseOptions(
    baseUrl: ApiConstants.baseUrl,
    connectTimeout: Duration(seconds: 30),
    receiveTimeout: Duration(seconds: 30),
  ));

  DioClient() {
    dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = StorageService().getAccessToken();
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        return handler.next(options);
      },
    ));
  }
}
```

**3. State Management (Provider) Example:**
```dart
// In main.dart
void main() {
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider()),
        ChangeNotifierProvider(create: (_) => FoodProvider()),
        // ... more providers
      ],
      child: MyApp(),
    ),
  );
}

// In widget
final auth = Provider.of<AuthProvider>(context);
// or
final auth = context.read<AuthProvider>();
```

**4. Image Upload Example:**
```dart
Future<VisionResult> analyzeFood(File imageFile) async {
  final formData = FormData.fromMap({
    'image': await MultipartFile.fromFile(
      imageFile.path,
      filename: 'food.jpg',
    ),
  });
  
  final response = await dio.post('/vision/analyze', data: formData);
  return VisionResult.fromJson(response.data);
}
```

---

## 📝 COMMUNICATION PROTOCOL

### **Daily Sync (15 minutes):**
- **Time:** 9:00 AM every day
- **Format:** 
  - Yesterday: What did I complete?
  - Today: What will I complete?
  - Blockers: Any issues?

### **Code Collaboration:**
- **Git Branches:**
  - `main` - production (don't touch)
  - `develop` - integration branch
  - `feature/web-auth` - web feature branches
  - `feature/mobile-camera` - mobile feature branches
- **Commit Messages:**
  - `feat: Add login page`
  - `fix: Fix date picker bug`
  - `style: Update button colors`
- **Pull Requests:**
  - Create PR to `develop`
  - Request review from backend team or each other
  - Merge after approval

### **When to Ask for Help:**
- API returns unexpected response
- Backend endpoint not working
- Need clarification on feature
- Stuck on bug for > 1 hour

### **Communication Channels:**
- **Urgent:** Call/WhatsApp
- **Questions:** Telegram/Slack
- **Updates:** GitHub PR comments
- **Demos:** Weekly video call

---

## ✅ DEFINITION OF DONE (80% Complete)

### **Web App:**
- ✅ All 10 core features working
- ✅ Responsive on mobile, tablet, desktop
- ✅ No critical bugs
- ✅ Loading states everywhere
- ✅ Error handling implemented
- ✅ Deployed to production URL
- ✅ Can demo full user flow: Register → Log food → View diary → Search recipes → View analytics → Chat

### **Mobile App:**
- ✅ All 10 core features working
- ✅ Camera + AI Vision working (KEY FEATURE)
- ✅ Runs on Android (APK built)
- ✅ No critical bugs
- ✅ Permissions handled
- ✅ Loading states everywhere
- ✅ Can demo full user flow: Register → Camera → Analyze food → Log to diary → View analytics → Chat

---

## 🎯 SUCCESS METRICS

**Week 1 Complete:**
- ✅ Web: Auth + Dashboard + Food browsing
- ✅ Mobile: Auth + Navigation + Food browsing

**Week 2 Complete:**
- ✅ Web: Food diary + Recipes + Analytics + Chatbot
- ✅ Mobile: Food diary + Camera/Vision + Recipes

**Week 3 Complete:**
- ✅ Web: Polish + Testing + Deployed
- ✅ Mobile: Profile + Analytics + Chatbot + APK built

**Final Demo (Day 15):**
- ✅ Web app live at production URL
- ✅ Mobile APK ready for installation
- ✅ Both apps can complete all core user flows
- ✅ Backend team satisfied with integration
- ✅ Ready for user testing

---

## 🚀 POST-SPRINT (After 3 Weeks)

### **Remaining 20% (Nice to Have):**
These can be added in Sprint 2 (if time allows):
1. ❌ Meal Planning AI (AI-powered meal plan generation)
2. ❌ Admin Dashboard (for system monitoring)
3. ❌ All 9 chatbot function tools (currently only 3-4)
4. ❌ Advanced analytics (7 charts instead of 2-3)
5. ❌ Recipe shopping list & ingredient substitutions
6. ❌ Favorite foods quick-add
7. ❌ Copy meals from previous days
8. ❌ Dark mode
9. ❌ Social features (share recipes, follow users)
10. ❌ Barcode scanning (mobile)
11. ❌ Offline mode (local database)
12. ❌ Push notifications

### **Production Checklist (Before Public Launch):**
- ❌ Complete testing (unit + integration + E2E)
- ❌ Security audit
- ❌ Performance optimization (Lighthouse score > 90)
- ❌ SEO optimization (web)
- ❌ App store preparation (mobile - icons, screenshots, descriptions)
- ❌ Privacy policy & Terms of service
- ❌ Analytics tracking (Google Analytics, Firebase)
- ❌ Error monitoring (Sentry)
- ❌ User onboarding tutorial
- ❌ Help documentation

---

## 📚 RESOURCES

### **Documentation:**
- [Main README](../README.md) - System overview
- [Backend API Swagger](http://localhost:8000/docs) - Interactive API docs
- [AI Services Swagger](http://localhost:8001/docs) - AI API docs
- [Function Calling Guide](./FUNCTION_CALLING.md) - 9 chatbot tools
- [Vision-Chat Integration](./VISION_CHAT.md) - Camera + AI integration

### **Design Inspiration:**
- **MyFitnessPal** - Food diary layout
- **Lose It!** - Clean UI design
- **Lifesum** - Meal planning
- **Yazio** - Analytics dashboard
- **Noom** - Chatbot interaction

### **Component Libraries (Optional):**
- **Web:** HeadlessUI, Radix UI, shadcn/ui
- **Mobile:** Flutter Material Components

### **Chart Libraries:**
- **Web:** Recharts (recommended), Chart.js, Nivo
- **Mobile:** fl_chart (already in pubspec.yaml)

---

## ⚠️ COMMON PITFALLS TO AVOID

1. **Over-engineering:** Don't build perfect code, ship working features
2. **Scope creep:** Stick to 80% plan, say NO to extra features
3. **Perfectionism:** 80% working > 100% not finished
4. **No testing:** Test as you build, not at the end
5. **Poor time management:** Use daily check-ins, track progress
6. **Communication gaps:** Ask questions early, don't assume
7. **Git conflicts:** Pull from `develop` daily, commit often
8. **Skipping edge cases:** Test error states, empty states, loading states
9. **Hardcoding:** Use environment variables for API URLs
10. **Ignoring mobile:** Test responsive design from Day 1 (web)

---

## 💡 MOTIVATION

**Remember:**
- ✅ Backend + AI already 100% complete (huge advantage!)
- ✅ 641 foods + 198 recipes already seeded
- ✅ AI Vision working (tested)
- ✅ 9 function calling tools working
- ✅ Documentation complete

**You have:**
- ✅ Solid foundation to build on
- ✅ Clear APIs with examples
- ✅ Realistic 3-week plan
- ✅ Support from backend team

**3 weeks from now:**
- 🎉 Full-stack nutrition app LIVE
- 🎉 Camera AI food recognition working
- 🎉 Chatbot helping users
- 🎉 Users can track nutrition goals
- 🎉 Portfolio-ready project

---

## 🏁 FINAL CHECKLIST

### **Before Starting (Day 0):**
- ✅ Read this entire plan
- ✅ Understand 80% scope (what to build)
- ✅ Understand 20% cuts (what NOT to build)
- ✅ Setup development environment
- ✅ Test backend APIs with Postman/curl
- ✅ Clone repository
- ✅ Create feature branches
- ✅ Agree on daily sync time

### **During Sprint (Days 1-15):**
- ✅ Daily sync at 9 AM
- ✅ Follow day-by-day plan
- ✅ Commit code daily
- ✅ Test features as you build
- ✅ Ask questions when stuck
- ✅ Update progress on task board
- ✅ Weekly demos (Days 5, 10, 15)

### **Sprint Complete (Day 15):**
- ✅ Web app deployed and live
- ✅ Mobile APK built and tested
- ✅ All core features working
- ✅ No critical bugs
- ✅ Documentation updated
- ✅ Demo video recorded
- ✅ Repository clean (no unused code)

---

## 📞 SUPPORT CONTACTS

**Backend Team:**
- Available for API questions
- Can provide sample requests/responses
- Can adjust API if absolutely needed (discuss first)

**Project Manager/Lead:**
- Daily check-ins
- Unblock issues
- Review PRs

---

**Good luck! 🚀 You got this!**

**Start strong, stay focused, ship on time! 💪**
