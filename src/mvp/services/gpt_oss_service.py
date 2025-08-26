#!/usr/bin/env python3
"""
OpenAI GPT Service Module

Provides GPT-5-nano model inference using OpenAI API
for enhanced AI analysis in the Student Success Prediction system.
"""

import os
import sys
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import json
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.mvp.logging_config import get_logger

logger = get_logger(__name__)

# Import caching service
try:
    from .gpt_cache_service import GPTCacheService
    CACHING_AVAILABLE = True
except ImportError:
    CACHING_AVAILABLE = False

class GPTOSSService:
    """Service class for managing OpenAI GPT model inference."""
    
    def __init__(self, api_key: str = None, model_name: str = "gpt-5-nano",
                 enable_caching: bool = True, timeout: int = 60):
        """
        Initialize OpenAI GPT service.
        
        Args:
            api_key: OpenAI API key (or set OPENAI_API_KEY env var)
            model_name: OpenAI model name (e.g., 'gpt-5-nano', 'gpt-4o-mini')
            enable_caching: Whether to enable result caching
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.model_name = model_name
        self.enable_caching = enable_caching and CACHING_AVAILABLE
        self.timeout = timeout
        self.is_initialized = False
        self.client = None
        
        # Initialize cache service if enabled
        self.cache_service = None
        if self.enable_caching:
            try:
                self.cache_service = GPTCacheService(
                    max_cache_size=500,  # Reasonable limit for GPT analyses
                    default_ttl_minutes=45  # Default 45-minute TTL
                )
                logger.info("🗄️ GPT caching enabled")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize caching: {str(e)}")
                self.enable_caching = False
        
        # Educational context prompts
        self.system_prompts = {
            'student_analysis': """You are an expert educational data analyst and K-12 intervention specialist. 
You analyze student data to provide actionable insights for educators and administrators. 
Focus on evidence-based recommendations, grade-appropriate interventions, and FERPA-compliant analysis.
Always consider the whole student including academic, behavioral, and social-emotional factors.""",
            
            'intervention_planning': """You are a K-12 intervention coordinator with expertise in educational support strategies.
Your role is to develop comprehensive, research-based intervention plans that are practical and implementable.
Consider resource constraints, timeline feasibility, and measurable outcomes.""",
            
            'cohort_analysis': """You are a district-level data analyst specializing in student cohort patterns and trends.
Identify actionable insights for systemic improvements while maintaining student privacy and focusing on equity."""
        }
        
    def _check_openai_connection(self) -> bool:
        """Check if OpenAI API is accessible and API key is valid."""
        if not OPENAI_AVAILABLE:
            logger.error("❌ OpenAI library not available. Install with: pip install openai")
            return False
            
        if not self.api_key:
            logger.error("❌ No OpenAI API key provided. Set OPENAI_API_KEY environment variable")
            return False
        
        try:
            # Initialize client
            self.client = openai.OpenAI(api_key=self.api_key)
            
            # Test API connection with a simple request
            test_params = {
                "model": self.model_name,
                "messages": [
                    {"role": "user", "content": "Test connection. Respond with 'OK'."}
                ],
                "timeout": 10
            }
            
            # Use appropriate token parameter based on model
            if "gpt-5" in self.model_name.lower():
                test_params["max_completion_tokens"] = 5
            else:
                test_params["max_tokens"] = 5
            
            response = self.client.chat.completions.create(**test_params)
            
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                logger.info(f"✅ OpenAI API connection successful")
                logger.info(f"✅ Model {self.model_name} is accessible")
                logger.info(f"🔍 Test response: '{content}'")
                return True
            else:
                logger.warning(f"⚠️ OpenAI API responded but unexpected format: {response}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to connect to OpenAI API: {str(e)}")
            if "model" in str(e).lower():
                logger.info("💡 Available models: gpt-4o, gpt-4o-mini, gpt-3.5-turbo")
            return False
    
    def initialize_model(self) -> bool:
        """
        Initialize connection to OpenAI API and verify model availability.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        logger.info(f"🤖 Initializing OpenAI GPT service: {self.model_name}")
        
        # Check OpenAI connection
        if not self._check_openai_connection():
            return False
        
        self.is_initialized = True
        logger.info("✅ OpenAI GPT service initialized successfully")
        return True
    
    
    def generate_analysis(self, prompt: str, analysis_type: str = "student_analysis", 
                         max_tokens: int = 1024, bypass_cache: bool = False) -> Dict[str, Any]:
        """
        Generate AI analysis using GPT-OSS model with optional caching.
        
        Args:
            prompt: Input prompt with student/educational data
            analysis_type: Type of analysis (student_analysis, intervention_planning, cohort_analysis)
            max_tokens: Maximum tokens to generate
            bypass_cache: Whether to bypass cache and force fresh analysis
            
        Returns:
            Dict containing generated analysis and metadata
        """
        # Check cache first if enabled and not bypassing
        if self.enable_caching and self.cache_service and not bypass_cache:
            cache_key_data = {
                "prompt_hash": hashlib.sha256(prompt.encode()).hexdigest()[:16],
                "max_tokens": max_tokens,
                "model": self.model_name
            }
            
            cached_result = self.cache_service.get_cached_analysis(
                analysis_type, cache_key_data
            )
            
            if cached_result:
                return cached_result
        if not self.is_initialized:
            if not self.initialize_model():
                return {
                    "success": False,
                    "error": "GPT-OSS model not available",
                    "analysis": "GPT analysis unavailable - using fallback mode",
                    "metadata": {"model": "fallback", "timestamp": datetime.now().isoformat()}
                }
        
        try:
            # Build system and user messages with GPT-5-nano optimization
            system_prompt = self.system_prompts.get(analysis_type, self.system_prompts['student_analysis'])
            
            # For GPT-5-nano, use specific prompt format to trigger reasoning
            if "gpt-5-nano" in self.model_name.lower():
                enhanced_prompt = f"""{prompt}

Think step by step about this student's situation:
1. What are the key risk factors?
2. What interventions would be most effective?
3. What is the priority order for implementing support?

Based on your analysis, provide specific recommendations for the educator."""
                
                messages = [
                    {"role": "system", "content": system_prompt + "\n\nYou must always provide a complete written analysis after your reasoning."},
                    {"role": "user", "content": enhanced_prompt}
                ]
            else:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
            
            # Generate response via OpenAI API
            start_time = datetime.now()
            
            # Configure request parameters based on model capabilities
            request_params = {
                "model": self.model_name,
                "messages": messages,
                "timeout": self.timeout
            }
            
            # GPT-5-nano has parameter restrictions - only supports defaults
            if "gpt-5-nano" in self.model_name.lower():
                # Use only default values for restricted parameters
                pass  # temperature=1.0 (default), top_p=1.0 (default)
            else:
                # Other models support custom parameters
                request_params["temperature"] = 0.8
                request_params["top_p"] = 0.9
            
            # GPT-5 models use max_completion_tokens and need more tokens for reasoning
            if "gpt-5" in self.model_name.lower():
                # GPT-5-nano uses tokens for reasoning, so significantly increase allocation
                if "gpt-5-nano" in self.model_name.lower():
                    # GPT-5-nano needs massive token allocation due to reasoning overhead
                    # Based on community reports: reasoning can use 1000+ tokens before output
                    adjusted_tokens = max(max_tokens + 2000, 3000)  # Ensure at least 3000 tokens total
                else:
                    adjusted_tokens = max_tokens
                request_params["max_completion_tokens"] = adjusted_tokens
            else:
                request_params["max_tokens"] = max_tokens
            
            # Add GPT-5-nano specific parameters if using that model
            if "gpt-5-nano" in self.model_name.lower():
                # Use minimal reasoning to reduce token overhead and get faster output
                request_params["reasoning_effort"] = "minimal"
            
            # Use different API endpoint for GPT-5 reasoning models
            if "gpt-5" in self.model_name.lower():
                # Try Responses API for GPT-5 models
                try:
                    response = self.client.responses.create(
                        model=self.model_name,
                        input=messages[1]["content"],  # User message content
                        reasoning={"effort": request_params.get("reasoning_effort", "minimal")},
                        max_output_tokens=request_params.get("max_completion_tokens", max_tokens)
                    )
                except AttributeError:
                    # Fallback to chat completions if responses API not available
                    logger.warning("⚠️ Responses API not available, falling back to Chat Completions")
                    response = self.client.chat.completions.create(**request_params)
                except Exception as e:
                    logger.warning(f"⚠️ Responses API failed: {str(e)}, falling back to Chat Completions")
                    response = self.client.chat.completions.create(**request_params)
            else:
                # Use standard chat completions for other models
                response = self.client.chat.completions.create(**request_params)
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # Process response with different formats for different APIs
            if hasattr(response, 'output') and response.output:
                # Responses API format - extract text from structured response
                generated_text = ""
                try:
                    # Handle structured response objects
                    if isinstance(response.output, list):
                        for item in response.output:
                            if hasattr(item, 'content') and item.content:
                                for content_item in item.content:
                                    if hasattr(content_item, 'text'):
                                        generated_text += content_item.text + "\n"
                            elif hasattr(item, 'text'):
                                generated_text += item.text + "\n"
                            else:
                                generated_text += str(item) + "\n"
                    else:
                        generated_text = str(response.output)
                    
                    generated_text = generated_text.strip()
                    if generated_text:
                        success = True
                        logger.info(f"✅ GPT-5 Responses API generated {len(generated_text)} characters of content")
                    else:
                        generated_text = "GPT-5 responded but no extractable text content found"
                        success = False
                except Exception as e:
                    logger.warning(f"⚠️ Error extracting content from Responses API: {str(e)}")
                    generated_text = f"Response received but content extraction failed: {str(e)}"
                    success = False
            elif hasattr(response, 'choices') and response.choices and len(response.choices) > 0:
                # Chat Completions API format
                message = response.choices[0].message
                if message and message.content and message.content.strip():
                    generated_text = message.content.strip()
                    success = True
                    logger.info(f"✅ Generated {len(generated_text)} characters of content")
                else:
                    # GPT-5-nano commonly returns empty content after reasoning
                    if "gpt-5-nano" in self.model_name.lower():
                        reasoning_tokens = getattr(response.usage, 'reasoning_tokens', 0) if hasattr(response, 'usage') else 0
                        total_tokens = getattr(response.usage, 'total_tokens', 0) if hasattr(response, 'usage') else 0
                        logger.warning(f"⚠️ GPT-5-nano returned empty content after using {reasoning_tokens} reasoning tokens")
                        generated_text = f"GPT-5-nano processed the request (used {total_tokens} tokens including {reasoning_tokens} reasoning tokens) but returned no visible output. This may be due to API endpoint mismatch - reasoning models work better with Responses API."
                        success = False
                    else:
                        generated_text = f"Model returned empty response. Message: {message}"
                        success = False
            else:
                generated_text = f"Unexpected response format. Response: {response}"
                success = False
            
            # Build result
            result = {
                "success": success,
                "analysis": generated_text,
                "metadata": {
                    "model": self.model_name,
                    "analysis_type": analysis_type,
                    "processing_time_seconds": processing_time,
                    "timestamp": end_time.isoformat(),
                    "tokens_used": getattr(response.usage, 'total_tokens', 0) if hasattr(response, 'usage') else len(generated_text.split()),
                    "prompt_tokens": getattr(response.usage, 'prompt_tokens', 0) if hasattr(response, 'usage') else 0,
                    "completion_tokens": getattr(response.usage, 'completion_tokens', 0) if hasattr(response, 'usage') else 0
                }
            }
            
            # Cache the result if caching is enabled
            if self.enable_caching and self.cache_service:
                try:
                    cache_key_data = {
                        "prompt_hash": hashlib.sha256(prompt.encode()).hexdigest()[:16],
                        "max_tokens": max_tokens,
                        "model": self.model_name
                    }
                    
                    self.cache_service.cache_analysis_result(
                        analysis_type, cache_key_data, result
                    )
                except Exception as e:
                    logger.warning(f"⚠️ Failed to cache analysis result: {str(e)}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ GPT analysis generation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "analysis": "Analysis generation failed - please try again",
                "metadata": {"model": self.model_name, "timestamp": datetime.now().isoformat()}
            }
    
    def analyze_student_comprehensive(self, student_data: Dict[str, Any], 
                                    intervention_history: List[Dict] = None,
                                    peer_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate comprehensive student analysis using all available data.
        
        Args:
            student_data: Complete student profile data
            intervention_history: Previous interventions and outcomes
            peer_context: Grade-level and cohort comparison data
            
        Returns:
            Comprehensive analysis with actionable insights
        """
        # Build comprehensive prompt
        prompt_parts = []
        
        # Student profile section
        student_summary = self._format_student_data(student_data)
        prompt_parts.append(f"STUDENT PROFILE:\n{student_summary}")
        
        # Intervention history
        if intervention_history:
            intervention_summary = self._format_intervention_history(intervention_history)
            prompt_parts.append(f"\nINTERVENTION HISTORY:\n{intervention_summary}")
        
        # Peer context
        if peer_context:
            peer_summary = self._format_peer_context(peer_context)
            prompt_parts.append(f"\nPEER CONTEXT:\n{peer_summary}")
        
        # Analysis request
        prompt_parts.append("""
\nPlease provide a comprehensive analysis including:
1. Current risk assessment and protective factors
2. Priority intervention recommendations with specific strategies
3. Timeline and resource requirements
4. Expected outcomes and success metrics
5. Family engagement recommendations
6. Progress monitoring suggestions

Focus on actionable, evidence-based recommendations appropriate for K-12 educational settings.""")
        
        full_prompt = "\n".join(prompt_parts)
        
        return self.generate_analysis(full_prompt, "student_analysis", max_tokens=1536)
    
    def _format_student_data(self, student_data: Dict[str, Any]) -> str:
        """Format student data for GPT analysis."""
        formatted = []
        
        # Basic demographics (anonymized)
        if student_data.get('grade_level'):
            formatted.append(f"Grade Level: {student_data['grade_level']}")
        
        # Academic performance
        if student_data.get('risk_score'):
            formatted.append(f"Current Risk Score: {student_data['risk_score']:.2f}")
        if student_data.get('risk_category'):
            formatted.append(f"Risk Category: {student_data['risk_category']}")
        
        # Key metrics
        metrics = ['attendance_rate', 'gpa', 'assignment_completion', 'behavior_incidents']
        for metric in metrics:
            if student_data.get(metric) is not None:
                formatted.append(f"{metric.replace('_', ' ').title()}: {student_data[metric]}")
        
        return "\n".join(formatted) if formatted else "Limited student data available"
    
    def _format_intervention_history(self, interventions: List[Dict]) -> str:
        """Format intervention history for analysis."""
        if not interventions:
            return "No previous interventions recorded"
        
        formatted = []
        for intervention in interventions[-5:]:  # Last 5 interventions
            status = intervention.get('status', 'unknown')
            outcome = intervention.get('outcome', 'pending')
            int_type = intervention.get('intervention_type', 'unspecified')
            formatted.append(f"- {int_type} ({status}): {outcome}")
        
        return "\n".join(formatted)
    
    def _format_peer_context(self, peer_data: Dict[str, Any]) -> str:
        """Format peer comparison context."""
        formatted = []
        
        if peer_data.get('grade_average_gpa'):
            formatted.append(f"Grade Level Average GPA: {peer_data['grade_average_gpa']:.2f}")
        if peer_data.get('percentile_rank'):
            formatted.append(f"Performance Percentile: {peer_data['percentile_rank']}%")
        
        return "\n".join(formatted) if formatted else "No peer comparison data available"
    
    def health_check(self) -> Dict[str, Any]:
        """Check service health and OpenAI API connection status."""
        health_info = {
            "service": "OpenAI GPT Service",
            "initialized": self.is_initialized,
            "model": self.model_name,
            "caching_enabled": self.enable_caching,
            "openai_available": OPENAI_AVAILABLE,
            "api_key_configured": bool(self.api_key),
            "timeout": self.timeout
        }
        
        # Add cache statistics if caching is enabled
        if self.enable_caching and self.cache_service:
            try:
                cache_health = self.cache_service.health_check()
                health_info["cache_status"] = cache_health
            except Exception as e:
                health_info["cache_status"] = {"status": "error", "error": str(e)}
        
        # Add model info if available
        if self.is_initialized:
            try:
                model_info = self.get_model_info()
                health_info["model_info"] = model_info
            except Exception as e:
                health_info["model_info"] = {"error": str(e)}
        
        return health_info
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the OpenAI model."""
        if not self.is_initialized:
            return {"status": "not_initialized"}
        
        try:
            # OpenAI doesn't have a direct model info endpoint
            # Return basic information we know
            return {
                "model": self.model_name,
                "status": "available",
                "provider": "OpenAI",
                "api_version": getattr(openai, '__version__', 'unknown') if OPENAI_AVAILABLE else 'unknown'
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}