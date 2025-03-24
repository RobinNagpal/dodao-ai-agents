# Creating first report For Test Ticker

## Make the Flow

- Build the flow

  ![Copy Criteria](./images/criteira_and_report/flow.png)

- In first step we get the related SEC data for the specific ticker, criterion and report type
- In second step we give the SEC data to OpenAI and also the prompt about the report Type to be generated
- In third step generated report is passed to next component as data which has this report content in data field
- Carefully fill the fileds which are in yellow rectangle in image as they are to be sent for saving
- The final body created by previous component is passed as body on post request to https://kolagains.com/api/langflow/save-report
