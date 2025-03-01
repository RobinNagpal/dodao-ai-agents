# V0 - Proof of Concept - CrowdFunding

Here the focus was to learn about agents, their effectiveness, and getting some useful output from them.

We are targeted CrowdFunding as not much information is available about them and can be useful for investors.

## Main Features

1. Spider Charts - Done
2. Summary of Analysis - Done
3. Detailed Analysis of Each Evaluation Category - Done
4. Detailed analysis of each item explaining



## Learnings:

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
