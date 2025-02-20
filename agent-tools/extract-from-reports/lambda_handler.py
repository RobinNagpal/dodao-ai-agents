# Purpose:
#     This lambda will be called to extract data related to few topics from the reports.
#     Parameters like - rent & lease, debt, stock distribution

# There will be a function which will get the latest 10Q report from the SEC and all the attachments from the report.
# For each attachment(ignore balance_sheet, ic, cf), the function will call chatgpt 4o-mini to see if know if the attachments has data specific to
# the topic. At a time max 2 topics can match. The output will a json
# {
#    "topic_rent": {matched: true, match_confidence: 0.8},
#    "topic_debt_matched": {matched: true, match_confidence: 0.8},
#  }

# We can keep a status file at the top to see if the process is completed or not.

# We can probably collect all this information and for each topic pick the top 10(or less) and store it in a file in s3 bucket.

# we create a file related to each topic in s3 bucket and store the attachments in the file.
#  So the path will be <ProjectTicker>/Latest10QReport/<TopicName>.txt
#  So the path will be FVR/Latest10QReport/rent.txt
#  So the path will be FVR/Latest10QReport/debt.txt

# We need to see how lambda executes in the background, as we want to say that it has started processing, and the
# lambda should die only after processing and collecting information for each topic.

# There can be another tool which can just read the file and return it to the agent for analysis. And the tool can
# throw an error if the file is not present.
