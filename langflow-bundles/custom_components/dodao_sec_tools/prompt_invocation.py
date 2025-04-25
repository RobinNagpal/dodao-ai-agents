from langflow.custom import Component
from langflow.inputs import DropdownInput
from langflow.io import MessageTextInput, Output, DataInput, MultilineInput
from langflow.schema import Data
from langflow.schema.message import Message
from langflow.helpers.data import data_to_text
import requests
import json

class PromptInvocatorComponent(Component):
    display_name = "Prompt Invocator"
    description = "A custom component for running a prompt using a prompt key."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "custom_components"
    name = "PromptInvocator"

    KOALAGAINS_INVOCATION_ENDPOINT = "https://koalagains.com/api/actions/prompt-invocation/full-req-resp"
    
    inputs = [
        DataInput(
            name="input_json",
            display_name="Input Json",
            info="The data to send to the prompt invocation.",
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
            options=["gpt-4o-mini", "gpt-4o", "o3-mini", "o4-mini"],
            value="gpt-4o",
        ),
        MultilineInput(
            name="body_to_append",
            display_name="Body To Append",
            info="Body to be appended after the prompt.",
        ),
        DropdownInput(
            name="output_type",
            display_name="Output Type",
            options=["Data", "Message"],
            value="Data",
            info="Select the type of output returned by the component.",
        ),
    ]

    outputs = [
        Output(
            display_name="Data",
            name="invocation_output",
            method="output_data",
        ),
        Output(
            display_name="Message",
            name="text",
            method="output_message",
        ),
    ]

    def call_prompt_invocator(self) -> Data:
        """Calls the API and returns the raw Data output."""
        input_json = self.input_json.data if self.input_json and self.input_json.data else {}
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
                resp_data = {"raw_text": response.text}
            return Data(data=resp_data)
        except Exception as exc:
            return Data(data={"error": str(exc)})

    def output_data(self) -> Data:
        if self.output_type == "Data":
            return self.call_prompt_invocator()
        return Data(data={})

    def output_message(self) -> Message:
        if self.output_type == "Message":
            data = self.call_prompt_invocator()
            try:
                text = data_to_text("{message}", data)
                return Message(text=text)
            except Exception as exc:
                return Message(text=str(exc))
        return Message(text="")
