import traceback
from urllib.parse import urlparse

from dotenv import load_dotenv
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from koala_gains.agent_state import AgentState, Config, ReportType, ProcessedProjectInfo
from koala_gains.structures.report_structures import (
    StartupAndTeamInfoStructure,
    StructuredReportResponse,
    TeamMemberStructure,
)
from koala_gains.utils.linkedin_utls import get_cached_linkedin_profile
from koala_gains.utils.llm_utils import (
    get_llm,
    structured_report_response,
    NORMAL_4_0_CONFIG,
)
from koala_gains.utils.prompt_utils import create_prompt_for_checklist
from koala_gains.utils.report_utils import (
    update_report_status_failed,
    update_report_status_in_progress,
    update_report_with_structured_output,
)

load_dotenv()

search = GoogleSerperAPIWrapper()


class TeamMemberProfile(BaseModel):
    name: str = Field(description="The name of the team member")
    profile_url: str = Field(
        description="URL that opens in a new tab of the team member's LinkedIn profile"
    )
    profile_summary: str = Field(
        description="Summary of the team member's LinkedIn profile"
    )
    experiences: list[str] = Field(
        description="List of experiences with the title, company, and duration"
    )
    educations: list[str] = Field(
        description="List of educations with the degree, school, and duration"
    )


class AnalyzedTeamProfile(TypedDict):
    id: str
    name: str
    title: str
    info: str
    academicCredentials: str
    qualityOfAcademicCredentials: str
    workExperience: str
    depthOfWorkExperience: str
    relevantWorkExperience: str


def find_startup_info(config: Config, page_content: str) -> StartupAndTeamInfoStructure:
    prompt = (
        """From the scraped content, extract the following project info as JSON:
            
            - startup_name: str (The name of the project or startup being discussed) 
            - startup_details: str (A single sentence explaining what the startup does)
            - industry: str (A brief overview of the industry, including how it has grown in the last 3-5 years, its expected growth in the next 3-5 years, challenges, and unique benefits for startups in this space)
            - team_members: list of objects {id: str (Unique ID for each team member, formatted as firstname_lastname), name: str (The name of the team member), title: str (The position of the team member in the startup), info: str (Details or additional information about the team member as mentioned on the startup page)}
            
            Return the extracted information as a JSON object.
            
            {
              "$schema": "http://json-schema.org/draft-07/schema#",
              "title": "StartupAndTeamInfoStructure",
              "description": "Information about the startup, industry, and team",
              "type": "object",
              "properties": {
                "startup_name": {
                  "type": "string",
                  "description": "The name of the project or startup being discussed"
                },
                "startup_details": {
                  "type": "string",
                  "description": "A single sentence explaining what the startup does"
                },
                "industry": {
                  "type": "string",
                  "description": "A brief overview of the industry, including how it has grown in the last 3-5 years, its expected growth in the next 3-5 years, challenges, and unique benefits for startups in this space"
                },
                "team_members": {
                  "type": "array",
                  "description": "A list of team members with their details",
                  "items": {
                    "type": "object",
                    "title": "TeamMemberStructure",
                    "description": "Information about the team members",
                    "properties": {
                      "id": {
                        "type": "string",
                        "description": "Unique ID for each team member, formatted as firstname_lastname"
                      },
                      "name": {
                        "type": "string",
                        "description": "The name of the team member"
                      },
                      "title": {
                        "type": "string",
                        "description": "The position of the team member in the startup"
                      },
                      "info": {
                        "type": "string",
                        "description": "Details or additional information about the team member as mentioned on the startup page"
                      }
                    },
                    "required": ["id", "name", "title", "info"]
                  }
                }
              },
              "required": ["startup_name", "startup_details", "industry", "team_members"]
            }
    
            """
        + f"Startup Info:  \n{page_content}"
    )
    print("Fetching Team Info")
    structured_llm = get_llm(config).with_structured_output(StartupAndTeamInfoStructure)
    response = structured_llm.invoke([HumanMessage(content=prompt)])
    print("Team Info Fetched", response.model_dump_json(indent=4))
    return response


def is_linkedin_profile_url(url: str) -> bool:
    parsed = urlparse(url)
    # Check if the domain is LinkedIn (including subdomains)
    if "linkedin.com" not in parsed.netloc.lower():
        return False

    path = parsed.path
    # Check if path starts with /in/ or /pub/ and has a profile identifier
    if path.startswith(("/in/", "/pub/")):
        parts = path.split("/")
        # Ensure there's a profile name (parts[2] is non-empty)
        if len(parts) >= 3 and parts[2].strip():
            return True
    return False


def search_linkedin_url(query: str) -> str:
    print("Searching for:", query)
    results = search.results(query)  # Ensure 'search' is defined/imported
    for result in results.get("organic", []):
        link = result.get("link", "")
        if is_linkedin_profile_url(link):
            print("Found LinkedIn profile:", link)
            return link
    return ""  # Return empty if no profile found


def generate_team_member_report(startup_name: str, member: TeamMemberStructure) -> str:
    try:
        query = f"Find the LinkedIn profile url of {member.name} working as {member.title} at {startup_name}"

        linked_in_url = search_linkedin_url(query)
        if linked_in_url == "":
            print(f"Could not find LinkedIn url for {member.name} from search")
            return f"## {member.name} - ${member.title}:\nLinkedin Info:  Could not find LinkedIn profile\n\nInfo on startup Page: {member.info}"

        linkedin_profile = get_cached_linkedin_profile(linked_in_url)
        print(f"Fetched LinkedIn profile for {member.name} from {linked_in_url}")

        if linkedin_profile is None:
            print(
                f"Could not find LinkedIn profile for {member.name} from {linked_in_url}"
            )
            return f"## {member.name} - ${member.title}:\nLinkedin Info:  Could not find LinkedIn profile\n\nInfo on startup Page: {member.info}"

        prompt = f"""
        Return the profile information of the team member as a markdown table which includes the following fields:
        - Name: str (The name of the team member)
        - Profile URL - URL that opens in a new tab of the team member's LinkedIn profile
        - Profile: Summary of the team member's LinkedIn profile
        - Experiences: List of experiences with the title, company, and duration
        - Educations: List of educations with the degree, school, and duration 
        
        Summarize the experiences and educations in a concise manner.
        
        Here is the information of the team member:
        Profile URL: {linked_in_url}
        
        Name: {member.name}
        Title: {member.title}
        Info: {member.info}
        
        {linkedin_profile}
        """

        structured_llm = get_llm(NORMAL_4_0_CONFIG).with_structured_output(
            TeamMemberProfile
        )
        response: TeamMemberProfile = structured_llm.invoke(
            [HumanMessage(content=prompt)]
        )

        member_profile_table_str = (
            f"<table>"
            f"    <tr>"
            f"        <td><b>Name:</b></td>"
            f"        <td>{response.name}</td>"
            f"    </tr>"
            f"    <tr>"
            f"        <td><b>Profile URL:</b></td>"
            f"""       <td><a href="{response.profile_url}" target="_blank">{response.profile_url}</a></td>"""
            f"    </tr>"
            f"    <tr>"
            f"        <td><b>Profile:</b></td>"
            f"        <td>{response.profile_summary}</td>"
            f"    </tr>"
            f"    <tr>"
            f"        <td><b>Experiences:</b></td>"
            f"        <td>{'<br>'.join(response.experiences)}</td>"
            f"    </tr>"
            f"    <tr>"
            f"        <td><b>Educations:</b></td>"
            f"        <td>{'<br>'.join(response.educations)}</td>"
            f"    </tr>"
            f"</table>"
        )

        image_tag = ""
        if linkedin_profile.get("profile_pic_url"):
            image_tag = f"""![{member.name}]({linkedin_profile.get('profile_pic_url')} "200x200")"""

        return (
            f"## {member.name} - {member.title}:\n"
            f"{image_tag}\n"
            "### Linkedin Info:\n"
            f"{member_profile_table_str}\n\n"
            f"### Info on startup Page:"
            f"{member.info}"
        )
    except Exception as e:
        print(traceback.format_exc())
        return f"## {member.name} - ${member.title}:\nLinkedin Info:  Error occurred while finding LinkedIn profile\n\nInfo on startup Page: {member.info}"


def generate_team_performance_report(
    state: AgentState, profile_information: str
) -> StructuredReportResponse:
    processes_project_info: ProcessedProjectInfo = state.get("processed_project_info")
    crowdfunding_page_content = processes_project_info.get(
        "content_of_crowdfunding_url"
    )
    sector_info = (
        state.get("processed_project_info")
        .get("industry_details")
        .get("sector_details")
        .get("basic_info")
    )
    sub_sector_info = (
        state.get("processed_project_info")
        .get("industry_details")
        .get("sub_sector_details")
        .get("basic_info")
    )

    prompt = f"""
    You are an expert startup investor. Analyze that the team woking in the startup is exceptional or just good enough.:
    
    Make sure to be conservative based on the profile information of the team members. Make sure to quote the information from the profiles of the team members.
    
    Then rate the founder or founders and the core team on the following parameters and also explain:
    1. General Profile Information: This includes the credentials, quality of the previous companies the member has worked at.
    2. Past Experience: This includes the past experience of the team member and how it is relevant to the startup.
    3. Previous Startup Experience: Has the member worked as a core member in a startup before.
    4. Length of involvement: How long has the member been involved in the startup. Is it from the beginning or has the member joined recently.
    5. Any Exceptional Achievements: Any exceptional achievements of the team member. 
   
    {create_prompt_for_checklist('Founder and Team')}

    Make sure to be conservative. Make sure to quote informaiton from linkedin profile
    
    LinkedIn Profiles
    {profile_information}
    
    Here is the information you have about the startup:
    
    {crowdfunding_page_content}
    
    Sector Info
    {sector_info}
    
    {sub_sector_info}
    """
    return structured_report_response(
        state.get("config"), "detailed_founder_and_team_report", prompt
    )


def create_founder_and_team_report(state: AgentState) -> None:
    """
    Orchestrates the entire team info analysis process.
    """
    project_id = state.get("project_info").get("project_id")
    print("Generating team info")
    try:
        processes_project_info: ProcessedProjectInfo = state.get(
            "processed_project_info"
        )
        content_of_crowdfunding_url = processes_project_info.get(
            "content_of_crowdfunding_url"
        )
        update_report_status_in_progress(project_id, ReportType.FOUNDER_AND_TEAM)
        startup_info: StartupAndTeamInfoStructure = find_startup_info(
            state.get("config"), content_of_crowdfunding_url
        )
        team_members_tables: list[str] = []
        for member in startup_info.team_members:
            member_info_as_table = generate_team_member_report(
                startup_info.startup_name, member
            )
            team_members_tables.append(member_info_as_table)

        team_info_report = "\n\n".join(team_members_tables)
        founder_and_team_report = generate_team_performance_report(
            state, team_info_report
        )
        update_report_with_structured_output(
            project_id,
            ReportType.FOUNDER_AND_TEAM,
            founder_and_team_report,
            team_info_report,
        )
    except Exception as e:
        # Capture full stack trace
        print(traceback.format_exc())
        error_message = str(e)
        print(f"An error occurred:\n{error_message}")
        update_report_status_failed(
            project_id, ReportType.FOUNDER_AND_TEAM, error_message=error_message
        )
