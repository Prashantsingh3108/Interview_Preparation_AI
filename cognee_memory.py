import os
import cognee
from dotenv import load_dotenv

load_dotenv()

class CogneeMemory:

    def __init__(self):
        self.initialized = False

    async def initialize(self):
        if not self.initialized:
            await cognee.serve(
                api_key=os.getenv("COGNEE_API_KEY")
            )
            self.initialized = True