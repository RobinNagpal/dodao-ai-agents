# Creating Your First Report for a Test Ticker

Once you’ve set up your flow and configured the SEC tools, you’re ready to generate your first report using a test ticker. This section will walk you through how to build the flow and send the final report for saving on the KoalaGains platform.

## Step 1: Build the Flow

Start by assembling your flow in LangFlow as shown below:

![Copy Criteria](./images/criteira_and_report/flow.png)

The flow generally follows these steps:

1. **Retrieve SEC Data**

   - The first component pulls in the relevant SEC data based on the **ticker**, **criterion**, and **report type**.

2. **Generate the Report**

   - The second component sends this data, along with a prompt describing the report type, to **OpenAI**, which generates the actual report content.

3. **Prepare the Final Output**
   - The generated report is passed to the next component, which wraps the content into a structured format.
   - Make sure to **fill in all fields highlighted in yellow** in the LangFlow interface. These fields are essential for saving the report correctly.

## Step 2: Save the Report

Once the final report is structured, it is sent as the **body of a POST request** to the KoalaGains platform:

**Endpoint:**  
👉 `https://koalagains.com/api/langflow/save-report`

The system will save the report, making it available for viewing directly on the platform.

This completes the process of generating and saving your first report using a test ticker. You can now repeat these steps for any public company ticker of your choice.
