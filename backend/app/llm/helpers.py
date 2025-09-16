"""
LLM helper functions for managing different language model providers.

This module provides utilities to create and configure language models
from different providers (OpenAI, Google Gemini) based on configuration settings.
"""

from typing import Optional, Dict, Any
from langchain_core.language_models import BaseLanguageModel
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings


def create_llm(
    model_name: Optional[str] = None,
    temperature: float = 0,
    system_instruction: Optional[str] = None,
    **kwargs
) -> BaseLanguageModel:
    """
    Create a language model instance based on the configured provider.
    
    Args:
        model_name: Specific model name to use (optional, uses defaults if not provided)
        temperature: Temperature setting for the model (default: 0)
        system_instruction: System instruction/prompt for the model
        **kwargs: Additional model-specific parameters
        
    Returns:
        Configured language model instance
        
    Raises:
        ValueError: If the configured provider is not supported
        RuntimeError: If required API keys are missing
    """
    provider = getattr(settings, 'preferred_llm_provider', 'GOOGLE').upper()
    
    if provider == 'OPENAI':
        return _create_openai_llm(
            model_name=model_name,
            temperature=temperature,
            system_instruction=system_instruction,
            **kwargs
        )
    elif provider == 'GOOGLE':
        return _create_google_llm(
            model_name=model_name,
            temperature=temperature,
            system_instruction=system_instruction,
            **kwargs
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}. Supported providers: OPENAI, GOOGLE")


def _create_openai_llm(
    model_name: Optional[str] = None,
    temperature: float = 0,
    system_instruction: Optional[str] = None,
    **kwargs
) -> ChatOpenAI:
    """
    Create an OpenAI language model instance.
    
    Args:
        model_name: OpenAI model name (default: gpt-3.5-turbo)
        temperature: Temperature setting
        system_instruction: System instruction
        **kwargs: Additional OpenAI-specific parameters
        
    Returns:
        Configured OpenAI model instance
        
    Raises:
        RuntimeError: If OpenAI API key is missing
    """
    if not settings.openai_api_key:
        raise RuntimeError("OpenAI API key is required but not configured. Set OPENAI_API_KEY environment variable.")
    
    # Default model if not specified
    if model_name is None:
        model_name = "gpt-3.5-turbo"
    
    # Prepare model kwargs
    model_kwargs = {
        "temperature": temperature,
        **kwargs
    }
    
    # Add system instruction if provided
    if system_instruction:
        model_kwargs["system_instruction"] = system_instruction
    
    return ChatOpenAI(
        model=model_name,
        openai_api_key=settings.openai_api_key,
        temperature=temperature,
        model_kwargs=kwargs
    )


def _create_google_llm(
    model_name: Optional[str] = None,
    temperature: float = 0,
    system_instruction: Optional[str] = None,
    **kwargs
) -> ChatGoogleGenerativeAI:
    """
    Create a Google Gemini language model instance.
    
    Args:
        model_name: Google model name (default: gemini-1.5-flash)
        temperature: Temperature setting
        system_instruction: System instruction
        **kwargs: Additional Google-specific parameters
        
    Returns:
        Configured Google Gemini model instance
        
    Raises:
        RuntimeError: If Google API key is missing
    """
    if not settings.google_api_key:
        raise RuntimeError("Google API key is required but not configured. Set GOOGLE_API_KEY environment variable.")
    
    # Default model if not specified
    if model_name is None:
        model_name = "gemini-1.5-flash"
    
    # Prepare model kwargs
    model_kwargs = {
        "temperature": temperature,
        **kwargs
    }
    
    # Add system instruction if provided
    if system_instruction:
        model_kwargs["system_instruction"] = system_instruction
    
    return ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=settings.google_api_key,
        temperature=temperature,
        model_kwargs=kwargs
    )


def get_available_models() -> Dict[str, list]:
    """
    Get list of available models for each provider.
    
    Returns:
        Dictionary mapping provider names to lists of available models
    """
    return {
        "OPENAI": [
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k",
            "gpt-4",
            "gpt-4-turbo-preview",
            "gpt-4-32k"
        ],
        "GOOGLE": [
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-pro"
        ]
    }


def get_current_provider() -> str:
    """
    Get the currently configured LLM provider.
    
    Returns:
        The configured provider name (OPENAI or GOOGLE)
    """
    return getattr(settings, 'preferred_llm_provider', 'GOOGLE').upper()


def is_provider_configured(provider: str) -> bool:
    """
    Check if a specific provider is properly configured.
    
    Args:
        provider: Provider name to check (OPENAI or GOOGLE)
        
    Returns:
        True if provider is configured, False otherwise
    """
    provider = provider.upper()
    
    if provider == 'OPENAI':
        return bool(settings.openai_api_key)
    elif provider == 'GOOGLE':
        return bool(settings.google_api_key)
    else:
        return False


def get_provider_info() -> Dict[str, Any]:
    """
    Get information about the current provider configuration.
    
    Returns:
        Dictionary with provider information
    """
    current_provider = get_current_provider()
    
    return {
        "current_provider": current_provider,
        "is_configured": is_provider_configured(current_provider),
        "available_models": get_available_models().get(current_provider, []),
        "openai_configured": is_provider_configured("OPENAI"),
        "google_configured": is_provider_configured("GOOGLE")
    }
