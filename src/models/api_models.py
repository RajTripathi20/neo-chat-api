from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from src.utils.constants.models import (
    DEFAULT_MODEL, 
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE, 
    DEFAULT_TOP_P, 
    DEFAULT_N, 
    DEFAULT_STREAM,
    DEFAULT_PRESENCE_PENALTY, 
    DEFAULT_FREQUENCY_PENALTY
)
from src.utils.constants.messages import (
    ROLE_USER,
    DEFAULT_USER_MESSAGE
)
from src.utils.constants.api import (
    CHAT_COMPLETION_OBJECT, 
    CHAT_COMPLETION_CHUNK_OBJECT, 
    MODELS_LIST_OBJECT
)

class Message(BaseModel):
    """
    Represents a message in a chat conversation.
    
    Attributes:
        role: The role of the message sender (user, assistant, system)
        content: The content of the message
        name: Optional name of the sender
        reasoning: Optional reasoning behind the message (for reasoning models)
    """
    role: str = ROLE_USER
    content: str = DEFAULT_USER_MESSAGE
    name: Optional[str] = None
    reasoning: Optional[str] = None

class ChatRequest(BaseModel):
    """
    Represents a request to the chat completions API.
    
    Attributes:
        model: The model to use for generating completions
        messages: List of messages in the conversation
        max_tokens: Maximum number of tokens to generate
        temperature: Sampling temperature (higher = more random)
        top_p: Nucleus sampling parameter
        n: Number of completions to generate
        stream: Whether to stream the response
        stop: Sequence(s) at which to stop generation
        presence_penalty: Penalty for token presence
        frequency_penalty: Penalty for token frequency
        user: User identifier for tracking
        include_reasoning: Whether to include reasoning in the response
        reasoning_effort: Level of reasoning effort (high, medium, low)
    """
    model: str = DEFAULT_MODEL
    messages: List[Message]
    max_tokens: Optional[int] = DEFAULT_MAX_TOKENS
    temperature: Optional[float] = DEFAULT_TEMPERATURE
    top_p: Optional[float] = DEFAULT_TOP_P
    n: Optional[int] = DEFAULT_N
    stream: Optional[bool] = DEFAULT_STREAM
    stop: Optional[Union[str, List[str]]] = None
    presence_penalty: Optional[float] = DEFAULT_PRESENCE_PENALTY
    frequency_penalty: Optional[float] = DEFAULT_FREQUENCY_PENALTY
    user: Optional[str] = None
    include_reasoning: Optional[bool] = None
    reasoning_effort: Optional[str] = None

class Usage(BaseModel):
    """
    Represents usage information for a completion request.
    
    Attributes:
        prompt_tokens: Number of tokens in the prompt
        completion_tokens: Number of tokens in the completion
        total_tokens: Total number of tokens used
        total_cost: Total cost of the request
        model_id: ID of the model used
        provider: Provider of the model
        generation_id: ID of the generation
        generation_time: Time taken for generation
    """
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    total_cost: float
    model_id: Optional[str] = None
    provider: Optional[str] = None
    generation_id: Optional[str] = None
    generation_time: Optional[float] = None

class Choice(BaseModel):
    """
    Represents a completion choice.
    
    Attributes:
        index: Index of the choice
        message: The message containing the completion
        finish_reason: Reason why generation finished
    """
    index: int
    message: Message
    finish_reason: str

class ChatResponse(BaseModel):
    """
    Represents a response from the chat completions API.
    
    Attributes:
        id: Unique identifier for the completion
        object: Type of object (always "chat.completion")
        created: Timestamp when the completion was created
        model: Model used for the completion
        choices: List of completion choices
        usage: Usage information
    """
    id: str
    object: str = CHAT_COMPLETION_OBJECT
    created: int
    model: str
    choices: List[Choice]
    usage: Usage

# Models for streaming responses
class StreamingDelta(BaseModel):
    """
    Represents a delta in a streaming response.
    
    Attributes:
        content: Content of the delta
        role: Role of the message
        function_call: Function call information
        tool_calls: Tool call information
        reasoning: Reasoning information
    """
    content: Optional[str] = None
    role: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    reasoning: Optional[str] = None

class StreamingChoice(BaseModel):
    """
    Represents a choice in a streaming response.
    
    Attributes:
        index: Index of the choice
        delta: Delta information
        finish_reason: Reason why generation finished
    """
    index: int
    delta: StreamingDelta
    finish_reason: Optional[str] = None

class StreamingChatResponse(BaseModel):
    """
    Represents a streaming response from the chat completions API.
    
    Attributes:
        id: Unique identifier for the completion
        object: Type of object (always "chat.completion.chunk")
        created: Timestamp when the chunk was created
        model: Model used for the completion
        choices: List of streaming choices
        usage: Usage information (only in the final chunk)
    """
    id: str
    object: str = CHAT_COMPLETION_CHUNK_OBJECT
    created: int
    model: str
    choices: List[StreamingChoice]
    usage: Optional[Usage] = None

# Models for model information
class ModelPricing(BaseModel):
    """
    Represents pricing information for a model.
    
    Attributes:
        input_price_per_million_tokens: Price per million tokens for input
        output_price_per_million_tokens: Price per million tokens for output
    """
    input_price_per_million_tokens: float
    output_price_per_million_tokens: float

class ModelInfo(BaseModel):
    """
    Represents information about a model.
    
    Attributes:
        id: Unique identifier for the model
        name: Name of the model
        description: Description of the model
        pricing: Pricing information
        context_length: Maximum context length
        available: Whether the model is available
    """
    id: str
    name: str
    description: str
    pricing: ModelPricing
    context_length: int
    available: bool = True

class ModelsResponse(BaseModel):
    """
    Represents a response from the models API.
    
    Attributes:
        object: Type of object (always "list")
        data: List of model information
    """
    object: str = MODELS_LIST_OBJECT
    data: List[ModelInfo] 