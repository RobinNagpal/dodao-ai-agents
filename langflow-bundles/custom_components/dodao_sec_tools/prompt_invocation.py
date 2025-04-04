from langflow.custom import Component
from langflow.inputs import DropdownInput
from langflow.io import MessageTextInput, Output, DataInput, MultilineInput
from langflow.schema import Data

import requests
import json

class PromptInvocatorComponent(Component):
    display_name = "Prompt Invocator"
    description = "A custom component for running prompt using prompt key."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "custom_components"
    name = "PromptInvocator"

    KOALAGAINS_INVOCATION_ENDPOINT = "https://koalagains.com/api/actions/prompt-invocation/full-req-resp"
    
    inputs = [
        DataInput(
            name="input_json",
            display_name="Input Json",
            info="The data to send to the prompt invocation.",
            required=True,
        ),
        MessageTextInput(
            name="prompt_key",
            display_name="Prompt Key",
            info="The key added when creating the prompt.",
            required=True,
        ),
        DropdownInput(
            name="agent_llm",
            display_name="LLM Provider",
            options=["OpenAI"],
            value="OpenAI",
        ),
        DropdownInput(
            name="model",
            display_name="Model",
            options=["gpt-4o-mini", "gpt-4o", "o3-mini"],
            value="gpt-4o-mini",
        ),
        MultilineInput(
            name="body_to_append",
            display_name="Body To Append",
            info="Body to be appended after the prompt.",
        ),
    ]

    outputs = [
        Output(
            display_name="Invocation Output",
            name="invocation_output",
            method="call_prompt_invocator",
        ),
    ]

    def call_prompt_invocator(self) -> Data:
        input_json = self.input_json.data
        prompt_key = self.prompt_key
        agent_llm = self.agent_llm
        model = self.model
        body_to_append = self.body_to_append

        payload = {
            "inputJson": input_json,
            "promptKey": prompt_key,
            "llmProvider": agent_llm,
            "model": model,
            "bodyToAppend": body_to_append,
            "requestFrom": "langflow"
            }
        try:
            
            response = requests.post(self.KOALAGAINS_INVOCATION_ENDPOINT, json=payload)
            try:
                resp_data = response.json()
            except json.JSONDecodeError:
                # If not valid JSON, just return the raw text
                resp_data = {"raw_text": response.text}

            return Data(
               data=resp_data
            )

        except Exception as exc:
            # If there's a network error, timeouts, etc., return an error structure
            return Data(data={"error": str(exc)})