import re
import time
import json
import logging


from collections import defaultdict

from app.core.config import settings


class BaseLLM:
    def __init__(self, max_tokens=100, buffer_size=40, temperature: float=0.1,**kwargs):
        self.max_tokens = max_tokens
        self.buffer_size = buffer_size
        self.temperature = temperature
        self.kwargs = kwargs


    async def generate(self, messages, stream=True):
        raise NotImplementedError


    async def generate_stream(self, messages:list):
        raise NotImplementedError
