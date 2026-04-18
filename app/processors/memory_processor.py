from pipecat.processors.frame_processor import FrameProcessor

class MemoryProcessor(FrameProcessor):
    def __init__(self, memory):
        super().__init__()
        self.memory = memory

    async def process_frame(self, frame, direction):   # ✅ FIXED

        if hasattr(frame, "text"):

            # User speech
            if frame.__class__.__name__ == "TranscriptionFrame":
                print(f"\n👤 User: {frame.text}")
                self.memory.append({
                    "role": "user",
                    "content": frame.text
                })

            # AI response
            elif frame.__class__.__name__ == "LLMResponseFrame":
                print(f"\n🧠 AI: {frame.text}")
                self.memory.append({
                    "role": "assistant",
                    "content": frame.text
                })

        # ✅ MUST pass direction
        await self.push_frame(frame, direction)