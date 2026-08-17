import os
from groq import Groq
from dotenv import load_dotenv
from brain.base import BaseBrain
from brain.prompts import PromptBuilder
from brain.intent_parser import IntentParser
from engine.types import ExecutionPlan

load_dotenv()

class GroqBrain(BaseBrain):
    def __init__(self, tools_metadata: list):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in .env")

        self.client = Groq(api_key=self.api_key)
        self.model = "openai/gpt-oss-120b"
        self.prompt_builder = PromptBuilder(tools_metadata)
        self.parser = IntentParser()

    @property
    def provider_name(self) -> str:
        return "groq"

    def think(self, user_query: str) -> ExecutionPlan:
        system_prompt = self.prompt_builder.build_system_prompt()
        user_prompt = self.prompt_builder.build_user_prompt(user_query)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,
            max_tokens=300
        )

        raw_text = response.choices[0].message.content.strip()
        return self.parser.parse(raw_text, user_query)

    def retry(self, user_query: str, previous_error: str, previous_response: str) -> ExecutionPlan:
        retry_prompt = self.prompt_builder.build_retry_prompt(
            user_query, previous_error, previous_response
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": retry_prompt}
            ],
            temperature=0.0,
            max_tokens=300
        )

        raw_text = response.choices[0].message.content.strip()
        return self.parser.parse(raw_text, user_query)