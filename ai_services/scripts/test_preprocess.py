import sys
sys.path.insert(0, '/app')

from app.services.chat_service import ChatService

class FakeChatService(ChatService):
    def __init__(self):
        pass

svc = FakeChatService()
test_queries = [
    'Gợi ý bữa ăn sáng',
    'Món ăn giảm cân',
    'Nấu với thịt bò',
    'Thịt bò có bao nhiêu calories?',
    'cho tôi những món giàu protein'
]

for q in test_queries:
    processed = svc.preprocess_query(q)
    print(f'"{q}" -> "{processed}"')
