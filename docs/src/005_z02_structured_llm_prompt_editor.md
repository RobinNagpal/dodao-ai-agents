This can be a Typescript app which allows for adding a `StructuredLLMCall`.
- Input type and schema
- Output type and schema
- Prompt
- Default Model

Then it gives a slug based url which can be called with the input, and the model type.

We can also save all the invocations, making it easier to debug.

#### Template Editor
We have a lot of prompts and we need to regularly update them. We should have some configurable way to update the prompts

The prompts take a input object and then return a string. Handlebars can be used to populate the string with the object.
There is also good support for handlebars in react online editors and we can use one of them to edit the prompts via a UI.

See these examples & libraries
- https://medium.com/@jacksbridger/building-a-handlebars-email-previewer-df83d346e2e2
- https://github.com/suren-atoyan/monaco-react && https://github.com/react-monaco-editor/react-monaco-editor

More Information
- This editor can be a standalone lambda app or can be a vercel app.
- We can save the prompts in a json file and then load them in the editor or in the DB
- We can also have a versioning system for the prompts
- We can write a simple python script to make it easy to use the prompts in python code.


#### JSON schema editor.
We also use a JSON schema for getting a structured response. We should also be able to create the JSON schema via a UI.

We can use
- https://github.com/Open-Federation/json-schema-editor-visual
- https://github.com/ginkgobioworks/react-json-schema-form-builder
- https://github.com/Optum/jsonschema-editor-react
- https://github.com/lin-mt/json-schema-editor-antd

