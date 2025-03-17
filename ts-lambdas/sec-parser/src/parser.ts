// Imports
import axios from "axios";
import * as fs from "fs";
import * as dotenv from "dotenv";
import * as cheerio from "cheerio";
import * as console from "node:console";

dotenv.config();

// --- Interfaces for TOC structures ---
export interface ITocNode {
  name?: string;
  anchorId?: string;
  parts?: ITocNode[];
  items?: ITocNode[];
  subItems?: ITocNode[];
  // This field will be added dynamically.
  content?: ElementContents;
}

export interface ITocDict {
  parts: ITocNode[];
}

// --- New Models for Section Content ---
export class TableData {
  title?: string;
  info?: string;
  markdownTableContent: string;

  constructor(markdownTableContent: string, title?: string, info?: string) {
    this.markdownTableContent = markdownTableContent;
    this.title = title;
    this.info = info;
  }

  toMarkdownString(): string {
    const parts: string[] = [];
    if (this.title) {
      parts.push(`**${this.title}**`);
    }
    if (this.info) {
      parts.push(this.info);
    }
    if (this.markdownTableContent) {
      parts.push(this.markdownTableContent);
    }
    return parts.join("\n\n");
  }
}

export class ElementContents {
  data: TableData[];
  text: string;

  constructor(data: TableData[], text: string) {
    this.data = data;
    this.text = text;
  }

  toMarkdownString(): string {
    const parts: string[] = [];
    if (this.text) {
      parts.push(this.text);
    }
    this.data.forEach((table) => {
      const tableMd: string = table.toMarkdownString();
      if (tableMd) {
        parts.push(tableMd);
      }
    });
    return parts.join("\n\n").trim();
  }
}

// --- Updated Models for the output structure ---
export class TenQSubSubItemWithContent {
  name: string;
  anchorId: string;
  content: ElementContents;

  constructor(name: string, anchorId: string, content: ElementContents) {
    this.name = name;
    this.anchorId = anchorId;
    this.content = content;
  }

  toMarkdownString(level: number = 4): string {
    const header: string = `${"#".repeat(level)} ${this.name}`;
    const contentMd: string = this.content.toMarkdownString();
    return `${header}\n\n${contentMd}`.trim();
  }
}

export class TenQSubItemWithContent {
  name: string;
  anchorId: string;
  content: ElementContents;
  subItems: TenQSubSubItemWithContent[];

  constructor(
    name: string,
    anchorId: string,
    content: ElementContents,
    subItems: TenQSubSubItemWithContent[]
  ) {
    this.name = name;
    this.anchorId = anchorId;
    this.content = content;
    this.subItems = subItems;
  }

  toMarkdownString(level: number = 3): string {
    const header: string = `${"#".repeat(level)} ${this.name}`;
    const childrenMd: string = this.subItems
      .map((child) => child.toMarkdownString(level + 1))
      .join("\n\n");
    const contentMd: string = this.content.toMarkdownString();
    const mdParts: string[] = [header, contentMd];
    if (childrenMd) {
      mdParts.push(childrenMd);
    }
    return mdParts.join("\n\n").trim();
  }
}

export class TenQItemWithContent {
  name: string;
  anchorId: string;
  content: ElementContents;
  subItems: TenQSubItemWithContent[];

  constructor(
    name: string,
    anchorId: string,
    content: ElementContents,
    subItems: TenQSubItemWithContent[]
  ) {
    this.name = name;
    this.anchorId = anchorId;
    this.content = content;
    this.subItems = subItems;
  }

  toMarkdownString(level: number = 2): string {
    const header: string = `${"#".repeat(level)} ${this.name}`;
    const childrenMd: string = this.subItems
      .map((child) => child.toMarkdownString(level + 1))
      .join("\n\n");
    const contentMd: string = this.content.toMarkdownString();
    const mdParts: string[] = [header, contentMd];
    if (childrenMd) {
      mdParts.push(childrenMd);
    }
    return mdParts.join("\n\n").trim();
  }
}

export class PartWithContent {
  name: string;
  content: ElementContents;
  items: TenQItemWithContent[];

  constructor(name: string, content: ElementContents, items: TenQItemWithContent[]) {
    this.name = name;
    this.content = content;
    this.items = items;
  }

  toMarkdownString(level: number = 1): string {
    const header: string = `${"#".repeat(level)} ${this.name}`;
    const childrenMd: string = this.items
      .map((item) => item.toMarkdownString(level + 1))
      .join("\n\n");
    const contentMd: string = this.content.toMarkdownString();
    const mdParts: string[] = [header, contentMd];
    if (childrenMd) {
      mdParts.push(childrenMd);
    }
    return mdParts.join("\n\n").trim();
  }
}

export class TenQSectionsWithContent {
  parts: PartWithContent[];

  constructor(parts: PartWithContent[]) {
    this.parts = parts;
  }

  toMarkdownString(): string {
    return this.parts.map((part) => part.toMarkdownString(1)).join("\n\n");
  }
}

// --- Helper Functions ---

// Process a table element to remove nested tables and convert it to a markdown string.

export function processTableElementUsingTurndown(
  tableEl: cheerio.Element,
  $: cheerio.Root
): TableData {
  // Get the full HTML for the table.
  const tableHtml = $.html(tableEl);
/*

  // Initialize TurndownService with some options.
  const turndownService = new TurndownService();

  // Use the gfm plugin
  turndownService.use(gfm)

  // Use the table and strikethrough plugins only
  turndownService.use([tables, strikethrough])

  // Convert the HTML table to Markdown.
  const markdownTable = turndownService.turndown(tableHtml);

*/

  return new TableData(tableHtml, "", undefined);
}

// Recursively traverse a slice of elements to extract any table elements.
export function extractAllTables(
  contentSlice: cheerio.Element[],
  $: cheerio.Root
): TableData[] {
  let tableDataList: TableData[] = [];
  contentSlice.forEach((el) => {
    const tag = (el as cheerio.TagElement).tagName;
    if (tag === "table") {
      tableDataList.push(processTableElementUsingTurndown(el, $));
    } else {
      const children = $(el).children().toArray();
      tableDataList = tableDataList.concat(extractAllTables(children, $));
    }
  });
  return tableDataList;
}


// Process a slice of HTML elements into an ElementContents object.
// export function processContentSlice(
//   contentSlice: cheerio.Element[],
//   $: cheerio.Root
// ): ElementContents {
//   // Use clones so we don’t modify the original slice.
//   const clonedForTables = contentSlice.map((el) => $(el).clone()[0] as cheerio.Element);
//   const clonedForText = contentSlice.map((el) => $(el).clone()[0] as cheerio.Element);
//
//   const tables: TableData[] = extractAllTables(clonedForTables, $);
//   const text: string = extractTextWithoutTables(clonedForText, $);
//   return new ElementContents(tables, text);
// }

function processInlineNode(node: cheerio.Element, $: cheerio.Root): string {
  if (node.type === 'text') {
    return node.data ? node.data : "";
  } else if (node.type === 'tag') {
    if (node.tagName.toLowerCase() === 'table') {
      // Convert the table element to markdown.
      return processTableElementUsingTurndown(node, $).toMarkdownString();
    } else {
      // Process all children inline.
      let result = "";
      $(node).contents().each((_, child) => {
        result += processInlineNode(child, $);
      });
      return result;
    }
  }
  return "";
}

// Updated processContentSlice that produces a single inline markdown string,
// preserving the order of text and tables.
export function processContentSlice(
  contentSlice: cheerio.Element[],
  $: cheerio.Root
): ElementContents {
  const inlineMarkdownParts: string[] = [];
  contentSlice.forEach((node) => {
    const md = processInlineNode(node, $).trim();
    if (md) {
      inlineMarkdownParts.push(md);
    }
  });
  // Join parts with double newlines to preserve separation.
  const combinedMarkdown = inlineMarkdownParts.join("\n\n");
  // Here we return an ElementContents that has an empty table data array,
  // with all inline content stored in the text field.
  return new ElementContents([], combinedMarkdown);
}

// Extract content for a given TOC node based on a stop selector
function extractContentForNode($: cheerio.Root, node: ITocNode, siblingSelector: string): ElementContents {
  if (!node.anchorId || node.anchorId.trim() === "") {
    return new ElementContents([], "");
  }
  const anchor = $(`#${node.anchorId}`);
  if (!anchor.length) {
    return new ElementContents([], "");
  }
  // Get all sibling nodes after the anchor until we hit an element that matches one of the sibling anchors.
  const contentNodes = anchor.nextUntil(siblingSelector).toArray();
  return processContentSlice(contentNodes, $);
}


// --- Helper to build a selector string for a set of TOC nodes with valid anchor IDs.
function buildSiblingAnchorSelector(nodes: ITocNode[]): string {
  return nodes
    .filter((n) => n.anchorId && n.anchorId.trim() !== "")
    .map((n) => `#${n.anchorId}`)
    .join(", ");
}

/**
 * Recursively assign content to each TOC node.
 *
 * For a given node:
 * - If the node has child nodes (from any level: parts, items, subItems),
 *   then we use the earliest child anchor as a boundary.
 *   This means the node’s own content is extracted only from its anchor until the first child’s anchor.
 *
 * - Otherwise, we extract content from its anchor until the sibling boundary (derived from all siblings).
 *
 * This approach ensures that if content is assigned to a subitem or subsubitem, it is not repeated in the parent.
 */
// New helper: Recursively collect all valid anchor IDs from a node’s descendants.
function getDescendantAnchors(node: ITocNode): string[] {
  let anchors: string[] = [];
  if (node.parts) {
    node.parts.forEach(child => {
      if (child.anchorId && child.anchorId.trim() !== "") {
        anchors.push(child.anchorId);
      }
      anchors = anchors.concat(getDescendantAnchors(child));
    });
  }
  if (node.items) {
    node.items.forEach(child => {
      if (child.anchorId && child.anchorId.trim() !== "") {
        anchors.push(child.anchorId);
      }
      anchors = anchors.concat(getDescendantAnchors(child));
    });
  }
  if (node.subItems) {
    node.subItems.forEach(child => {
      if (child.anchorId && child.anchorId.trim() !== "") {
        anchors.push(child.anchorId);
      }
      anchors = anchors.concat(getDescendantAnchors(child));
    });
  }
  return anchors;
}

// Helper: Build a selector string from an array of anchor IDs.
function buildDescendantAnchorSelector(anchors: string[]): string {
  return anchors.map(id => `#${id}`).join(", ");
}

/**
 * Recursively assign content to each TOC node.
 *
 * For a given node:
 * - We compute a selector representing all descendant anchors.
 * - If any are found, we extract content only from the node’s anchor until the first descendant anchor.
 *   This ensures that content that belongs to children (or deeper) is excluded from the parent.
 * - Otherwise, we fall back to using the sibling boundary.
 */
function assignContentToNode(node: ITocNode, siblings: ITocNode[], $: cheerio.Root): void {
  // Build a selector from the sibling list for the overall boundary.
  const siblingSelector = buildSiblingAnchorSelector(siblings);

  // Get all descendant anchors from this node.
  const descendantAnchors = getDescendantAnchors(node);
  const descendantSelector = buildDescendantAnchorSelector(descendantAnchors);

  if (descendantSelector.trim() !== "") {
    // Extract only the content from the node's anchor until the first descendant anchor.
    node.content = extractContentForNode($, node, descendantSelector);
  } else {
    // Otherwise, use the sibling boundary.
    node.content = extractContentForNode($, node, siblingSelector);
  }

  // Now recursively assign content to children.
  if (node.parts && node.parts.length > 0) {
    node.parts.forEach(child => assignContentToNode(child, node.parts!, $));
  }
  if (node.items && node.items.length > 0) {
    node.items.forEach(child => assignContentToNode(child, node.items!, $));
  }
  if (node.subItems && node.subItems.length > 0) {
    node.subItems.forEach(child => assignContentToNode(child, node.subItems!, $));
  }
}

// --- New Implementation of parseHtmlToSections ---
//
// This function loads the HTML with Cheerio, removes inline styles,
// and then assigns content to each node by recursively walking the TOC.
// With the updated assignContentToNode logic, a parent node’s content will stop
// at the first child anchor so that duplicate content is not included.
export function parseHtmlToSections(
  htmlContent: string,
  toc: ITocDict
): TenQSectionsWithContent {
  const $ = cheerio.load(htmlContent);
  $("*").removeAttr("style");

  // Recursively assign content for each top-level part.
  toc.parts.forEach(part => assignContentToNode(part, toc.parts, $));

  // Convert the enriched TOC tree into our final model.
  function convertPart(node: ITocNode): PartWithContent {
    const items: TenQItemWithContent[] = (node.items || []).map(convertItem);
    return new PartWithContent(node.name || "", node.content as ElementContents, items);
  }
  function convertItem(node: ITocNode): TenQItemWithContent {
    const subItems: TenQSubItemWithContent[] = (node.subItems || []).map(convertSubItem);
    return new TenQItemWithContent(node.name || "", node.anchorId || "", node.content as ElementContents, subItems);
  }
  function convertSubItem(node: ITocNode): TenQSubItemWithContent {
    const subSubItems: TenQSubSubItemWithContent[] = (node.subItems || []).map(convertSubSubItem);
    return new TenQSubItemWithContent(node.name || "", node.anchorId || "", node.content as ElementContents, subSubItems);
  }
  function convertSubSubItem(node: ITocNode): TenQSubSubItemWithContent {
    return new TenQSubSubItemWithContent(node.name || "", node.anchorId || "", node.content as ElementContents);
  }

  const partsConverted: PartWithContent[] = toc.parts.map(convertPart);
  return new TenQSectionsWithContent(partsConverted);
}

// For this example, we define TableOfContents as equivalent to ITocDict.
export interface TableOfContents extends ITocDict {}

// Sample toc JSON (as provided).
const tocJson: string = `
{
  "parts": [
    {
      "name": "Part I - Financial Information",
      "items": [
        {
          "name": "Item 1: Financial Statements (unaudited)",
          "anchorId": "id3dda453371b496d93ed3b3548b5c007_10",
          "subItems": [
            {
              "name": "Index To Financial Statements",
              "anchorId": "",
              "subItems": [
                {
                  "name": "Consolidated Balance Sheets as of September 30, 2024 and December 31, 2023",
                  "anchorId": "id3dda453371b496d93ed3b3548b5c007_16"
                },
                {
                  "name": "Consolidated Statements of Income and Comprehensive Income for the quarters and nine months ended September 30, 2024 and 2023",
                  "anchorId": "id3dda453371b496d93ed3b3548b5c007_19"
                },
                {
                  "name": "Consolidated Statements of Changes in Equity for the quarters and nine months ended September 30, 2024 and 2023",
                  "anchorId": "id3dda453371b496d93ed3b3548b5c007_22"
                },
                {
                  "name": "Consolidated Statements of Cash Flows for the nine months ended September 30, 2024 and 2023",
                  "anchorId": "id3dda453371b496d93ed3b3548b5c007_28"
                },
                {
                  "name": "Notes to Consolidated Financial Statements",
                  "anchorId": "id3dda453371b496d93ed3b3548b5c007_31"
                }
              ]
            }
          ]
        },
        {
          "name": "Item 2: Management’s Discussion and Analysis of Financial Condition and Results of Operations",
          "anchorId": "id3dda453371b496d93ed3b3548b5c007_79",
          "subItems": []
        },
        {
          "name": "Item 3: Quantitative and Qualitative Disclosures About Market Risk",
          "anchorId": "id3dda453371b496d93ed3b3548b5c007_100",
          "subItems": []
        },
        {
          "name": "Item 4: Controls and Procedures",
          "anchorId": "id3dda453371b496d93ed3b3548b5c007_103",
          "subItems": []
        }
      ]
    },
    {
      "name": "Part II - Other Information",
      "items": [
        {
          "name": "Item 1: Legal Proceedings",
          "anchorId": "id3dda453371b496d93ed3b3548b5c007_109",
          "subItems": []
        },
        {
          "name": "Item 1A: Risk Factors",
          "anchorId": "id3dda453371b496d93ed3b3548b5c007_112",
          "subItems": []
        },
        {
          "name": "Item 2: Unregistered Sales of Equity Securities and Use of Proceeds",
          "anchorId": "id3dda453371b496d93ed3b3548b5c007_115",
          "subItems": []
        },
        {
          "name": "Item 3: Defaults Upon Senior Securities",
          "anchorId": "id3dda453371b496d93ed3b3548b5c007_118",
          "subItems": []
        },
        {
          "name": "Item 4: Mine Safety Disclosures",
          "anchorId": "id3dda453371b496d93ed3b3548b5c007_121",
          "subItems": []
        },
        {
          "name": "Item 5: Other Information",
          "anchorId": "id3dda453371b496d93ed3b3548b5c007_124",
          "subItems": []
        },
        {
          "name": "Item 6: Exhibits",
          "anchorId": "id3dda453371b496d93ed3b3548b5c007_127",
          "subItems": [
            {
              "name": "10.1 (a) Second Amendment, dated July 18, 2024",
              "anchorId": "link_placeholder_1",
              "subItems": []
            },
            {
              "name": "10.2 (b) Third Amended and Restated Credit Agreement, dated as of April 19, 2021",
              "anchorId": "link_placeholder_2",
              "subItems": []
            },
            {
              "name": "31.1 Certification of Chief Financial Officer Pursuant to Section 302 of the Sarbanes-Oxley Act of 2002",
              "anchorId": "link_placeholder_3",
              "subItems": []
            },
            {
              "name": "31.2 Certification of Chief Executive Officer Pursuant to Section 302 of the Sarbanes-Oxley Act of 2002",
              "anchorId": "link_placeholder_4",
              "subItems": []
            },
            {
              "name": "32.1 Certification of Chief Financial Officer Pursuant to 18 U.S.C. Section 1350",
              "anchorId": "link_placeholder_5",
              "subItems": []
            },
            {
              "name": "32.2 Certification of Chief Executive Officer Pursuant to 18 U.S.C. Section 1350",
              "anchorId": "link_placeholder_6",
              "subItems": []
            },
            {
              "name": "Inline XBRL Documents",
              "anchorId": "",
              "subItems": [
                {
                  "name": "101.INS XBRL Instance Document",
                  "anchorId": ""
                },
                {
                  "name": "101.SCH Inline XBRL Taxonomy Extension Schema Document",
                  "anchorId": ""
                },
                {
                  "name": "101.CAL Inline XBRL Taxonomy Extension Calculation Linkbase Document",
                  "anchorId": ""
                },
                {
                  "name": "101.LAB Inline XBRL Taxonomy Extension Label Linkbase Document",
                  "anchorId": ""
                },
                {
                  "name": "101.PRE Inline XBRL Taxonomy Extension Presentation Linkbase Document",
                  "anchorId": ""
                },
                {
                  "name": "101.DEF Inline XBRL Taxonomy Extension Definition Linkbase Document",
                  "anchorId": ""
                },
                {
                  "name": "104 Cover Page Interactive Data File included as Exhibit 101",
                  "anchorId": ""
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
`;

const SEC_HEADERS = {
  "User-Agent": "Your Name (your.email@domain.com)",
  "Accept-Encoding": "gzip, deflate",
  Host: "www.sec.gov",
};

// Fetches the SEC HTML document.
export async function fetchSecHtml(url: string): Promise<string | null> {
  try {
    const response = await axios.get(url, { headers: SEC_HEADERS, timeout: 10000 });
    return response.data;
  } catch (e) {
    console.error("Error fetching document:", e);
    return null;
  }
}


// --- Main Execution ---
export async function main(): Promise<void> {
  // EDGAR-related functionality is not provided in this example.
  // Replace the following with your own SEC/EDGAR URL logic.
  const htmlUrl: string = "https://www.sec.gov/Archives/edgar/data/895417/000089541724000102/els-20240930.htm"; // update as needed

  const htmlContent: string | null = await fetchSecHtml(htmlUrl);
  if (!htmlContent) {
    throw new Error("Error fetching SEC document");
  }

  // Parse the tocJson
  const tocParsed: TableOfContents = JSON.parse(tocJson);
  const parsedContents: TenQSectionsWithContent = parseHtmlToSections(htmlContent, tocParsed);

  // Convert parsed content to markdown.
  const markdownString: string = parsedContents.toMarkdownString();
  // console.log(markdownString);

  // Save the markdown string to a file.
  const outputFilename: string = "10q_content.md";
  fs.writeFileSync(outputFilename, markdownString, { encoding: "utf-8" });
  console.log(`Markdown content saved to ${fs.realpathSync(outputFilename)}`);
}
