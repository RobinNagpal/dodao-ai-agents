from bs4 import BeautifulSoup, Tag
from pydantic import BaseModel
from typing import List, Optional, Tuple, Dict, TypedDict
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
    all_elements: List[Tag] = list(soup.find_all(True))
    id_to_element: Dict[str, Tag] = {el.get("id"): el for el in all_elements if el.get("id")}
    return id_to_element, all_elements


def get_ordered_elements(id_to_element: Dict[str, Tag], anchor_list: List[str]) -> List[Tag]:
    return [id_to_element[aid] for aid in anchor_list if aid in id_to_element]


def process_table_element(table_el: Tag) -> TableData:
    new_table_el: Tag = copy.deepcopy(table_el)
    # Remove nested tables so that only the current table is processed.
    for nested in new_table_el.find_all("table"):
        if nested != new_table_el:
            nested.decompose()

    try:
        df_list: List[pd.DataFrame] = pd.read_html(str(new_table_el))
        if df_list:
            df: pd.DataFrame = df_list[0]
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


def extract_all_tables(content_slice: List[Tag]) -> List[TableData]:
    """
    Recursively traverses the content slice using the element’s children,
    extracting any table elements found.
    """
    table_data_list: List[TableData] = []
    for el in content_slice:
        if el.name == "table":
            table_data_list.append(process_table_element(el))
        else:
            # Iterate over direct children.
            children = [child for child in el.children if isinstance(child, Tag)]
            table_data_list.extend(extract_all_tables(children))
    return table_data_list


def extract_text_without_tables(content_slice: List[Tag]) -> str:
    """
    Combines the HTML of the content slice, re-parses it,
    removes all table elements, and then extracts text.
    """
    combined_html: str = "".join(el.decode() for el in content_slice)
    soup = BeautifulSoup(combined_html, "html.parser")
    for table in soup.find_all("table"):
        table.decompose()

    text_without_tables = soup.get_text(strip=True)
    print(text_without_tables)

    return text_without_tables


def process_content_slice(content_slice: List[Tag]) -> ElementContents:
    """
    Processes a slice of HTML elements by splitting the task into two immutable branches:
      - A tables branch that recursively extracts and processes all tables.
      - A text branch that extracts text after removing table elements.
    """
    table_data_list: List[TableData] = extract_all_tables(content_slice)
    text_content: str = extract_text_without_tables(content_slice)
    return ElementContents(data=table_data_list, text=text_content)


def add_content_to_toc(node: TocNode, content_map: Dict[str, ElementContents]) -> TocNode:
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
    Given the HTML content of a 10-Q document and a TOC (with keys "parts", "items", and "subItems"),
    this function:
      1. Flattens the TOC to get nodes with non-empty anchorId.
      2. Parses the HTML and maps elements.
      3. For each anchor, extracts the elements between it and the next anchor.
         - Processes tables recursively.
         - Removes tables before capturing plain text.
      4. Recursively updates the TOC with the extracted content.
    """
    toc_dict: TocDict = toc.dict()  # type: ignore

    flattened_toc: List[TocNode] = flatten_toc(toc_dict)
    anchor_list: List[str] = [node["anchorId"] for node in flattened_toc if node.get("anchorId")]

    soup: BeautifulSoup = BeautifulSoup(html_content, "html.parser")
    for tag in soup.find_all(True):
        if tag.has_attr("style"):
            del tag["style"]
    id_to_element, all_elements = build_id_to_element(soup)
    elements_in_order: List[Tag] = get_ordered_elements(id_to_element, anchor_list)

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

    processed_toc: Dict[str, List[TocNode]] = {
        "parts": [add_content_to_toc(part, content_map) for part in toc_dict.get("parts", [])]
    }
    return TenQSectionsWithContent(**processed_toc)
