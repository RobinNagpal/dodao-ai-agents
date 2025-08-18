# News API Service

An Express application to fetch news topics, articles, and parse article content. This service was converted from a serverless function to a containerized Express application.

## Features

- Fetch user-specific news topics from the database
- Search for news articles from Google News
- Parse and extract content from news articles
- CORS support for cross-origin requests
- Containerized with Docker for easy deployment

## API Endpoints

### POST /api/user-topics

Fetches news topics for a specific user from the database.

#### Request Body

```json
{
  "userId": "user-id-here"
}
```

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| userId | string | The ID of the user | Yes |

#### Response

```json
{
  "topics": [
    {
      "id": "topic-id-1",
      "topic": "Cryptocurrency",
      "description": "Latest news about cryptocurrency",
      "filters": ["Bitcoin", "Ethereum", "Blockchain"],
      "templateUsed": "default",
      "folderId": null,
      "createdAt": "2023-01-01T00:00:00Z",
      "updatedAt": "2023-01-02T00:00:00Z",
      "createdBy": "user-id",
      "updatedBy": null
    }
  ]
}
```

### POST /api/news

Fetches news articles from Google News based on the provided search term.

#### Request Body

```json
{
  "searchTerm": "cryptocurrency",
  "prettyURLs": true,
  "queryVars": {
    "hl": "en",
    "gl": "US",
    "ceid": "US:en"
  },
  "timeframe": 24,
  "puppeteerArgs": ["--no-sandbox", "--disable-setuid-sandbox"],
  "limit": 10
}
```

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| searchTerm | string | The term to search for | Yes |
| prettyURLs | boolean | Whether to return pretty URLs | No (default: true) |
| queryVars | object | Query variables for language and region | No |
| queryVars.hl | string | Language code | No |
| queryVars.gl | string | Country code | No |
| queryVars.ceid | string | Country and language | No |
| timeframe | number | Time frame for news in hours | No (default: 24) |
| puppeteerArgs | string[] | Arguments to pass to Puppeteer | No |
| limit | number | Maximum number of results to return | No (default: 10) |

#### Response

```json
{
  "articles": [
    {
      "title": "Article Title",
      "link": "https://example.com/article",
      "source": "Example News",
      "time": "2 hours ago",
      "snippet": "Article snippet text"
    }
  ]
}
```

### POST /api/article

Fetches and parses a news article from the provided URL.

#### Request Body

```json
{
  "url": "https://example.com/article"
}
```

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| url | string | The URL of the article to parse | Yes |

#### Response

```json
{
  "article": {
    "title": "Article Title",
    "content": "<div>Article content in HTML format</div>",
    "excerpt": "Article excerpt",
    "author": "Author Name",
    "date_published": "2023-01-01T00:00:00Z",
    "lead_image_url": "https://example.com/image.jpg",
    "dek": null,
    "next_page_url": null,
    "url": "https://example.com/article",
    "domain": "example.com",
    "word_count": 500,
    "direction": "ltr",
    "total_pages": 1,
    "rendered_pages": 1
  }
}
```

## Development

### Prerequisites

- Node.js 18.x or later
- Docker (optional, for containerized deployment)

### Installation

1. Install dependencies:

```bash
npm install
```

2. Generate Prisma client:

```bash
npx prisma generate
```

3. Start the development server:

```bash
npm run dev
```

The server will be available at http://localhost:3000.

## Deployment

### Using Docker

1. Build the Docker image:

```bash
docker build -t news-api-service .
```

2. Run the container:

```bash
docker run -p 3000:3000 -e DATABASE_URL=your-database-url news-api-service
```

### Manual Deployment

1. Build the TypeScript code:

```bash
npm run build
```

2. Start the server:

```bash
npm start
```

## Environment Variables

- `PORT`: The port the server will listen on (default: 3000)
- `DATABASE_URL`: PostgreSQL connection string for Prisma

## Dependencies

- express: Web framework for Node.js
- @prisma/client: ORM for database access
- google-news-scraper: For scraping news from Google News
- @postlight/parser: For parsing article content
- cors: For handling Cross-Origin Resource Sharing
- helmet: For adding security headers
- morgan: For HTTP request logging
- typescript: For TypeScript support
