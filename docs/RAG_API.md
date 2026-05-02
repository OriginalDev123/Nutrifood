# RAG API - Quick Reference

> **Status:** ✅ Production Ready | **Version:** 1.0.0 | **Last Updated:** March 5, 2026

## 📋 Overview

Quick RAG (Retrieval Augmented Generation) endpoint for nutrition Q&A. Combines semantic search with Gemini 2.5 Flash to answer questions about foods and recipes.

**Key Features:**
- 🔍 Semantic search across 839 documents (641 foods + 198 recipes)
- 🤖 Gemini 2.5 Flash for natural language answers
- 🇻🇳 Optimized for Vietnamese queries
- ⚡ Fast response (1.6-3.7s average)
- 💯 No API costs for embeddings (local model)

---

## Endpoint: `/chat/rag`

### Request

**Method:** `POST`  
**URL:** `http://localhost:8001/chat/rag?question={your_question}`  
**Headers:** `Content-Type: application/json`

### Parameters

- `question` (string, required): Nutrition question in Vietnamese or English

### Response

```json
{
  "question": "Thịt bò có bao nhiêu calories?",
  "processed_query": "Thịt bò calories",
  "answer": "100g thịt bò có chứa **250.0 kcal**.",
  "sources": [
    "Thịt bò - Beef",
    "Bơ lạt - Unsalted Butter"
  ],
  "retrieved": 3,
  "processing_ms": 3668
}
```

### Features

✅ **Query Preprocessing** - Removes Vietnamese question words for better search  
✅ **Optimized Threshold** - 0.35 for Vietnamese diacritics  
✅ **Local Embeddings** - 384D sentence-transformers (no API costs)  
✅ **Gemini 2.5 Flash** - Latest stable model  
✅ **Fast Response** - 1.6-3.7s average  

### Examples

#### Python (requests)

```python
import requests

response = requests.post(
    "http://localhost:8001/chat/rag",
    params={"question": "Thịt bò có bao nhiêu calories?"}
)

data = response.json()
print(data['answer'])
# Output: 100g thịt bò có chứa **250.0 kcal**.
```

#### JavaScript (fetch)

```javascript
const response = await fetch(
  'http://localhost:8001/chat/rag?question=Cánh%20gà%20protein%20bao%20nhiêu?',
  { method: 'POST', headers: { 'Content-Type': 'application/json' } }
);

const data = await response.json();
console.log(data.answer);
// Output: Cánh gà cung cấp **18.0g protein**/100g.
```

#### cURL

```bash
curl -X POST "http://localhost:8001/chat/rag?question=Cam%20có%20vitamin%20C%20không?" \
  -H "Content-Type: application/json"
```

### Test Queries

- ✅ "Thịt bò có bao nhiêu calories?" → 250.0 kcal
- ✅ "Cánh gà protein bao nhiêu?" → 18.0g  
- ✅ "Cam có chứa vitamin C không?" → Có, rất nhiều
- ✅ "Cơm trắng carbs" → 28.2g
- ✅ "Sữa tươi có đường không?" → No data (correct - not in DB)

### Query Preprocessing

The endpoint automatically optimizes Vietnamese questions:

| Original | Processed |
|----------|-----------|
| "Thịt bò có bao nhiêu calories?" | "Thịt bò calories" |
| "Cam có chứa vitamin C không?" | "Cam vitamin C" |
| "Cơm trắng carbs bao nhiêu?" | "Cơm trắng carbs" |

This improves semantic search accuracy for Vietnamese queries.

### Technical Details

- **Embedding Model:** sentence-transformers/all-MiniLM-L6-v2 (384D)
- **Vector Database:** Qdrant (839 documents: 641 foods + 198 recipes)
- **LLM:** Gemini 2.5 Flash
- **Search Threshold:** 0.35 (optimized for Vietnamese)
- **Top-K:** 3 documents
- **Context Window:** Full content (no truncation)

### Error Handling

**400 Bad Request** - Empty question  
**500 Internal Server Error** - Processing failure  
**503 Service Unavailable** - Service not initialized

### Performance

- **Average Response Time:** 1.6-3.7s
- **Embedding Time:** ~500ms
- **Search Time:** ~100ms  
- **Generation Time:** ~1-3s (Gemini)

---

## Integration with Frontend

### React Example

```tsx
import { useState } from 'react';

function NutritionChat() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);

  const askQuestion = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `http://localhost:8001/chat/rag?question=${encodeURIComponent(question)}`,
        { method: 'POST', headers: { 'Content-Type': 'application/json' } }
      );
      const data = await response.json();
      setAnswer(data.answer);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <input
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="Hỏi về dinh dưỡng..."
      />
      <button onClick={askQuestion} disabled={loading}>
        {loading ? 'Đang xử lý...' : 'Hỏi'}
      </button>
      {answer && <div>{answer}</div>}
    </div>
  );
}
```

---

**Status:** ✅ Production Ready  
**Last Updated:** 2026-03-05  
**Tested:** 5/5 queries successful
