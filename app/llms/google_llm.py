import json
import logging

from .base_llm import BaseLLM

from google import genai
from google.genai import types
from app.utils import clean_json_string
from app.core.config import settings



class GoogleLLM(BaseLLM):
    def __init__(self, max_tokens=100, buffer_size=40, temperature: float=0.1,model:str = 'gemini-3-flash-preview',**kwargs):
        self.max_tokens = max_tokens
        self.buffer_size = buffer_size
        self.temperature = temperature
        self.kwargs = kwargs
        self.model = model
        self.llm = genai.Client(
            api_key=settings.GEMINI_API_KEY,
            # vertexai=False is the default, but we're being explicit
            vertexai=False
        )
        self.config = types.GenerateContentConfig(
            max_output_tokens=5000,
            temperature=self.temperature,
        )


    async def generate(self, messages,json_resp=False):
        if not messages:
            raise Exception("No messages provided")

        system_instruction, contents = await self._prepare_messages(messages)
        self.config.system_instruction = system_instruction

        response = await self.llm.aio.models.generate_content(
            model=self.model,
            contents=contents,
            config=self.config
        )

        print(response.text)
        if json_resp:
            return clean_json_string(response.text)

        return response.text


    async def generate_stream(self, messages):
        if not messages:
            raise Exception("No messages provided")

        system_instruction, contents = await self._prepare_messages(messages)
        # Apply system instruction to the config for this specific call
        self.config.system_instruction = system_instruction

        buffer = ""
        logging.info(f"Streaming from Gemini API: {self.model}")

        # Async streaming call using .aio
        async for response in await self.llm.aio.models.generate_content_stream(
            model=self.model,
            contents=contents,
            config=self.config
        ):
            chunk_text = response.text
            if chunk_text:
                buffer += chunk_text

            if len(buffer) >= self.buffer_size:
                yield buffer
                buffer = ""

        if buffer:
            yield buffer
        self.started_streaming = False


    async def _prepare_messages(self, messages):
        """Converts generic role/content messages to Gemini's role/parts format."""
        system_instruction = None
        formatted_messages = []

        for m in messages:
            if m["role"] == "system":
                system_instruction = m["content"]
            else:
                # Gemini roles are strictly 'user' or 'model'
                role = "user" if m["role"] == "user" else "model"
                formatted_messages.append(
                    types.Content(
                        role=role, 
                        parts=[types.Part.from_text(text=str(m["content"]))]
                    )
                )

        return system_instruction, formatted_messages
