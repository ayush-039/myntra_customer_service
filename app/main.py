from app.pipeline import create_pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask

async def run_agent():
    try:
        pipeline = create_pipeline()
        task = PipelineTask(pipeline)
        runner = PipelineRunner()
        await runner.run(task)
    except KeyboardInterrupt:
        print("Shutting down gracefully...")
    except Exception as e:
        print(f"An error occurred: {e}")
        raise e 