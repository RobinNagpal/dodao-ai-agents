import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import { PrismaClient } from '@prisma/client';
import { newsRoutes } from './routes/newsRoutes';

// Initialize Prisma client
const prisma = new PrismaClient();

// Create Express app
const app = express();
const port = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(helmet());
app.use(morgan('dev'));
app.use(express.json());

// Routes
app.use('/api', newsRoutes);

// Health check endpoint
app.get('/health', (req, res) => {
  try {
    res.status(200).json({ status: 'ok' });
  } catch (error: any) {
    console.error('Error in health check endpoint:', error);
    res.status(500).json({
      error: 'Internal server error',
      details: error?.message || 'Unknown error occurred'
    });
  }
});

// Global error handler
app.use((err: any, req: express.Request, res: express.Response, next: express.NextFunction) => {
  console.error('Unhandled error:', err);
  res.status(500).json({
    error: 'Internal server error',
    details: err?.message || 'Unknown error occurred'
  });
});

// Start server
app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});

// Handle graceful shutdown
process.on('SIGTERM', async () => {
  console.log('SIGTERM signal received: closing HTTP server');
  await prisma.$disconnect();
  process.exit(0);
});

process.on('SIGINT', async () => {
  console.log('SIGINT signal received: closing HTTP server');
  await prisma.$disconnect();
  process.exit(0);
});

export default app;
