## Pull/Push agent-status.json to s3 using tool

- Explain what we are trying to do here
- Explain how this tool will be used in langflow
- Explain how the full flow will work
- Explain the list of things you are changing or adding in the code

## **Pull/Push `agent-status.json` to S3 Using Langflow Components**

### **🔹 Objective**

- We aim to **update `agent_status.json`** whenever a report status changes (`in_progress`, `failed`, or `completed`).
- This involves **fetching `agent_status.json` from its public link**, modifying the status, and **uploading the updated file to S3** using an AWS Lambda function.

---

### **🔹 How This Works in Langflow**

- Three separate **custom components** handle different report status updates:
  1. **`status_file_updater.py`** → Updates `agent_status.json` for `in_progress` and `failed` statuses.
  2. **`status_file_updater_for_completed_report.py`** → Updates `agent_status.json` for `completed` status.
  3. **`s3_uploader.py`** → Uploads the modified `agent_status.json` back to S3.

#### **📌 Component Workflow**

1. **Fetching**: The tool fetches `agent_status.json` via its **public S3 link**.
2. **Updating**: Modifies the status for the given `report_type`.
3. **Uploading**: The updated file is passed to `s3_uploader.py` for storage in S3.

---

### **🔹 How the Full Flow Works**

1. **Processing Starts** (`in_progress`)

   - `status_file_updater.py` fetches `agent_status.json`, updates the status, and passes it to `s3_uploader.py` for upload.

2. **Processing Fails** (`failed`)

   - The same component is triggered with `failed` status.
   - Updates `agent_status.json` and reuploads.

3. **Processing Completes** (`completed`)
   - `status_file_updater_for_completed_report.py` is triggered.
   - Adds structured output (`summary`, `confidence`, `checklist`, `markdown path`).
   - **Returns four outputs**:
     - **Markdown content** (report text).
     - **Markdown path** (S3 location of the report).
     - **Updated `agent_status.json`** (with completion details).
     - **Agent status file path** (S3 location of `agent-status.json`).
   - Passes the updated `agent_status.json` to `s3_uploader.py`.

---

### **🔹 List of Changes & Additions**

1. **Separated components for different statuses**:

   - `status_file_updater.py` for `in_progress` and `failed`.
   - `status_file_updater_for_completed_report.py` for `completed` with structured output.

2. **`status_file_updater_for_completed_report.py` is now connected to two uploaders**:

   - **Sends Markdown content and path to `s3_uploader.py`.**
   - **Sends `agent_status.json` updates to another `s3_uploader.py` instance.**

3. **Delegated file upload** to `s3_uploader.py` instead of handling S3 writes inside status update components.
