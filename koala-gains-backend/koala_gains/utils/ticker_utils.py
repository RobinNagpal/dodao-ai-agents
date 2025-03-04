def create_new_ticker_report(ticker: str, sector_id: int, industry_group_id: int) -> None:
    try:
        # It is assumed that request.json matches the EquityDetailsDict type.
        criteria_request: CreateCriteriaRequest = {
            "sectorId": sector_id,
            "industryGroupId": industry_group_id,
        }
        print(f"Creating AI criteria for: {criteria_request}")
        custom_criteria_list: CriteriaLookupList = get_criteria_lookup_list()
        mathing_criteria = get_matching_criteria(
            custom_criteria_list,
            criteria_request.get("sectorId"),
            criteria_request.get("industryGroupId"),
        )

        final_data: IndustryGroupCriteriaStructure = generate_ai_criteria(
            mathing_criteria
        )
        ai_criteria_url: str = upload_ai_criteria_to_s3(mathing_criteria, final_data)
        update_criteria_lookup_list(mathing_criteria, ai_criteria_url)

        return (
            f"Successfully created AI criteria for ticker: {ticker} with sectorId: {sector_id} and industryGroupId: {industry_group_id}"
        )
    except Exception as e:
        print(f"Error creating AI criteria for ticker: {ticker} with sectorId: {sector_id} and industryGroupId: {industry_group_id}")
        print(e)
        return f"Error creating AI criteria for ticker: {ticker} with sectorId: {sector_id} and industryGroupId: {industry_group_id}"
