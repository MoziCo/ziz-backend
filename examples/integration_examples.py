"""
Integration examples for the Ziz SDK.

This example demonstrates how to integrate the Ziz SDK with popular
AI frameworks and libraries like OpenAI, LangChain, Hugging Face, etc.
"""

import asyncio
import time
from typing import Any, Dict, List

# Import the Ziz SDK
import ziz


# Example 1: OpenAI Integration
def openai_integration_example():
    """Example showing integration with OpenAI API."""
    print("=== OpenAI Integration Example ===")

    # Initialize Ziz client
    client = ziz.Client(
        api_key="your-secret-key-change-in-production",
        feature_id="openai-chatbot",
        api_url="http://localhost:8000",
    )

    # Simulate OpenAI chat completion
    def simulate_openai_chat(messages: List[Dict[str, str]], model: str = "gpt-4"):
        """Simulate OpenAI chat completion."""
        # This would normally be: openai.ChatCompletion.create()
        simulated_response = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "I'm a helpful AI assistant. How can I help you today?",
                    }
                }
            ],
            "usage": {"prompt_tokens": 20, "completion_tokens": 15, "total_tokens": 35},
            "model": model,
            "id": "chatcmpl-123456",
        }
        return simulated_response

    # Wrapped function that logs to Ziz
    def chat_with_logging(messages: List[Dict[str, str]], model: str = "gpt-4"):
        """OpenAI chat with automatic Ziz logging."""
        # Call OpenAI API
        response = simulate_openai_chat(messages, model)

        # Extract response content
        assistant_message = response["choices"][0]["message"]["content"]

        # Log to Ziz
        output_id = client.log_output(
            content=assistant_message,
            metadata={
                "model": model,
                "prompt_tokens": response["usage"]["prompt_tokens"],
                "completion_tokens": response["usage"]["completion_tokens"],
                "total_tokens": response["usage"]["total_tokens"],
                "openai_id": response["id"],
                "prompt": messages[-1]["content"] if messages else "",
                "conversation_length": len(messages),
            },
        )

        print(f"OpenAI response logged: {output_id}")
        return assistant_message, output_id

    # Example conversation
    messages = [{"role": "user", "content": "What's the weather like today?"}]

    response, output_id = chat_with_logging(messages)
    print(f"Assistant: {response}")

    # Log user feedback
    client.thumbs_up(output_id, metadata={"feedback_source": "user_interface"})

    client.cleanup()


# Example 2: LangChain Integration
def langchain_integration_example():
    """Example showing integration with LangChain."""
    print("\n=== LangChain Integration Example ===")

    client = ziz.Client(
        api_key="your-secret-key-change-in-production",
        feature_id="langchain-pipeline",
        api_url="http://localhost:8000",
    )

    # Simulate LangChain chain execution
    class SimulatedLangChain:
        """Simulated LangChain class."""

        def __init__(self, chain_type: str):
            self.chain_type = chain_type

        def run(self, input_text: str) -> Dict[str, Any]:
            """Simulate chain execution."""
            return {
                "output": f"LangChain {self.chain_type} processed: {input_text}",
                "intermediate_steps": [
                    "Step 1: Input processing",
                    "Step 2: Model inference",
                    "Step 3: Output formatting",
                ],
                "chain_type": self.chain_type,
                "input_tokens": len(input_text.split()),
                "processing_time": 0.5,
            }

    # Wrapper that adds Ziz logging
    def run_chain_with_logging(chain, input_text: str, metadata: Dict[str, Any] = None):
        """Run LangChain with Ziz logging."""
        start_time = time.time()

        # Execute the chain
        result = chain.run(input_text)

        end_time = time.time()

        # Log the output to Ziz
        output_id = client.log_output(
            content=result["output"],
            metadata={
                "chain_type": result["chain_type"],
                "input_text": input_text,
                "input_tokens": result["input_tokens"],
                "processing_time": result["processing_time"],
                "actual_execution_time": end_time - start_time,
                "intermediate_steps_count": len(result["intermediate_steps"]),
                "framework": "langchain",
                **(metadata or {}),
            },
        )

        print(f"LangChain output logged: {output_id}")

        # Log intermediate steps as interactions
        for i, step in enumerate(result["intermediate_steps"]):
            client.log_interaction(
                type="intermediate_step",
                value=step,
                output_id=output_id,
                metadata={"step_index": i, "step_type": "processing"},
            )

        return result, output_id

    # Example usage
    chain = SimulatedLangChain("summarization")
    input_text = "This is a long document that needs to be summarized using LangChain."

    result, output_id = run_chain_with_logging(
        chain,
        input_text,
        metadata={"user_id": "user_123", "task": "document_summarization"},
    )

    print(f"Chain result: {result['output']}")

    client.cleanup()


# Example 3: Hugging Face Integration
def huggingface_integration_example():
    """Example showing integration with Hugging Face models."""
    print("\n=== Hugging Face Integration Example ===")

    client = ziz.Client(
        api_key="your-secret-key-change-in-production",
        feature_id="huggingface-nlp",
        api_url="http://localhost:8000",
    )

    # Simulate Hugging Face pipeline
    def simulate_hf_pipeline(task: str, model: str):
        """Simulate Hugging Face pipeline."""

        def pipeline_func(text: str):
            # This would normally be: pipeline = transformers.pipeline(task, model=model)
            if task == "sentiment-analysis":
                return [{"label": "POSITIVE", "score": 0.9998}]
            elif task == "text-generation":
                return [
                    {
                        "generated_text": f"{text} and this is the generated continuation."
                    }
                ]
            elif task == "summarization":
                return [{"summary_text": f"Summary: {text[:50]}..."}]
            else:
                return [{"output": f"Processed: {text}"}]

        return pipeline_func

    # Wrapper function with Ziz logging
    def hf_pipeline_with_logging(task: str, model: str):
        """Create HF pipeline with Ziz logging."""
        pipeline = simulate_hf_pipeline(task, model)

        def logged_pipeline(text: str, **kwargs):
            start_time = time.time()

            # Run the pipeline
            results = pipeline(text)

            end_time = time.time()

            # Extract the main result
            main_result = results[0] if results else {}

            # Log to Ziz
            output_id = client.log_output(
                content=main_result,
                metadata={
                    "task": task,
                    "model": model,
                    "input_text": text,
                    "input_length": len(text),
                    "processing_time": end_time - start_time,
                    "framework": "huggingface",
                    "num_results": len(results),
                    **kwargs,
                },
            )

            print(f"Hugging Face {task} logged: {output_id}")
            return results, output_id

        return logged_pipeline

    # Example: Sentiment Analysis
    sentiment_pipeline = hf_pipeline_with_logging(
        "sentiment-analysis", "distilbert-base-uncased"
    )

    text = "I love using the Ziz SDK for tracking my AI applications!"
    results, output_id = sentiment_pipeline(text)

    print(f"Sentiment: {results[0]}")

    # Log confidence as interaction
    client.log_interaction(
        type="confidence_score",
        value=results[0]["score"],
        output_id=output_id,
        metadata={"prediction": results[0]["label"]},
    )

    # Example: Text Generation
    generation_pipeline = hf_pipeline_with_logging("text-generation", "gpt2")
    prompt = "The future of AI is"

    gen_results, gen_output_id = generation_pipeline(prompt, max_length=50)
    print(f"Generated: {gen_results[0]['generated_text']}")

    client.cleanup()


# Example 4: MLflow Integration
def mlflow_integration_example():
    """Example showing integration with MLflow for experiment tracking."""
    print("\n=== MLflow Integration Example ===")

    client = ziz.Client(
        api_key="your-secret-key-change-in-production",
        feature_id="mlflow-experiments",
        api_url="http://localhost:8000",
    )

    # Simulate MLflow experiment
    class SimulatedMLflow:
        """Simulated MLflow experiment tracking."""

        @staticmethod
        def start_run():
            return {"run_id": "run_123456", "experiment_id": "exp_789"}

        @staticmethod
        def log_metric(key: str, value: float):
            print(f"MLflow metric: {key} = {value}")

        @staticmethod
        def log_param(key: str, value: Any):
            print(f"MLflow param: {key} = {value}")

        @staticmethod
        def end_run():
            print("MLflow run ended")

    def run_experiment_with_ziz(model_config: Dict[str, Any], data: List[str]):
        """Run ML experiment with both MLflow and Ziz tracking."""
        # Start MLflow run
        run_info = SimulatedMLflow.start_run()

        try:
            # Log parameters to MLflow
            for key, value in model_config.items():
                SimulatedMLflow.log_param(key, value)

            # Simulate model training/inference
            results = []
            for i, text in enumerate(data):
                # Simulate model prediction
                prediction = f"Prediction for: {text}"
                confidence = 0.85 + (i * 0.02)  # Varying confidence

                # Log to Ziz for each prediction
                output_id = client.log_output(
                    content=prediction,
                    metadata={
                        "model_config": model_config,
                        "input_text": text,
                        "confidence": confidence,
                        "mlflow_run_id": run_info["run_id"],
                        "mlflow_experiment_id": run_info["experiment_id"],
                        "prediction_index": i,
                    },
                )

                # Log confidence as interaction
                client.log_interaction(
                    type="model_confidence",
                    value=confidence,
                    output_id=output_id,
                    metadata={"metric_type": "confidence_score"},
                )

                results.append({
                    "prediction": prediction,
                    "confidence": confidence,
                    "ziz_output_id": output_id,
                })

            # Calculate aggregate metrics
            avg_confidence = sum(r["confidence"] for r in results) / len(results)

            # Log metrics to MLflow
            SimulatedMLflow.log_metric("avg_confidence", avg_confidence)
            SimulatedMLflow.log_metric("num_predictions", len(results))

            # Log experiment summary to Ziz
            summary_output_id = client.log_output(
                content={
                    "experiment_summary": {
                        "total_predictions": len(results),
                        "average_confidence": avg_confidence,
                        "model_config": model_config,
                    }
                },
                metadata={
                    "experiment_type": "ml_experiment",
                    "mlflow_run_id": run_info["run_id"],
                    "total_predictions": len(results),
                    "framework": "mlflow",
                },
            )

            print(f"Experiment summary logged: {summary_output_id}")
            return results

        finally:
            SimulatedMLflow.end_run()

    # Run example experiment
    model_config = {
        "model_type": "transformer",
        "learning_rate": 0.001,
        "batch_size": 32,
        "epochs": 10,
    }

    test_data = [
        "This is a positive review",
        "This product is terrible",
        "Average quality, nothing special",
        "Excellent service and product!",
    ]

    results = run_experiment_with_ziz(model_config, test_data)
    print(f"Completed experiment with {len(results)} predictions")

    client.cleanup()


# Example 5: FastAPI Integration
def fastapi_integration_example():
    """Example showing integration with FastAPI web service."""
    print("\n=== FastAPI Integration Example ===")

    # This would normally be in a FastAPI application
    # from fastapi import FastAPI, HTTPException
    # app = FastAPI()

    # Simulate FastAPI request/response
    class SimulatedFastAPI:
        def __init__(self):
            self.client = ziz.Client(
                api_key="your-secret-key-change-in-production",
                feature_id="fastapi-service",
                api_url="http://localhost:8000",
            )

        def predict_endpoint(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
            """Simulate FastAPI prediction endpoint."""
            start_time = time.time()

            # Simulate model prediction
            input_text = request_data.get("text", "")
            model_name = request_data.get("model", "default")

            # Simulate processing
            prediction = f"Processed: {input_text}"
            confidence = 0.92

            end_time = time.time()

            # Log to Ziz
            output_id = self.client.log_output(
                content=prediction,
                metadata={
                    "model": model_name,
                    "input_text": input_text,
                    "confidence": confidence,
                    "api_endpoint": "/predict",
                    "processing_time": end_time - start_time,
                    "framework": "fastapi",
                    "request_id": request_data.get("request_id", "unknown"),
                },
            )

            # Prepare response
            response = {
                "prediction": prediction,
                "confidence": confidence,
                "model": model_name,
                "ziz_output_id": output_id,
            }

            print(f"FastAPI prediction logged: {output_id}")
            return response

        def feedback_endpoint(
            self, output_id: str, feedback: str, metadata: Dict[str, Any] = None
        ):
            """Simulate FastAPI feedback endpoint."""
            interaction_id = self.client.log_interaction(
                type="api_feedback",
                value=feedback,
                output_id=output_id,
                metadata={
                    "api_endpoint": "/feedback",
                    "framework": "fastapi",
                    **(metadata or {}),
                },
            )

            print(f"FastAPI feedback logged: {interaction_id}")
            return {"interaction_id": interaction_id, "status": "logged"}

    # Example usage
    api = SimulatedFastAPI()

    # Simulate API requests
    prediction_request = {
        "text": "Analyze this text for sentiment",
        "model": "sentiment-v2",
        "request_id": "req_123",
    }

    prediction_response = api.predict_endpoint(prediction_request)
    print(f"API Response: {prediction_response}")

    # Simulate feedback
    feedback_response = api.feedback_endpoint(
        output_id=prediction_response["ziz_output_id"],
        feedback="accurate",
        metadata={"user_id": "user_456", "session_id": "session_789"},
    )
    print(f"Feedback Response: {feedback_response}")


# Example 6: Streamlit Integration
def streamlit_integration_example():
    """Example showing integration with Streamlit."""
    print("\n=== Streamlit Integration Example ===")

    # This would normally be in a Streamlit app
    # import streamlit as st

    class SimulatedStreamlit:
        """Simulated Streamlit application."""

        def __init__(self):
            self.client = ziz.Client(
                api_key="your-secret-key-change-in-production",
                feature_id="streamlit-app",
                api_url="http://localhost:8000",
            )
            # Simulate session state
            self.session_state = {"last_output_id": None}

        def text_analysis_app(self):
            """Simulate Streamlit text analysis app."""
            print("=== Streamlit Text Analysis App ===")

            # Simulate user input
            user_text = "This is a sample text for analysis"
            analysis_type = "sentiment"

            print(f"User input: {user_text}")
            print(f"Analysis type: {analysis_type}")

            if user_text:  # Simulate button click
                # Perform analysis
                if analysis_type == "sentiment":
                    result = {"sentiment": "positive", "confidence": 0.89}
                elif analysis_type == "summary":
                    result = {"summary": f"Summary of: {user_text[:30]}..."}
                else:
                    result = {"analysis": f"Generic analysis of: {user_text}"}

                # Log to Ziz
                output_id = self.client.log_output(
                    content=result,
                    metadata={
                        "app_type": "streamlit",
                        "analysis_type": analysis_type,
                        "input_text": user_text,
                        "input_length": len(user_text),
                        "framework": "streamlit",
                    },
                )

                # Store in session state
                self.session_state["last_output_id"] = output_id

                print(f"Analysis result: {result}")
                print(f"Logged to Ziz: {output_id}")

                # Simulate feedback buttons
                self.add_feedback_buttons(output_id)

        def add_feedback_buttons(self, output_id: str):
            """Simulate Streamlit feedback buttons."""
            print("\n--- Feedback Buttons ---")

            # Simulate user clicking thumbs up
            feedback_type = "thumbs_up"  # This would come from user interaction

            if feedback_type:
                interaction_id = self.client.log_interaction(
                    type="streamlit_feedback",
                    value=feedback_type,
                    output_id=output_id,
                    metadata={
                        "feedback_method": "button_click",
                        "framework": "streamlit",
                    },
                )

                print(f"User feedback '{feedback_type}' logged: {interaction_id}")

    # Run simulated Streamlit app
    app = SimulatedStreamlit()
    app.text_analysis_app()


async def main():
    """Run all integration examples."""
    print("Ziz SDK Integration Examples")
    print("============================")
    print("Make sure your Ziz API is running on http://localhost:8000")
    print()

    try:
        openai_integration_example()
        langchain_integration_example()
        huggingface_integration_example()
        mlflow_integration_example()
        fastapi_integration_example()
        streamlit_integration_example()

        print("\n✅ All integration examples completed successfully!")

    except Exception as e:
        print(f"\n❌ Integration example failed: {e}")
        print("Make sure your Ziz API is running and accessible.")


if __name__ == "__main__":
    asyncio.run(main())
