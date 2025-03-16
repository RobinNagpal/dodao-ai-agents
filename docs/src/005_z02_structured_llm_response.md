There can be a component that extends the Agent Tool. It will have following additional features:
- Input box to say the entity type of the input message
- Checkbox to say if the input message is a json string and needs to be converted to json
- Input box to say the entity type of the output message
- Checkbox to say if the output message needs to be wrapped with input message 
- Input box to take the prompt template


The template will be used to create the input request. Then the input request will be sent to the agent and the output will be processed to create structured output.

What will the component do
- It will take the input type, will get the json schema for that type and will validate if the input message 
matches the schema
- It will take the output type, will get the json schema for that type and use it to create structured output
- The full output of the new component will be 
  ```json
  {
    "agentInput": {
      // This helps in passing all the information to the next step 
    },
    "agentOutput": {
      // This will be the structured output
    }
  }
  ```



Define All structures in Graphql Schema Definition
