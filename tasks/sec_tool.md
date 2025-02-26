# Merge three tools into one
Right now we have two tools
1. Fet All financial reports from latest 10Q for a ticker
2. Get specific financial report from latest 10Q for a ticker

And now we want to add another one
3. Get criterion information from latest 10Q for a ticker
   - This will check if it exisits in s3, else will create it and return it. Hassaan fixed some issues on it. Dawood is working on saving it to s3.


We can merge all these three tools into one. 

The tool can have a dropdown where user can select the type of information they want. Based on the selection, 
the tool will call the specific path in the lambda function.

This can be done in two parts.

1) Make sure tool is called correctly and the tool get all the required information. For example in case of criterion information, 
   the tool should know the criterion key. And in case of specific financial report, the tool should know the specific report_type.
2) Calling the lambda and returning the information.


Just do part 1 for now. Part 2 can be done in new PR.
