import express from 'express';
import { PrismaClient } from '@prisma/client';
import googleNewsScraper from 'google-news-scraper';
import { GNSUserConfig } from 'google-news-scraper';
import Parser from '@postlight/parser';
import {decodeGoogleNewsUrl} from "./newGoogleDecoder";
import {ResolveError, resolveFinalUrlWithPuppeteer, ResolveResult} from "./resolve-final-url";
import {decodeGoogleNewsUrls} from "./googleNewsDecoder";


// Node 18+/Bun/Deno (has fetch). Follows redirects and returns the final URL.
export async function resolveGoogleNewsUrl(u: string, method: 'HEAD' | 'GET' = 'HEAD'): Promise<string> {
  // Try HEAD first (lighter); some sites reject HEAD → fall back to GET.
  const tryOnce = async (m: 'HEAD' | 'GET') => {
    console.log('Trying', m, 'on', u);
    const r = await fetch(u, { method: m, redirect: 'follow' });
    console.log('Response:', r);
    return r.url || u;
  };
  try {
    const finalHead = await tryOnce(method);
    if (finalHead !== u) return finalHead;
    // If HEAD didn’t redirect, try GET just in case.
    return await tryOnce('GET');
  } catch {
    console.log('HEAD failed, falling back to GET');
    // Last resort: manual redirect handling (rarely needed)
    const r = await fetch(u, { method: 'GET', redirect: 'manual' });
    const loc = r.headers.get('location');
    console.log('Final URL:', loc);
    return loc ? new URL(loc, u).toString() : u;
  }
}



const getPrettyUrl = (uglyUrl: string): string | null => {
  const base64Match = uglyUrl.match(/\/read\/([A-Za-z0-9-_]+)/);
  if (!base64Match) {
    return null;
  }
  const base64String = base64Match[1];
  try {
    const decodedString = Buffer.from(base64String, "base64").toString("ascii");
    const urlPattern = /https?:\/\/[^\s"']+/g;
    const matches = decodedString.match(urlPattern) || [];
    const urls: string[] = matches.flatMap(match => {
      const splitUrls = match.split(/(?<!http:|https:)R(?![a-zA-Z0-9-_])|(?<!http:|https:)y(?![a-zA-Z0-9-_])/);
      return splitUrls.filter(url => {
        const cleanUrl = url.trim().replace(/[^\w\-\/:.]+$/, '').replace(/\\x[0-9A-Fa-f]{2}/g, '');
        return cleanUrl;
      });
    });
    const uniqueUrls: string[] = [...new Set(urls)];
    const finalUrl = uniqueUrls.length ? uniqueUrls[0] : uglyUrl;
    console.log('Decoded string:', decodedString);
    return finalUrl;
  } catch (error) {
    console.error(error);
    return null;
  }
}


// Initialize Prisma client
const prisma = new PrismaClient();

// Create router
const router = express.Router();

/**
 * Type definition for the request body when fetching news
 */
type FetchNewsRequestBody = {
  searchTerm: string;
  prettyURLs?: boolean;
  queryVars?: {
    hl?: string;
    gl?: string;
    ceid?: string;
  };
  timeframe?: number;
  puppeteerArgs?: string[];
  limit?: number;
};

/**
 * Type definition for the request body when fetching a specific article
 */
type FetchArticleRequestBody = {
  url: string;
};

/**
 * Type definition for the request body when fetching user topics
 */
type GetUserTopicsRequestBody = {
  userId: string;
};

/**
 * Type definition for a news topic
 */
type NewsTopic = {
  id: string;
  topic: string;
  description: string;
  filters: string[];
  templateUsed: string;
  folderId: string | null;
  createdAt: Date;
  updatedAt: Date;
  createdBy: string | null;
  updatedBy: string | null;
};

/**
 * Type definition for a news article
 */
type NewsArticle = {
  title: string;
  link: string;
  published: string;
  source: string;
  summary: string;
};

/**
 * Type definition for a parsed article
 */
type ParsedArticle = {
  title: string;
  content: string;
  excerpt: string;
  author: string | null;
  date_published: string | null;
  lead_image_url: string | null;
  dek: string | null;
  next_page_url: string | null;
  url: string;
  domain: string;
  word_count: number;
  direction: string;
  total_pages: number;
  rendered_pages: number;
};

/**
 * Route for fetching user topics
 * POST /api/user-topics
 */
router.post('/user-topics', async (req, res) => {
  console.log('Request received:', JSON.stringify(req.body, null, 2));

  try {
    const body: GetUserTopicsRequestBody = req.body;
    const { userId } = body;

    if (!userId) {
      return res.status(400).json({ error: 'userId is required' });
    }

    // Fetch topics for the user from the database
    const topics = await prisma.newsTopic.findMany({
      where: {
        createdBy: userId,
      },
    });

    return res.status(200).json({ topics });
  } catch (error: any) {
    console.error('Error fetching user topics:', error);
    return res.status(500).json({
      error: 'Internal server error',
      details: error?.message,
    });
  }
});

/**
 * Route for fetching news from Google News
 * POST /api/news
 */
router.post('/news', async (req, res) => {
  console.log('Request received:', JSON.stringify(req.body, null, 2));

  try {
    const body: FetchNewsRequestBody = req.body;
    const { searchTerm } = body;

    if (!searchTerm) {
      return res.status(400).json({ error: 'searchTerm is required' });
    }

    console.log('Body:', JSON.stringify(body));

    // Configure options for the google-news-scraper
    const options: GNSUserConfig = {
      searchTerm,
      timeframe: '24h',
      limit: 10,
      puppeteerArgs: ['--no-sandbox', '--disable-setuid-sandbox'],
      prettyURLs: true,
      puppeteerHeadlessMode: true,
    };

    // Fetch news articles
    const articles = await googleNewsScraper(options);
    for (const article of articles) {
      // let decodedLink: ResolveResult | ResolveError = await resolveFinalUrlWithPuppeteer(article.link);
      // let decodedLink: ResolveResult | ResolveError = await resolveFinalUrlWithPuppeteer(article.link);
      // console.log('Decoded link:', decodedLink);
      const url = await decodeGoogleNewsUrl(article.link);
      console.log('Decoded link:', url.status? url.decodedUrl : 'not-working');
      article.link = url.status? url.decodedUrl : 'not-working';
    }
    return res.status(200).json({ articles });
  } catch (error: any) {
    console.error('Error fetching news:', error);
    return res.status(500).json({
      error: 'Internal server error',
      details: error?.message,
    });
  }
});

/**
 * Route for fetching and parsing a news article
 * POST /api/article
 */
router.post('/article', async (req, res) => {
  console.log('Request received:', JSON.stringify(req.body, null, 2));

  try {
    const body: FetchArticleRequestBody = req.body;
    const { url } = body;

    if (!url) {
      return res.status(400).json({ error: 'url is required' });
    }

    // Fetch and parse the article using @postlight/parser
    const article = await Parser.parse(url);

    if (!article) {
      return res.status(404).json({ error: 'Could not parse article' });
    }

    // Format the article data
    const articleData: ParsedArticle = {
      title: article.title,
      content: article.content,
      excerpt: article.excerpt,
      author: article.author,
      date_published: article.date_published,
      lead_image_url: article.lead_image_url,
      dek: article.dek,
      next_page_url: article.next_page_url,
      url: article.url,
      domain: article.domain,
      word_count: article.word_count,
      direction: article.direction,
      total_pages: article.total_pages,
      rendered_pages: article.rendered_pages,
    };

    return res.status(200).json({ article: articleData });
  } catch (error: any) {
    console.error('Error fetching article:', error);
    return res.status(500).json({
      error: 'Internal server error',
      details: error?.message,
    });
  }
});

export { router as newsRoutes };
