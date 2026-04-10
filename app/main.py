import asyncio
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask
from pipecat.frames.frames import LLMMessagesUpdateFrame

from app.pipeline import create_pipeline

async def main():
    pipeline = await create_pipeline()
    task = PipelineTask(pipeline)
    runner = PipelineRunner()

    # ✅ AI speaks first
    # print("AI speaking first...")

    # await task.queue_frame(
    #     LLMMessagesUpdateFrame(
    #         messages=[
    #             {
    #                 "role": "user",
    #                 "content": "Greet the user as Myntra customer support"
    #             }
    #         ],
    #         run_llm=True
    #     )
    # )

    await runner.run(task)

if __name__ == "__main__":
    asyncio.run(main())