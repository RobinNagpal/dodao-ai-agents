# Background

Currently we have crowdfunding "Create Project" page which we use to create a new project and then we can populate
some basic information for the project using LLMs like

1. Scrapped crowdfunding page for the project
2. Scrapped SEC filings for the project
3. Sector and sub-sector of the project
4. etc

Then we use this information to populate the reports.

We can reuse the same design to create reports for REITs, or mat be any equities

# REITs Reports

We have a a page where user selects the sector and then the sub-sector from GICS. Then based on the sbu-sector we can
have a list of criterion which are important for that sub-sector.

For each criterion, we can have a list of reports we want on that criterion. For e.g. for Debt & Leverage, we can have
