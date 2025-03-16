from bs4 import BeautifulSoup, Tag
from pydantic import BaseModel
from typing import List, Optional, Tuple, Set, Dict, TypedDict
import copy
import pandas as pd

# --- TypedDicts for TOC structures ---
class TocNode(TypedDict, total=False):
    anchorId: str
    parts: List["TocNode"]
    items: List["TocNode"]
    subItems: List["TocNode"]
    # This field will be added dynamically:
    content: Dict[str, object]

class TocDict(TypedDict):
    parts: List[TocNode]


# --- New Models for Section Content ---
class TableData(BaseModel):
    title: Optional[str] = None
    info: Optional[str] = None
    markdownTableContent: str

    def to_markdown_string(self) -> str:
        parts: List[str] = []
        if self.title:
            parts.append(f"**{self.title}**")
        if self.info:
            parts.append(self.info)
        if self.markdownTableContent:
            parts.append(self.markdownTableContent)
        return "\n\n".join(parts)


class ElementContents(BaseModel):
    data: List[TableData]
    text: str

    def to_markdown_string(self) -> str:
        parts: List[str] = []
        if self.text:
            parts.append(self.text)
        for table in self.data:
            table_md: str = table.to_markdown_string()
            if table_md:
                parts.append(table_md)
        return "\n\n".join(parts)


# --- Updated Pydantic models for the output structure ---
class TenQSubSubItemWithContent(BaseModel):
    name: str
    anchorId: str
    content: ElementContents

    def to_markdown_string(self, level: int = 4) -> str:
        header: str = f"{'#' * level} {self.name}"
        content_md: str = self.content.to_markdown_string()
        return f"{header}\n\n{content_md}".strip()


class TenQSubItemWithContent(BaseModel):
    name: str
    anchorId: str
    content: ElementContents
    subItems: List[TenQSubSubItemWithContent]

    def to_markdown_string(self, level: int = 3) -> str:
        header: str = f"{'#' * level} {self.name}"
        children_md: str = "\n\n".join(
            child.to_markdown_string(level=level + 1) for child in self.subItems
        )
        content_md: str = self.content.to_markdown_string()
        md_parts: List[str] = [header, content_md]
        if children_md:
            md_parts.append(children_md)
        return "\n\n".join(md_parts).strip()


class TenQItemWithContent(BaseModel):
    name: str
    anchorId: str
    content: ElementContents
    subItems: List[TenQSubItemWithContent]

    def to_markdown_string(self, level: int = 2) -> str:
        header: str = f"{'#' * level} {self.name}"
        children_md: str = "\n\n".join(
            child.to_markdown_string(level=level + 1) for child in self.subItems
        )
        content_md: str = self.content.to_markdown_string()
        md_parts: List[str] = [header, content_md]
        if children_md:
            md_parts.append(children_md)
        return "\n\n".join(md_parts).strip()


class PartWithContent(BaseModel):
    name: str
    content: ElementContents
    items: List[TenQItemWithContent]

    def to_markdown_string(self, level: int = 1) -> str:
        header: str = f"{'#' * level} {self.name}"
        children_md: str = "\n\n".join(
            item.to_markdown_string(level=level + 1) for item in self.items
        )
        content_md: str = self.content.to_markdown_string()
        md_parts: List[str] = [header, content_md]
        if children_md:
            md_parts.append(children_md)
        return "\n\n".join(md_parts).strip()


class TenQSectionsWithContent(BaseModel):
    parts: List[PartWithContent]

    def to_markdown_string(self) -> str:
        return "\n\n".join(part.to_markdown_string(level=1) for part in self.parts)


# --- Helper Functions ---

def flatten_toc(toc: TocDict) -> List[TocNode]:
    """
    Recursively traverses the TOC structure (with 'parts', 'items', and 'subItems')
    and returns a flattened list of nodes that have a non-empty "anchorId".
    """
    flattened: List[TocNode] = []

    def traverse(node: TocNode) -> None:
        if node.get("anchorId"):
            flattened.append(node)
        for key in ["parts", "items", "subItems"]:
            for child in node.get(key, []):
                traverse(child)

    for part in toc.get("parts", []):
        traverse(part)
    return flattened


def build_id_to_element(soup: BeautifulSoup) -> Tuple[Dict[str, Tag], List[Tag]]:
    """
    Returns a mapping from element id to element and a list of all elements.
    """
    all_elements: List[Tag] = list(soup.find_all(True))
    id_to_element: Dict[str, Tag] = {el.get("id"): el for el in all_elements if el.get("id")}
    return id_to_element, all_elements


def get_ordered_elements(id_to_element: Dict[str, Tag], anchor_list: List[str]) -> List[Tag]:
    """
    Orders the HTML elements according to the list of anchors.
    """
    return [id_to_element[aid] for aid in anchor_list if aid in id_to_element]


def process_table_element(table_el: Tag, processed_table_ids: Set[int]) -> TableData:
    """
    Processes a table element by converting it to a markdown table using pandas.
    Marks the table and its descendants as processed.
    """
    processed_table_ids.add(id(table_el))
    for descendant in table_el.find_all():
        processed_table_ids.add(id(descendant))

    try:
        df_list: List[pd.DataFrame] = pd.read_html(str(table_el))
        if df_list:
            df: pd.DataFrame = df_list[0]
            # If column headers are numeric, assume the first row contains headers.
            if all(isinstance(col, (int, float)) for col in df.columns):
                df.columns = df.iloc[0]
                df = df[1:]
            markdown_table: str = df.to_markdown(index=False)
        else:
            markdown_table = ""
    except Exception:
        markdown_table = ""
    caption_tag: Optional[Tag] = table_el.find("caption")
    title: Optional[str] = caption_tag.get_text(strip=True) if caption_tag else None

    return TableData(title=title, info=None, markdownTableContent=markdown_table)


def process_tables_in_slice(content_slice: List[Tag]) -> Tuple[List[TableData], Set[int]]:
    """
    Processes all table elements in the content slice and returns their data along with processed IDs.
    """
    processed_table_ids: Set[int] = set()
    table_data_list: List[TableData] = []
    for sub_el in content_slice:
        # Check if the element or any of its ancestors are already processed
        if any(id(ancestor) in processed_table_ids for ancestor in sub_el.find_parents() + [sub_el]):
            continue
        if sub_el.name == 'table':
            table_data: TableData = process_table_element(sub_el, processed_table_ids)
            table_data_list.append(table_data)
    return table_data_list, processed_table_ids


def extract_text_from_slice(content_slice: List[Tag], processed_table_ids: Set[int]) -> str:
    """
    Extracts text from elements in the content slice, excluding those in processed tables.
    """
    text_parts: List[str] = []
    for sub_el in content_slice:
        # Check if the element or any of its ancestors are processed
        if any(id(ancestor) in processed_table_ids for ancestor in sub_el.find_parents() + [sub_el]):
            continue
        txt: str = sub_el.get_text(separator=" ", strip=True)
        if txt:
            text_parts.append(txt)
    return " ".join(text_parts).strip()


def process_content_slice(content_slice: List[Tag]) -> ElementContents:
    """
    Processes a slice of HTML elements by splitting table processing and text extraction.
    """
    # Process tables and get their data along with processed IDs
    table_data_list, processed_table_ids = process_tables_in_slice(content_slice)
    # Extract text content while excluding processed tables and their descendants
    text_content: str = extract_text_from_slice(content_slice, processed_table_ids)
    return ElementContents(data=table_data_list, text=text_content)


def add_content_to_toc(node: TocNode, content_map: Dict[str, ElementContents]) -> TocNode:
    """
    Recursively updates a TOC node with its corresponding content from content_map.
    """
    new_node: TocNode = copy.deepcopy(node)
    if new_node.get("anchorId"):
        new_node["content"] = content_map.get(new_node["anchorId"], ElementContents(data=[], text="")).dict()
    else:
        new_node["content"] = ElementContents(data=[], text="").dict()

    for key in ["parts", "items", "subItems"]:
        if key in new_node:
            new_node[key] = [add_content_to_toc(child, content_map) for child in new_node[key]]
    return new_node


def parse_html_to_sections(html_content: str, toc: BaseModel) -> TenQSectionsWithContent:
    """
    Given the HTML content of a 10-Q document and the table-of-contents (TOC)
    as a hierarchical JSON (with keys "parts", "items", and "subItems"),
    this function:
      1. Flattens the TOC to get a list of nodes with non-empty anchorId.
      2. Parses the HTML using BeautifulSoup and builds a mapping of elements.
      3. For each anchor, extracts all elements between it and the next anchor.
         - Processes tables separately (converting them to markdown).
         - Extracts plain text from non-table elements.
      4. Recursively updates the TOC structure with the extracted content.

    Returns:
      A TenQSectionsWithContent instance with the same hierarchy but with element content.
    """
    # Convert TOC to a dictionary. We assume the toc dict adheres to TocDict.
    toc_dict: TocDict = toc.dict()  # type: ignore

    # Flatten the TOC and get the ordered list of anchorIds.
    flattened_toc: List[TocNode] = flatten_toc(toc_dict)
    anchor_list: List[str] = [node["anchorId"] for node in flattened_toc if node.get("anchorId")]

    # Parse the HTML and build mappings.
    soup: BeautifulSoup = BeautifulSoup(html_content, "html.parser")
    id_to_element, all_elements = build_id_to_element(soup)
    elements_in_order: List[Tag] = get_ordered_elements(id_to_element, anchor_list)

    # Process each section corresponding to an anchor.
    content_map: Dict[str, ElementContents] = {}
    for i, elem in enumerate(elements_in_order):
        start_idx: int = all_elements.index(elem)
        if i < len(elements_in_order) - 1:
            next_elem: Tag = elements_in_order[i + 1]
            end_idx: int = all_elements.index(next_elem)
        else:
            end_idx = len(all_elements)

        content_slice: List[Tag] = all_elements[start_idx:end_idx]
        element_contents: ElementContents = process_content_slice(content_slice)
        content_map[elem["id"]] = element_contents
    # Recursively add content to the TOC nodes.
    processed_toc: Dict[str, List[TocNode]] = {"parts": [add_content_to_toc(part, content_map) for part in toc_dict.get("parts", [])]}
    return TenQSectionsWithContent(**processed_toc)
