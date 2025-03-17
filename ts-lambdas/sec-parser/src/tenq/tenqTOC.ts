import * as cheerio from "cheerio";
import {ChatOpenAI} from "@langchain/openai";
import {z} from "zod";

const model = new ChatOpenAI({
  apiKey: process.env.OPENAI_API_KEY,
  model: "gpt-4o",
  temperature: 1,
});

// Data structure interfaces
export interface TocEligibleElements {
  xpath: string;
  cleaned_html: string;
}

export interface TenQSubSubItem {
  name: string;
  anchorId: string;
}

export interface TenQSubItem {
  name: string;
  anchorId: string;
  subItems: TenQSubSubItem[];
}

export interface TenQItem {
  name: string;
  anchorId: string;
  subItems: TenQSubItem[];
}

export interface Part {
  name: string;
  items: TenQItem[];
}

export interface TableOfContents {
  parts: Part[];
}

// Zod schema for eligible table elements.
export const TocEligibleElementsSchema = z.object({
  xpath: z.string().describe("XPath of the eligible table element."),
  cleaned_html: z.string().describe("Cleaned HTML of the eligible table element, without inline styles."),
});

// Zod schema for a sub-sub-item.
export const TenQSubSubItemSchema = z.object({
  name: z.string().describe("Name of the sub-sub-item."),
  anchorId: z.string().describe("This is the id of the html element to which the hyperlink points"),
});

// Zod schema for a sub-item.
export const TenQSubItemSchema = z.object({
  name: z.string().describe("Name of the sub-item."),
  anchorId: z.string().describe("This is the id of the html element to which the hyperlink points"),
  subItems: z.array(TenQSubSubItemSchema).describe("List of sub-sub-items in the sub-item."),
});

// Zod schema for an item.
export const TenQItemSchema = z.object({
  name: z.string().describe("Name of the item."),
  anchorId: z.string().describe("This is the id of the html element to which the hyperlink points"),
  subItems: z.array(TenQSubItemSchema).describe("List of sub-items in the item."),
});

// Zod schema for a part.
export const PartSchema = z.object({
  name: z.string().describe("Name of the part."),
  items: z.array(TenQItemSchema).describe("List of items in the part."),
});

// Zod schema for the table of contents.
export const TableOfContentsSchema = z.object({
  parts: z.array(PartSchema).describe("List of parts in the 10-Q filing."),
});

/**
 * Mimics the getXPath function using raw Cheerio elements.
 * If the element has an id attribute, returns an XPath using that id.
 * Otherwise, builds the XPath by traversing up the parent chain.
 *
 * @param elem - A raw Cheerio element.
 * @returns The XPath string.
 */
export function getXpath(elem: cheerio.TagElement | null | undefined): string {
  if (!elem || !elem.name) {
    return "";
  }
  const idAttr = elem.attribs?.id;
  if (idAttr) {
    return `//*[@id='${idAttr}']`;
  }

  const parts: string[] = [];
  let current: cheerio.TagElement | null = elem;

  while (current && current.name) {
    const tagName = current.name.toLowerCase();
    let index = 1;

    // Check if the current element has a parent with children.
    if (current.parent && (current.parent as any).children) {
      // Filter parent's children for elements that are tags with the same name.
      const siblings: cheerio.Element[] = (current.parent as any).children.filter(
        (child: cheerio.Element) =>
          child.type === "tag" && child.name === current!.name
      );
      // Find the 1-based index of the current element among its siblings.
      index = siblings.findIndex((child: cheerio.Element) => child === current) + 1;
    }

    parts.unshift(`${tagName}[${index}]`);
    // Set current to the parent element (if it exists and is of type "tag").
    current = (current.parent as cheerio.TagElement) || null;
  }

  return "/" + parts.join("/");
}

/**
 * Recursively removes the "style" attribute from the provided raw Cheerio element
 * and all its descendant tag elements.
 *
 * @param elem - A raw Cheerio element.
 */
export function removeStyleAttributes(elem: cheerio.TagElement): void {
  if (elem.attribs && elem.attribs.style) {
    delete elem.attribs.style;
  }
  if (elem.children && elem.children.length > 0) {
    for (const child of elem.children) {
      // Only process child nodes that are tags.
      if (child.type === "tag") {
        removeStyleAttributes(child);
      }
    }
  }
}

/**
 * Finds table elements in the provided HTML string that:
 *  - Contain a nested <a> element, and
 *  - Have text content containing "Part" or "Item" (case-insensitive).
 *
 * For each matching table, the function logs its cleaned HTML (without inline styles)
 * and returns an array of TocEligibleElements.
 *
 * @param html - The HTML string to search.
 * @param limit - Maximum number of tables to process.
 * @returns Array of TocEligibleElements.
 */
export function findTableElementsWithToc(
  html: string,
  limit: number = 20
): TocEligibleElements[] {
  const $: cheerio.Root = cheerio.load(html);
  const tableXPaths: TocEligibleElements[] = [];
  let count = 0;

  // Get raw table elements as an array.
  const tables: cheerio.Element[] = $("table").toArray();

  for (const table of tables) {
    if (count >= limit) break;
    // We still use the Cheerio wrapper to easily search inside the element.
    const $table = $(table);
    const hasAnchor: boolean = $table.find("a").length > 0;
    const textContent: string = $table.text() || "";
    const textMatch: boolean = /(part|item)/i.test(textContent);

    if (hasAnchor && textMatch) {
      const xpath: string = getXpath(table as cheerio.TagElement);
      // To "clone" the raw element, serialize it and then load it again.
      const tableHtml = $.html(table);
      const $cloned = cheerio.load(tableHtml);
      // Assume the first top-level child is the cloned table.
      const clonedElement = $cloned.root().children().first().get(0);
      if (clonedElement) {
        removeStyleAttributes(clonedElement);
        // Get the cleaned HTML from the modified raw element.
        const cleanedHtml: string = $.html(clonedElement);
        tableXPaths.push({xpath, cleaned_html: cleanedHtml});
        console.log(
          `Table ${count + 1}: Cleaned HTML (without style attributes):\n${cleanedHtml}\n`
        );
        count++;
      }
    }
  }

  if (count === 0) {
    console.log("No table found meeting the specified criteria.");
  }

  return tableXPaths;
}


/**
 * Uses an LLM to create a table of contents structure from combined table HTML strings.
 * This function is asynchronous because it invokes the LLM API.
 *
 * @param combinedTablesStr - The combined HTML string of table elements.
 * @returns A promise that resolves to a TableOfContents object.
 */
export async function createTableOfContentsStructure(
  combinedTablesStr: string
): Promise<TableOfContents> {
  const prompt: string = `
The table elements below might have information about the sections and subsections of the 10-Q form.

Below are the parts and items that are mostly present in the 10-Q form. Each of the items then contains sub-items, and each sub-item may contain sub-sub-items.

{
    "PART I": {
        "ITEM 1": {
            "Title": "Financial Statements"
        },
        "ITEM 2": {
            "Title": "Management’s Discussion and Analysis of Financial Condition and Results of Operations"
        },
        "ITEM 3": {
            "Title": "Quantitative and Qualitative Disclosures About Market Risk"
        },
        "ITEM 4": {
            "Title": "Controls and Procedures"
        }
    },
    "PART II": {
        "ITEM 1": {
            "Title": "Legal Proceedings"
        },
        "ITEM 1A": {
            "Title": "Risk Factors"
        },
        "ITEM 2": {
            "Title": "Unregistered Sales of Equity Securities and Use of Proceeds"
        },
        "ITEM 3": {
            "Title": "Defaults Upon Senior Securities"
        },
        "ITEM 4": {
            "Title": "Mine Safety Disclosures"
        },
        "ITEM 5": {
            "Title": "Other Information"
        },
        "ITEM 6": {
            "Title": "Exhibits"
        }
    }
}

A part has items and items have subitems, and subitems can have subitems.

We want to create a nested JSON structure to represent the above information and include the id of the item and subitem whenever present in the table.

These parts, items, subitems, and subsubitems should be pointing to the element using an anchor tag (the element's id) and this is what
we will be using in the JSON structure.

Don't give me the code—just the JSON structure and try not using code for evaluating the JSON structure.

Here are the tables:

${combinedTablesStr}
`;

  // Placeholder ChatOpenAI implementation.
  // Configure the model to return output following the TableOfContents schema.
  const structuredLLM = model.withStructuredOutput<TableOfContents>(TableOfContentsSchema);
  const tocResponse: TableOfContents = await structuredLLM.invoke(prompt);
  console.log("LLM analysis response:\n", JSON.stringify(tocResponse, null, 2));
  return tocResponse;
}
