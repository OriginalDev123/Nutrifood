#!/usr/bin/env python3
"""
Seed Qdrant vector database with food and recipe data
Uses local embeddings (sentence-transformers)
"""

import sys
import os
sys.path.insert(0, '/app')

import asyncio
import httpx
from app.services.local_embedding_service import get_local_embedding_service
from app.services.retrieval_service import RetrievalService

# Database connection details
BACKEND_URL = os.getenv('BACKEND_API_URL') or os.getenv('BACKEND_URL', 'http://backend:8000')


async def fetch_foods():
    """Fetch all foods from backend with pagination"""
    print("📥 Fetching foods from database...")
    all_foods = []
    skip = 0
    limit = 100  # Max allowed by API
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            response = await client.get(
                f"{BACKEND_URL}/foods?skip={skip}&limit={limit}&verified_only=false"
            )
            if response.status_code != 200:
                if skip == 0:  # Only error on first fetch
                    print(f"❌ Error fetching foods: {response.status_code}")
                break
            
            data = response.json()
            foods = data.get('foods', [])
            all_foods.extend(foods)
            
            # Check if we got all data
            total = data.get('total', 0)
            if len(all_foods) >= total or len(foods) < limit:
                break
            
            skip += limit
    
    print(f"✅ Fetched {len(all_foods)} foods")
    return all_foods


async def fetch_recipes():
    """Fetch all recipes from backend with pagination"""
    print("\n📥 Fetching recipes from database...")
    all_recipes = []
    skip = 0
    limit = 100  # Max allowed by API
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            response = await client.get(
                f"{BACKEND_URL}/recipes",
                params={"skip": skip, "limit": limit}
            )
            if response.status_code != 200:
                if skip == 0:  # Only error on first fetch
                    print(f"❌ Error fetching recipes: {response.status_code}")
                break
            
            recipes = response.json()
            if not isinstance(recipes, list):
                break

            all_recipes.extend(recipes)

            # If we got less than limit, we're done
            if len(recipes) < limit:
                break
            
            skip += limit
    
    print(f"✅ Fetched {len(all_recipes)} recipes")
    return all_recipes


def prepare_food_documents(foods):
    """Prepare food data for embedding"""
    documents = []
    
    for food in foods:
        food_id = food.get('food_id')
        if not food_id:
            continue  # Skip if no ID
            
        # Create rich text content for better semantic search
        content = f"""
        {food.get('name_vi', '')} ({food.get('name_en', '')})
        
        Nutrition per 100g:
        - Calories: {food.get('calories_per_100g', 0)} kcal
        - Protein: {food.get('protein_per_100g', 0)}g
        - Carbs: {food.get('carbs_per_100g', 0)}g
        - Fat: {food.get('fat_per_100g', 0)}g
        - Fiber: {food.get('fiber_per_100g', 0)}g
        
        Category: {food.get('category', 'Unknown')}
        Description: {food.get('description', '')}
        """.strip()
        
        # Match RetrievalService expected format: id, title, content, source
        documents.append({
            'id': food_id,
            'title': f"{food.get('name_vi', '')} - {food.get('name_en', '')}",
            'content': content,
            'source': 'foods_database',
            # Additional metadata in payload
            'type': 'food',
            'category': food.get('category', 'Unknown'),
            'calories': food.get('calories_per_100g', 0),
            'protein': food.get('protein_per_100g', 0),
            'carbs': food.get('carbs_per_100g', 0),
            'fat': food.get('fat_per_100g', 0)
        })
    
    return documents


def prepare_recipe_documents(recipes):
    """Prepare recipe data for embedding"""
    documents = []
    
    for recipe in recipes:
        recipe_id = recipe.get('recipe_id')
        if not recipe_id:
            continue  # Skip if no ID
            
        # Extract instructions from steps
        instructions_steps = recipe.get('instructions_steps', [])
        if isinstance(instructions_steps, list):
            instructions_text = ' '.join([step.get('text', '') for step in instructions_steps])
        else:
            instructions_text = str(recipe.get('instructions', ''))
        
        # Build rich content for semantic search
        content = f"""
        Recipe: {recipe.get('name_vi', '')} ({recipe.get('name_en', '')})
        
        Description: {recipe.get('description', '')}
        
        Category: {recipe.get('category', '')}
        Cuisine: {recipe.get('cuisine_type', '')}
        
        Nutrition per serving:
        - Calories: {recipe.get('calories_per_serving', 0)} kcal
        
        Servings: {recipe.get('servings', 1)}
        Prep time: {recipe.get('prep_time_minutes', 0)} mins
        Cook time: {recipe.get('cook_time_minutes', 0)} mins
        Difficulty: {recipe.get('difficulty_level', 'easy')}
        
        Instructions: {instructions_text[:300]}
        Tags: {', '.join(recipe.get('tags', []))}
        """.strip()
        
        # Match RetrievalService expected format: id, title, content, source
        documents.append({
            'id': recipe_id,
            'title': f"Recipe: {recipe.get('name_vi', '')} - {recipe.get('name_en', '')}",
            'content': content,
            'source': 'recipes_database',
            # Additional metadata in payload
            'type': 'recipe',
            'category': recipe.get('category', ''),
            'calories': float(recipe.get('calories_per_serving', 0)),
            'servings': recipe.get('servings', 1),
            'difficulty': recipe.get('difficulty_level', 'easy')
        })
    
    return documents


async def seed_database():
    """Main seeding function"""
    print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌱 SEEDING QDRANT WITH FOOD & RECIPE DATA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """)
    
    # Initialize services
    print("🔧 Initializing services...")
    embedding_service = get_local_embedding_service()
    qdrant_url = os.getenv('QDRANT_URL', 'http://qdrant:6333')
    retrieval_service = RetrievalService(qdrant_url=qdrant_url, embedding_service=embedding_service)
    print(f"✅ Services ready (embedding dimension: {embedding_service.get_embedding_dimension()}D)")
    
    # Fetch data
    foods = await fetch_foods()
    recipes = await fetch_recipes()
    
    if not foods and not recipes:
        print("\n❌ No data to seed!")
        return
    
    # Prepare documents
    print("\n📦 Preparing documents...")
    food_docs = prepare_food_documents(foods)
    recipe_docs = prepare_recipe_documents(recipes)
    all_docs = food_docs + recipe_docs
    print(f"✅ Prepared {len(food_docs)} food docs + {len(recipe_docs)} recipe docs = {len(all_docs)} total")
    
    # Store in Qdrant (RetrievalService will handle embeddings internally)
    print("\n💾 Storing in Qdrant (this may take 30-60 seconds for embeddings)...")
    try:
        retrieval_service.create_collection(recreate=True)
        count = retrieval_service.add_documents(all_docs)
        print(f"✅ Successfully stored {count} documents in Qdrant!")
    except Exception as e:
        print(f"❌ Error storing documents: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Verify
    print("\n🔍 Verifying storage...")
    collection_info = retrieval_service.get_collection_info()
    points_count = collection_info.get('vectors_count', 0)
    print(f"✅ Qdrant now contains {points_count} vectors")
    
    # Test search
    print("\n🧪 Testing semantic search...")
    test_queries = [
        "Phở bò có bao nhiêu calo?",
        "Món ăn nhiều protein",
        "Recipes for weight loss"
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: '{query}'")
        results = retrieval_service.search(query, top_k=3)
        for i, result in enumerate(results, 1):
            title = result.get('title', 'Unknown')
            score = result.get('score', 0)
            source = result.get('source', 'unknown')
            print(f"   {i}. {title} ({source}) - Score: {score:.3f}")
    
    print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ SEEDING COMPLETE!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Summary:
- Foods indexed: {len(food_docs)}
- Recipes indexed: {len(recipe_docs)}
- Total vectors: {points_count}
- Embedding model: all-MiniLM-L6-v2 (384D)
- Status: READY FOR RAG CHATBOT! 🚀

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """)


if __name__ == "__main__":
    asyncio.run(seed_database())
