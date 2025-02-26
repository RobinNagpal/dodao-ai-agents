from langflow.custom import Component
from langflow.io import Output, MultiselectInput
from langflow.schema.message import Message

class SwitchComponent(Component):
    display_name = "Switch"
    description = "Routes input items to separate outputs dynamically."
    name = "SwitchComponent"
    icon = "custom_components"

    # Define an input that holds a list of items (e.g., strings)
    inputs = [
        MultiselectInput(
            name="items",
            display_name="Items",
            info="List of items to process.",
            value=["Item 1", "Item 2"],  # default example values
            tool_mode=True,
        ),
        # Other inputs as needed...
    ]

    # Initially, you can leave outputs empty or define a placeholder
    outputs = []

    def update_outputs(self, frontend_node: dict, field_name: str, field_value: any) -> dict:
        """
        Override update_outputs to create a dynamic output for each item in the list.
        """
        if field_name == "items":
            # Clear current outputs
            dynamic_outputs = []
            for idx, item in enumerate(field_value, start=1):
                # Create a unique output for each item.
                # The method 'process_item' should be defined to handle each output.
                new_output = Output(
                    name=f"item_{idx}",
                    display_name=f"Output for {item}",
                    method="process_item",
                )
                dynamic_outputs.append(new_output.model_dump())
            # Update the frontend node's outputs with the dynamic outputs
            frontend_node["outputs"] = dynamic_outputs
        return frontend_node

    def process_item(self) -> Message:
        """
        Process one item. In a real scenario, you might use context (like the output name)
        or additional parameters to know which item to process.
        """
        # For demonstration, simply return a message
        return Message(text="Processed dynamic output")
