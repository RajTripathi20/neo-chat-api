"""
Request processing pipeline module.

This module implements a processing pipeline for chat completion requests,
following the Chain of Responsibility pattern to allow for flexible processing
of requests through multiple steps.
"""

import time
import uuid
import json
from typing import List, Dict, Any, AsyncGenerator
from src.models.api_models import (
    ChatRequest, ChatResponse, Choice, Message, Usage,
    StreamingChatResponse, StreamingChoice, StreamingDelta
)
from src.providers.openrouter import RouterClient
from src.services.accounting import credit_manager
from src.utils.constants.messages import (
    ROLE_ASSISTANT, 
    FINISH_REASON_STOP
)


# Initialize OpenRouter client
router_client = RouterClient()

class ProcessingStep:
    """
    Base class for processing steps in the pipeline.
    
    This class defines the interface for all processing steps and
    provides a default implementation that passes the request through unchanged.
    """
    
    async def execute(self, request: ChatRequest) -> ChatRequest:
        """
        Execute the processing step.
        
        Args:
            request: The chat completion request to process.
            
        Returns:
            ChatRequest: The processed request.
        """
        return request

class SanitizationFilter(ProcessingStep):
    """
    Filter out harmful content from the request.
    
    This step sanitizes the request by filtering out harmful content
    from the messages.
    """
    
    async def execute(self, request: ChatRequest) -> ChatRequest:
        """
        Execute the sanitization filter.
        
        Args:
            request: The chat completion request to sanitize.
            
        Returns:
            ChatRequest: The sanitized request.
        """
        # Simple implementation - in a real system, this would be more sophisticated
        for message in request.messages:
            # Replace any harmful content with [FILTERED]
            # This is just a placeholder for demonstration
            pass
        return request

class IntentClassifier(ProcessingStep):
    """
    Classify the intent of the request.
    
    This step analyzes the request to determine the user's intent,
    which can be used to route the request to the appropriate handler.
    """
    
    async def execute(self, request: ChatRequest) -> ChatRequest:
        """
        Execute the intent classifier.
        
        Args:
            request: The chat completion request to classify.
            
        Returns:
            ChatRequest: The classified request.
        """
        # Simple implementation - in a real system, this would use ML models
        # This is just a placeholder for demonstration
        return request

class ContentProcessor:
    """
    Process the content of the request through a series of steps.
    
    This class manages a pipeline of processing steps that are applied
    to the request in sequence.
    """
    
    def __init__(self):
        """
        Initialize the content processor with a list of processing steps.
        """
        self.steps = [
            SanitizationFilter(),
            IntentClassifier(),
        ]
    
    async def process(self, request: ChatRequest) -> ChatRequest:
        """
        Process the request through all steps in the pipeline.
        
        Args:
            request: The chat completion request to process.
            
        Returns:
            ChatRequest: The processed request.
        """
        for step in self.steps:
            request = await step.execute(request)
        return request

# Create a singleton instance
content_processor = ContentProcessor()

class ResponseBuilder:
    """
    Build a response from the result of a request.
    
    This class is responsible for constructing the response object
    from the result of processing a request.
    """
    
    @staticmethod
    async def build_response(result: Dict[str, Any]) -> ChatResponse:
        """
        Build a chat completion response.
        
        Args:
            result: The result of processing the request.
            
        Returns:
            ChatResponse: The chat completion response.
        """
        # Create message with reasoning if available
        message = Message(
            role=ROLE_ASSISTANT,
            content=result["content"]
        )
        
        # Add reasoning if available
        if result.get("reasoning"):
            message.reasoning = result["reasoning"]
        
        # Create response
        response = ChatResponse(
            id=f"chatcmpl-{uuid.uuid4()}",
            created=int(time.time()),
            model=result["model"],
            choices=[
                Choice(
                    index=0,
                    message=message,
                    finish_reason=FINISH_REASON_STOP
                )
            ],
            usage=Usage(
                prompt_tokens=result["usage"]["prompt_tokens"],
                completion_tokens=result["usage"]["completion_tokens"],
                total_tokens=result["usage"]["total_tokens"],
                total_cost=result["cost"],
                model_id=result["usage"].get("model_id"),
                provider=result["usage"].get("provider"),
                generation_id=result["usage"].get("generation_id"),
                generation_time=result["usage"].get("generation_time")
            )
        )
        
        return response

class UsageRecorder:
    """
    Record usage information for billing purposes.
    
    This class is responsible for recording usage information
    for billing and analytics purposes.
    """
    
    @staticmethod
    async def record_usage(user_id: str, result: Dict[str, Any]) -> None:
        """
        Record usage information.
        
        Args:
            user_id: The ID of the user.
            result: The result of processing the request.
        """
        await credit_manager.deduct_credits(
            user_id=user_id,
            amount=result["cost"],
            description=f"Chat completion with {result['model']}",
            metadata={
                "model": result["model"],
                "tokens": result["usage"]["total_tokens"],
                "prompt_tokens": result["usage"]["prompt_tokens"],
                "completion_tokens": result["usage"]["completion_tokens"],
            }
        )

async def process_request(request: ChatRequest) -> ChatResponse:
    """
    Process the request through the pipeline and return the response.
    
    This function coordinates the processing of a request through the pipeline,
    calls the external API, builds the response, and records usage information.
    
    Args:
        request: The chat completion request to process.
        
    Returns:
        ChatResponse: The chat completion response.
    """
    # Process the request through the pipeline
    processed_request = await content_processor.process(request)
    
    # Call OpenRouter API
    result = await router_client.chat(processed_request)
    
    # Build response
    response = await ResponseBuilder.build_response(result)
    
    # Record usage for billing
    user_id = getattr(request, "user", "anonymous")
    await UsageRecorder.record_usage(user_id, result)
    
    return response

class StreamingResponseBuilder:
    """
    Build streaming responses from the results of a request.
    
    This class is responsible for constructing streaming response objects
    from the results of processing a request.
    """
    
    @staticmethod
    async def build_streaming_responses(request: ChatRequest, result_generator) -> AsyncGenerator[StreamingChatResponse, None]:
        """
        Build streaming chat completion responses.
        
        Args:
            request: The chat completion request.
            result_generator: A generator that yields results.
            
        Yields:
            StreamingChatResponse: Streaming chat completion responses.
        """
        response_id = f"chatcmpl-{uuid.uuid4()}"
        created = int(time.time())
        
        async for result in result_generator:
            # Create streaming response
            streaming_response = StreamingChatResponse(
                id=response_id,
                created=created,
                model=result["model"],
                choices=[
                    StreamingChoice(
                        index=0,
                        delta=StreamingDelta(
                            content=result.get("content"),
                            role=result.get("role"),
                            reasoning=result.get("reasoning")
                        ),
                        finish_reason=result.get("finish_reason")
                    )
                ]
            )
            
            # Add usage information to the final chunk
            if result.get("is_final"):
                streaming_response.usage = Usage(
                    prompt_tokens=result["usage"]["prompt_tokens"],
                    completion_tokens=result["usage"]["completion_tokens"],
                    total_tokens=result["usage"]["total_tokens"],
                    total_cost=result["cost"],
                    model_id=result["usage"].get("model_id"),
                    provider=result["usage"].get("provider"),
                    generation_id=result["usage"].get("generation_id"),
                    generation_time=result["usage"].get("generation_time")
                )
                
                # Record usage for billing
                user_id = getattr(request, "user", "anonymous")
                await UsageRecorder.record_usage(user_id, result)
            
            yield streaming_response

async def process_streaming_request(request: ChatRequest) -> AsyncGenerator[StreamingChatResponse, None]:
    """
    Process the streaming request through the pipeline and yield responses.
    
    This function coordinates the processing of a streaming request through the pipeline,
    calls the external API, and yields streaming responses.
    
    Args:
        request: The chat completion request to process.
        
    Yields:
        StreamingChatResponse: Streaming chat completion responses.
    """
    # Process the request through the pipeline
    processed_request = await content_processor.process(request)
    
    # Call OpenRouter API with streaming
    result_generator = router_client.chat_stream(processed_request)
    
    # Yield streaming responses
    async for response in StreamingResponseBuilder.build_streaming_responses(request, result_generator):
        yield response 