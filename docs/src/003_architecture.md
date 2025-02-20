# Architecture

## Layers
#### Bottom Layer: **Data Layer**
- SEC EDGAR Filings
- Industry Data
- X and Instagram Data for sentiment analysis
- News, Industry Reports, etc. 

#### Data Extraction Layer - AI Tools
- Extract qualitative information from SEC EDGAR filings (Similar to yahoo finance)
- Extract qualitative information from SEC EDGAR filings (Not present anywhere else currently)
- Extract detailed quantitative information specific to industry (Not present else currently)
- Extract detailed qualitative information specific to industry (Not present else currently)
- Extract sentiment analysis from X and Instagram data
- Extract sentiment analysis from SEC EDGAR filings

#### RAW Reports  - Using Large Language Models
- Raw basic financial reports(balance sheet, income statement, cash flow statement)
- Quantitative information specific to each parameter specific to industry
- Qualitative information specific to each parameter specific to industry
- Sentiment analysis reports
- Industry performance and projections - Past, Present, Future

#### Consolidated Reports - Using Purpose Built AI Agents
- Spider chat reports consolidating all aspects of the company
- Comparison reports with industry and competitors
- Detailed easy to understand reports for each parameter specific to industry
- Reports specific to investment style (Value, Growth, Dividend, etc.)
- Reports specific to investment horizon (Short, Medium, Long)
- Custom reports based on needs of the business

```mermaid

flowchart BT
    %% Consolidated Reports (Top Layer)
    subgraph CR[Consolidated Reports: Purpose Built AI Agents]
        CR1[Spider Chat Reports: Consolidating All Aspects]
        CR2[Comparison Reports with Industry & Competitors]
        CR3[Detailed, Easy-to-Understand Reports per Industry Parameter]
        CR4[Reports Specific to Investment Style: Value, Growth, Dividend, etc.]
        CR5[Reports Specific to Investment Horizon: Short, Medium, Long]
        CR6[Custom Reports Based on Business Needs]
    end

    %% RAW Reports (Next Layer)
    subgraph RR[RAW Reports: Large Language Models]
        RR1[Basic Financial Reports: Balance Sheet, Income Statement, Cash Flow Statement]
        RR2[Quantitative Info Specific to Each Industry Parameter]
        RR3[Qualitative Info Specific to Each Industry Parameter]
        RR4[Sentiment Analysis Reports]
        RR5[Industry Performance & Projections: Past, Present, Future]
    end

    %% Data Extraction Layer (Next Layer)
    subgraph DE[Data Extraction Layer: AI Tools]
        DE1[Extract Qualitative Info from SEC EDGAR Filings: Similar to Yahoo Finance]
        DE2[Extract Unique Qualitative Info from SEC EDGAR Filings]
        DE3[Extract Detailed Quantitative Industry Data]
        DE4[Extract Detailed Qualitative Industry Data]
        DE5[Extract Sentiment Analysis from X & Instagram Data]
        DE6[Extract Sentiment Analysis from SEC EDGAR Filings]
    end

    %% Data Layer (Bottom Layer)
    subgraph DL[Data Layer]
        DL1[SEC EDGAR Filings]
        DL2[Industry Data]
        DL3[X & Instagram Data for Sentiment Analysis]
        DL4[News, Industry Reports, etc.]
    end

    %% Arrows between layers
    DL --> DE
    DE --> RR
    RR --> CR

```
