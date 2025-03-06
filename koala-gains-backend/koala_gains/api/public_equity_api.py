from typing import List, Optional

from flask import Blueprint, jsonify

from flask_pydantic import validate
from pydantic import BaseModel

from koala_gains.api.api_helper import handle_exception
from koala_gains.structures.criteria_structures import IndustryGroupCriteriaStructure
from koala_gains.structures.public_equity_structures import (
    IndustryGroupCriteria,
    CriteriaLookupList,
    IndustryGroupCriterion,
    Sector,
    IndustryGroup,
    PerformanceChecklistItem,
    MetricValueItem,
    CriteriaEvaluation,
    ReportValueItem,
    get_ticker_file_key,
    ImportantMetrics,
)
from koala_gains.utils.criteria_utils import (
    generate_ai_criteria,
    get_ai_criteria,
    update_criteria_lookup_list_for_custom_criteria,
    upload_ai_criteria_to_s3,
    update_criteria_lookup_list,
    get_matching_criteria_lookup_item,
    get_criteria_lookup_list,
    upload_custom_criteria_to_s3,
)
from koala_gains.utils.s3_utils import upload_to_s3
from koala_gains.utils.ticker_utils import (
    initialize_new_ticker_report,
    get_ticker_report,
    save_criteria_evaluation,
    save_performance_checklist, trigger_criteria_matching,
)


class CreateCriteriaRequest(BaseModel):
    sectorId: int
    industryGroupId: int


class UpsertCustomCriteriaRequest(BaseModel):
    sectorId: int
    industryGroupId: int
    criteria: list[IndustryGroupCriterion]


class CreateAllReportsRequest(BaseModel):
    ticker: str
    sectorId: Sector
    industryGroupId: IndustryGroup


class CreateSingleCriterionReportsRequest(BaseModel):
    ticker: str
    sectorId: int
    industryGroupId: int
    criterionKey: str


class SaveCriterionReportRequest(BaseModel):
    ticker: str
    criterionKey: str
    reportKey: str
    shouldTriggerNext: bool
    data: str


class SavePerformanceChecklistRequest(BaseModel):
    ticker: str
    criterionKey: str
    performanceChecklist: List[PerformanceChecklistItem]


class SaveCriterionMetricsRequest(BaseModel):
    ticker: str
    criterionKey: str
    metrics: List[MetricValueItem]


class RepopulateCriteriaMatchingRequest(BaseModel):
    ticker: str

public_equity_api = Blueprint("public_equity_api", __name__)


@public_equity_api.route("/upsert-ai-criteria", methods=["POST"])
@validate(body=CreateCriteriaRequest)
def create_ai_criteria(body: CreateCriteriaRequest):
    try:
        print(
            f"Creating AI criteria for: sectorId: {body.sectorId}, industryGroupId: {body.industryGroupId}"
        )
        custom_criteria_list: CriteriaLookupList = get_criteria_lookup_list()

        criteria_lookup_item = get_matching_criteria_lookup_item(
            custom_criteria_list,
            body.sectorId,
            body.industryGroupId,
        )

        ai_criteria_reponse: IndustryGroupCriteriaStructure = generate_ai_criteria(
            criteria_lookup_item
        )
        ai_criteria_url: str = upload_ai_criteria_to_s3(
            criteria_lookup_item,
            IndustryGroupCriteria(
                tickers=ai_criteria_reponse.tickers,
                criteria=ai_criteria_reponse.criteria,
                selectedSector=Sector(
                    id=criteria_lookup_item.sectorId,
                    name=criteria_lookup_item.sectorName,
                ),
                selectedIndustryGroup=IndustryGroup(
                    id=criteria_lookup_item.industryGroupId,
                    name=criteria_lookup_item.industryGroupName,
                ),
            ),
        )
        update_criteria_lookup_list(criteria_lookup_item, ai_criteria_url)

        return (
            jsonify(
                {
                    "success": True,
                    "message": "AI criteria file created successfully.",
                    "filePath": ai_criteria_url,
                }
            ),
            200,
        )

    except Exception as e:
        return handle_exception(e)


@public_equity_api.route("/upsert-custom-criteria", methods=["POST"])
@validate(body=UpsertCustomCriteriaRequest)
def create_custom_criteria(body: UpsertCustomCriteriaRequest):
    try:
        # Validate required fields
        sector_id = body.sectorId
        industry_group_id = body.industryGroupId
        criteria: list[IndustryGroupCriterion] = body.criteria
        print(
            f"Creating Custom criteria for Sector ID: {sector_id}, Industry Group ID: {industry_group_id}"
        )
        if not sector_id or not industry_group_id or not criteria:
            return (
                jsonify({"success": False, "message": "Missing required fields"}),
                400,
            )

        # Get the existing criteria lookup list
        custom_criteria_list: CriteriaLookupList = get_criteria_lookup_list()
        # Find matching criteria
        matching_criteria = get_matching_criteria_lookup_item(
            custom_criteria_list, sector_id, industry_group_id
        )

        # Generate final criteria data using provided criteria
        final_data = IndustryGroupCriteria(
            tickers=[],
            selectedSector=Sector(
                id=matching_criteria.sectorId, name=matching_criteria.sectorName
            ),
            selectedIndustryGroup=IndustryGroup(
                id=matching_criteria.industryGroupId,
                name=matching_criteria.industryGroupName,
            ),
            criteria=criteria,  # Use the provided criteria
        )
        # Upload criteria to S3
        custom_criteria_url = upload_custom_criteria_to_s3(
            matching_criteria, final_data
        )

        # Update criteria lookup list with the new custom criteria
        update_criteria_lookup_list_for_custom_criteria(
            matching_criteria, custom_criteria_url
        )

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Custom criteria file upserted successfully.",
                    "filePath": custom_criteria_url,
                }
            ),
            200,
        )

    except Exception as e:
        return handle_exception(e)


@public_equity_api.route("/re-populate-matching-attachments", methods=["POST"])
@validate(body=RepopulateCriteriaMatchingRequest)
def repopulate_criteria_matching(body: RepopulateCriteriaMatchingRequest):
    trigger_criteria_matching(
        ticker=body.ticker,
        force=True
    )

    try:
        return (
            jsonify({"success": True, "message": "Ticker processed successfully."}),
            200,
        )
    except Exception as e:
        return handle_exception(e)


@public_equity_api.route("/create-all-reports", methods=["POST"])
def create_all_reports():
    # Step 1 - Create a ticker report file if it does not exist
    # Step 2 - Populate matching criteria for the ticker if it does not exist
    # Step 3 - Generate report for the ticker using the criteria
    # For the first criterion, trigger the report, and pass shouldTriggerNext as True
    return jsonify({"success": True, "message": "Ticker processed successfully."}), 200


@public_equity_api.route("/create-single-report", methods=["POST"])
@validate(body=CreateSingleCriterionReportsRequest)
def process_single_ticker(body: CreateSingleCriterionReportsRequest):
    initialize_new_ticker_report(body.ticker, body.sectorId, body.industryGroupId)

    trigger_criteria_matching(
        ticker=body.ticker,
        force=False
    )

    return jsonify({"success": True, "message": "Ticker processed successfully."}), 200


@public_equity_api.route("/criterion-report", methods=["PUT"])
@validate(body=SaveCriterionReportRequest)
def save_and_trigger_next(body: SaveCriterionReportRequest):
    try:
        ticker_report = get_ticker_report(body.ticker)
        # Ensure evaluations list is always a list, even if it was originally None.
        evaluations = ticker_report.evaluationsOfLatest10Q or []

        # Generate the report URL first.
        report_url = save_criteria_evaluation(
            body.ticker, body.criterionKey, body.reportKey, body.data
        )

        # Try to find an existing evaluation matching the criterion key.
        evaluation = next(
            (e for e in evaluations if e.criterionKey == body.criterionKey), None
        )

        # Create a new ReportValueItem.
        new_report = ReportValueItem(
            reportKey=body.reportKey, outputFileUrl=report_url, status="Completed"
        )

        if evaluation is None:
            # If no evaluation exists for the criterion, create and append a new one.
            new_evaluation = CriteriaEvaluation(
                criterionKey=body.criterionKey,
                importantMetrics=None,
                reports=[new_report],
                performanceChecklist=None,
            )
            evaluations.append(new_evaluation)
        else:
            # Ensure the reports list exists.
            evaluation.reports = evaluation.reports or []
            # Try to find an existing report.
            report_item = next(
                (r for r in evaluation.reports if r.reportKey == body.reportKey), None
            )
            if report_item:
                # Update the report if found.
                report_item.outputFileUrl = report_url
                report_item.status = "Completed"
            else:
                # Otherwise, add the new report and update shouldTriggerNext if available.
                evaluation.reports.append(new_report)
                if hasattr(evaluation, "shouldTriggerNext"):
                    evaluation.shouldTriggerNext = body.shouldTriggerNext

        # Update the ticker report evaluations and upload the new state.
        ticker_report.evaluationsOfLatest10Q = evaluations
        ticker_file_key = get_ticker_file_key(body.ticker)
        upload_to_s3(
            ticker_report.model_dump_json(indent=2),
            ticker_file_key,
            content_type="application/json",
        )

        return (
            jsonify({"success": True, "message": "Ticker processed successfully."}),
            200,
        )

    except Exception as e:
        return handle_exception(e)


@public_equity_api.route("/criterion-metrics", methods=["POST"])
@validate(body=SaveCriterionMetricsRequest)
def save_criterion_metrics(body: SaveCriterionMetricsRequest):
    try:
        ticker_report = get_ticker_report(body.ticker)
        evaluations = ticker_report.evaluationsOfLatest10Q or []

        # Find the evaluation for the given criterionKey
        evaluation = next(
            (e for e in evaluations if e.criterionKey == body.criterionKey), None
        )

        # Build new importantMetrics using the provided metrics
        new_metrics = ImportantMetrics(status="Completed", metrics=body.metrics)

        if evaluation is None:
            # If no evaluation exists, create one with the metrics
            evaluation = CriteriaEvaluation(
                criterionKey=body.criterionKey,
                importantMetrics=new_metrics,
                reports=None,
                performanceChecklist=None,
            )
            evaluations.append(evaluation)
        else:
            # Update the importantMetrics of the existing evaluation
            evaluation.importantMetrics = new_metrics

        # Save updated evaluations back into the ticker report and upload to S3
        ticker_report.evaluationsOfLatest10Q = evaluations
        ticker_file_key = get_ticker_file_key(body.ticker)
        upload_to_s3(
            ticker_report.model_dump_json(indent=2),
            ticker_file_key,
            content_type="application/json",
        )

        return (
            jsonify(
                {"success": True, "message": "Criterion metrics saved successfully."}
            ),
            200,
        )

    except Exception as e:
        return handle_exception(e)


@public_equity_api.route("/criterion-performance-checklist", methods=["POST"])
@validate(body=SavePerformanceChecklistRequest)
def save_criterion_performance_checklist(body: SavePerformanceChecklistRequest):
    try:
        ticker_report = get_ticker_report(body.ticker)
        evaluations = ticker_report.evaluationsOfLatest10Q or []

        # Save the performance checklist to S3 and get back its URL.
        save_performance_checklist(
            body.ticker, body.criterionKey, body.performanceChecklist
        )

        # Find the evaluation for the given criterionKey
        evaluation = next(
            (e for e in evaluations if e.criterionKey == body.criterionKey), None
        )

        if evaluation is None:
            # If no evaluation exists, create one with the performance checklist
            evaluation = CriteriaEvaluation(
                criterionKey=body.criterionKey,
                performanceChecklist=body.performanceChecklist,
                importantMetrics=None,
                reports=None,
            )
            evaluations.append(evaluation)
        else:
            # Update the existing evaluation's performance checklist
            evaluation.performanceChecklist = body.performanceChecklist

        # Determine if this evaluation is not the last one in the evaluations list.
        # If not last, trigger the next criterion report by setting shouldTriggerNext = True.
        index = evaluations.index(evaluation)
        should_trigger_next = index < (len(evaluations) - 1)
        if hasattr(evaluation, "shouldTriggerNext"):
            evaluation.shouldTriggerNext = should_trigger_next

        # Save updated evaluations back into the ticker report and upload to S3
        ticker_report.evaluationsOfLatest10Q = evaluations
        ticker_file_key = get_ticker_file_key(body.ticker)
        upload_to_s3(
            ticker_report.model_dump_json(indent=2),
            ticker_file_key,
            content_type="application/json",
        )

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Performance checklist saved successfully.",
                }
            ),
            200,
        )

    except Exception as e:
        return handle_exception(e)


@public_equity_api.route("/copy-ai-criteria", methods=["POST"])
@validate(body=CreateCriteriaRequest)
def copy_ai_criteria_to_custom(body: CreateCriteriaRequest):
    try:
        print(
            f"Copy AI criteria for: sectorId: {body.sectorId}, industryGroupId: {body.industryGroupId}"
        )
        custom_criteria_list: CriteriaLookupList = get_criteria_lookup_list()

        criteria_lookup_item = get_matching_criteria_lookup_item(
            custom_criteria_list, body.sectorId, body.industryGroupId
        )

        ai_criteria_data = get_ai_criteria(criteria_lookup_item)

        custom_criteria_url = upload_custom_criteria_to_s3(
            criteria_lookup_item, ai_criteria_data
        )

        update_criteria_lookup_list_for_custom_criteria(
            criteria_lookup_item, custom_criteria_url
        )

        return (
            jsonify(
                {
                    "success": True,
                    "message": "AI criteria file copied successfully.",
                    "filePath": custom_criteria_url,
                }
            ),
            200,
        )

    except Exception as e:
        return handle_exception(e)
