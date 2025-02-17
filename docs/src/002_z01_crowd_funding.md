# V0 - Proof of Concept - CrowdFunding

Here the focus is to learn about agents, their effectiveness, and getting some useful output from them.

We are targeting CrowdFunding as not much information is available about them and can be useful for investors.

## Main Features

#### 1. Spider Charts - Done

- Spider Chart with 6 or 8 sections
- For each pie in the spider chart, we will have a rating (0s or 1s for ~5 items).

#### 2. Summary of Analysis - Done

For these categories in Spider Chart, we will have summary of analysis which is the same as the pie chart i.e.
tick or cross on each item

#### Detailed Analysis of Each Evaluation Category - Done

Detailed analysis of each item explaining

- Important Information Available related to the item(evaluation criteria like revenue, growth, price, etc)
- The opinion of the AI Agent on the investment opportunity

#### Improve accuracy of the agent - In Progress

The reports currently produced are not very accurate. We are working on improving the accuracy of the agent.

Learnings:

- The agent is accurate to 50-60%
- If we have more accurate information like in the case of public companies, the agent can be more accurate
- Providing LLMs output to the LLM in the next step degrades the quality of the output a lot. For this we have added
  a project processing step where we will process the project information so that all the steps downstream can use the
  same information.
- Agent can product different outputs for the same input. So we have to make sure at least its consistent. That means
  when asking for a type of information like TAM, SAM, SOM, etc(information not present in the provided/scraped text),
  it should only be done
  once in the full process.
- We need some configurable way of creating the agents. We decided to use Langflow for this.
