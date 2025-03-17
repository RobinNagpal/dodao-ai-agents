import 'express-async-errors';
import {fetchSecHtml, parseHtmlToSections, TableOfContents, TenQSectionsWithContent} from "@/tenq/parser";
import {createTableOfContentsStructure, findTableElementsWithToc, TocEligibleElements} from "@/tenq/tenqTOC";

import express, {json} from 'express';
import fs from "fs";
import helmet from 'helmet';
import console from "node:console";

const app = express();
app.use(json());
app.use(helmet());
app.use(express.json());

app.post('/latest-ten-q-parsed', async (req, res) => {
  const htmlUrl = req.body.latestTenQUrl
  // const htmlUrl: string = "https://www.sec.gov/Archives/edgar/data/895417/000089541724000102/els-20240930.htm"; // update as needed

  const htmlContent: string | null = await fetchSecHtml(htmlUrl);
  if (!htmlContent) {
    throw new Error("Error fetching SEC document");
  }
  try {
    const eligibleTableElements: TocEligibleElements[] = findTableElementsWithToc(htmlContent)
    console.log('Eligible Items Length ', eligibleTableElements.length)
    const combinedTableHtml = eligibleTableElements.map(e => e.cleaned_html).join("\n\n")
    const toc: TableOfContents = await createTableOfContentsStructure(combinedTableHtml)
    console.log(JSON.stringify(toc, null, 2))
    const parsedContents: TenQSectionsWithContent = parseHtmlToSections(htmlContent, toc);

    // Convert parsed content to markdown.
    const markdownString: string = parsedContents.toMarkdownString();
    // console.log(markdownString);

    // Save the markdown string to a file.
    const outputFilename: string = "10q_content.md";
    fs.writeFileSync(outputFilename, markdownString, {encoding: "utf-8"});
    console.log(`Markdown content saved to ${fs.realpathSync(outputFilename)}`);
    res.json(parsedContents);
  } catch (e) {
    console.error(e)
    res.status(500).json({
      msg: 'Error parsing SEC document',
    });

  }
});

app.use((_, res, _2) => {
  res.status(404).json({ error: 'NOT FOUND' });
});

export { app };
