import asyncio
from app.routers.assistant import AskRequest, CommandRequest
from app.routers.assistant import ask_assistant, pastor_command

class MockUser:
    id = "test_user_id"
    church_id = "test_church_id"
    role = "pastor"

class MockCongregation:
    id = "test_user_id"
    church_id = "test_church_id"
    role = "member"

class MockDB:
    def query(self, *args, **kwargs):
        class MockQuery:
            def filter(self, *args, **kwargs):
                return self
            def order_by(self, *args, **kwargs):
                return self
            def limit(self, *args, **kwargs):
                return self
            def all(self, *args, **kwargs):
                return []
            def update(self, *args, **kwargs):
                pass
        return MockQuery()
    def add(self, *args, **kwargs):
        pass
    def commit(self, *args, **kwargs):
        pass

async def test_assistant():
    db = MockDB()
    pastor = MockUser()
    print("Testing Pastor Command...")
    req1 = CommandRequest(command="Set the main verse to John 3:16")
    try:
        res1 = await pastor_command(req1, pastor, db)
        print("Pastor Response:", res1)
    except Exception as e:
        print("Pastor Command Failed:", e)

    member = MockCongregation()
    print("\nTesting Congregation Ask...")
    req2 = AskRequest(query="What is the shortest verse in the Bible?")
    try:
        res2 = await ask_assistant(req2, member, db)
        print("Congregation Response:", res2)
    except Exception as e:
        print("Congregation Ask Failed:", e)

if __name__ == "__main__":
    asyncio.run(test_assistant())
