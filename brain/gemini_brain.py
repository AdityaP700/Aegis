import os
import json
from dotenv import load_dotenv
from brain.base import BaseBrain
from brain.prompts import PromptBuilder
from brain.intent_parser import IntentParser
from engine.types import ExecutionPlan
import google.generativeai as genai

load_dotenv()

class GeminiBrain(BaseBrain):
    """Gemini implementation of the Brain."""


    def __init__(self, tools_metadata: list):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in .env")

        self.min_delay_between_calls = 5.0  # 5 seconds between calls
        self.last_call_time = 0.0
        # Initialize Gemini
        genai.configure(api_key=self.api_key)

        self.model = genai.GenerativeModel(
            "gemini-2.5-pro",
            generation_config={
                "temperature": 0.0,
                "max_output_tokens": 300
            }
        )

        self.prompt_builder = PromptBuilder(tools_metadata)
        self.parser = IntentParser()

    @property
    def provider_name(self) -> str:
        return "gemini"

    def think(self, user_query: str) -> ExecutionPlan:
        """
        Interpret user intent using Gemini.

        Args:
            user_query: Natural language query

        Returns:
            ExecutionPlan object
        """
        # Build prompts
        system_prompt = self.prompt_builder.build_system_prompt()
        user_prompt = self.prompt_builder.build_user_prompt(user_query)

        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        # Call Gemini
        response = self.model.generate_content(full_prompt)
        raw_text = response.text.strip()

        # Parse into ExecutionPlan
        plan = self.parser.parse(raw_text, user_query)

        return plan

    def retry(self, user_query: str, previous_error: str, previous_response: str) -> ExecutionPlan:
        """
        Retry with error feedback.

        Args:
            user_query: Original query
            previous_error: What was wrong
            previous_response: What the LLM returned

        Returns:
            New ExecutionPlan
        """
        retry_prompt = self.prompt_builder.build_retry_prompt(
            user_query, previous_error, previous_response
        )

        response = self.model.generate_content(retry_prompt)
        raw_text = response.text.strip()

        plan = self.parser.parse(raw_text, user_query)
        return plan