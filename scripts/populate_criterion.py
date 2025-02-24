industry_sectors = {
    "name": "US Public Equities",
    "id": "us-public-equities",
    "children": [
        {
            "name": "Information Technology (IT)",
            "id": "information-technology-it",
            "children": [
                {
                    "name": "Software & Services",
                    "id": "information-technology-it-software-services",
                    "children": [
                        {
                            "name": "Application Software",
                            "id": "information-technology-it-software-services-application-software"
                        },
                        {
                            "name": "Systems Software",
                            "id": "information-technology-it-software-services-systems-software"
                        },
                        {
                            "name": "IT Consulting & Services",
                            "id": "information-technology-it-software-services-it-consulting-services"
                        },
                        {
                            "name": "Data Processing & Outsourced Services",
                            "id": "information-technology-it-software-services-data-processing-outsourced-services"
                        },
                        {
                            "name": "Internet Services & Infrastructure",
                            "id": "information-technology-it-software-services-internet-services-infrastructure"
                        }
                    ]
                },
                {
                    "name": "Technology Hardware & Equipment",
                    "id": "information-technology-it-technology-hardware-equipment",
                    "children": [
                        {
                            "name": "Communications Equipment",
                            "id": "information-technology-it-technology-hardware-equipment-communications-equipment"
                        },
                        {
                            "name": "Technology Hardware, Storage & Peripherals",
                            "id": "information-technology-it-technology-hardware-equipment-technology-hardware-storage-peripherals"
                        },
                        {
                            "name": "Electronic Components",
                            "id": "information-technology-it-technology-hardware-equipment-electronic-components"
                        },
                        {
                            "name": "Electronic Manufacturing Services",
                            "id": "information-technology-it-technology-hardware-equipment-electronic-manufacturing-services"
                        },
                        {
                            "name": "Office Electronics",
                            "id": "information-technology-it-technology-hardware-equipment-office-electronics"
                        }
                    ]
                },
                {
                    "name": "Semiconductors & Semiconductor Equipment",
                    "id": "information-technology-it-semiconductors-semiconductor-equipment",
                    "children": [
                        {
                            "name": "Semiconductor Materials & Equipment",
                            "id": "information-technology-it-semiconductors-semiconductor-equipment-semiconductor-materials-equipment"
                        },
                        {
                            "name": "Semiconductors (Design & Manufacturing)",
                            "id": "information-technology-it-semiconductors-semiconductor-equipment-semiconductors-design-manufacturing"
                        }
                    ]
                }
            ]
        },
        {
            "name": "Health Care",
            "id": "health-care",
            "children": [
                {
                    "name": "Health Care Equipment & Services",
                    "id": "health-care-health-care-equipment-services",
                    "children": [
                        {
                            "name": "Health Care Equipment",
                            "id": "health-care-health-care-equipment-services-health-care-equipment"
                        },
                        {
                            "name": "Health Care Supplies",
                            "id": "health-care-health-care-equipment-services-health-care-supplies"
                        },
                        {
                            "name": "Health Care Services (Hospitals, Managed Care)",
                            "id": "health-care-health-care-equipment-services-health-care-services-hospitals-managed-care"
                        },
                        {
                            "name": "Health Care Technology",
                            "id": "health-care-health-care-equipment-services-health-care-technology"
                        }
                    ]
                },
                {
                    "name": "Pharmaceuticals, Biotechnology & Life Sciences",
                    "id": "health-care-pharmaceuticals-biotechnology-life-sciences",
                    "children": [
                        {
                            "name": "Pharmaceuticals",
                            "id": "health-care-pharmaceuticals-biotechnology-life-sciences-pharmaceuticals"
                        },
                        {
                            "name": "Biotechnology",
                            "id": "health-care-pharmaceuticals-biotechnology-life-sciences-biotechnology"
                        },
                        {
                            "name": "Life Sciences Tools & Services",
                            "id": "health-care-pharmaceuticals-biotechnology-life-sciences-life-sciences-tools-services"
                        }
                    ]
                }
            ]
        }
    ]
    }

#  1. Write structured output
#  Call llm to return the structured output for the given input.
# save the output in a file. The file can be in output/<sector>/<subsector>/<subsubsector>.json
