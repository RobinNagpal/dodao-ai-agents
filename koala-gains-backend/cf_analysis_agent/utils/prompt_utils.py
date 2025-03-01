

def create_prompt_for_checklist(report_type: str) -> str:

    return f"""
    Make sure the output is formatted nicely in markdown and doesn't have many nested points. Use longer sentences and
    paragraphs instead of second and third level bullet points. Include timeline comparisons and velocity metrics.
    
    Create a checklist of "Five Key Points" for the {report_type} report which an ideal company should meet to be the best
    in its industry and specific sector, and see how many of these points met by the provided startup. 
    If the company meets that specific point, give a score of 1, otherwise 0. Explain the reasons for the
    score given. Be conservative in your scoring and provide detailed explanations on how the evaluation was made.
    
    Here is how the json structure should look like:

    """ +  """

    {
        "oneLineSummary": "This report evaluates key performance areas with detailed insights.",
          "status": "success",
          "summary": "This report provides an in-depth evaluation of several key performance areas. Each checklist item is assessed using specific criteria, and detailed explanations along with the calculation logic are provided to support the scores.",
          "failureReason": null,
          "confidence": 8.5,
          "performanceChecklist": [
            {
            "checklistItem": "Clear Title Presentation",
              "oneLineExplanation": "The title clearly represents the content.",
              "informationUsed": "Document header and metadata analysis.",
              "detailedExplanation": "The title was compared against expected formats and verified for clarity and relevance. Use numbers whenver possible like the numbers shared by startup or by industry standards.",
              "calculationLogic": "Score is set to 1 if the title is both descriptive and formatted according to guidelines; otherwise, 0. Explain by using the numbers shared by startup or by industry standards",
              "score": 1
            },
            {
            "checklistItem": "Concise Explanation",
              "oneLineExplanation": "Explanation meets brevity and clarity requirements.",
              "informationUsed": "Text analysis of the explanation section.",
              "detailedExplanation": "The explanation was evaluated based on sentence structure and length. The assessment confirmed that the explanation provides necessary details without excessive verbosity. Use numbers whenver possible like the numbers shared by startup or by industry standards",
              "calculationLogic": "A readability check determines if the explanation falls within the optimal word count and clarity metrics. A positive evaluation assigns a score of 1, otherwise 0. Explain by using the numbers shared by startup or by industry standards",
              "score": 0
            }
          ]
    }
    """
