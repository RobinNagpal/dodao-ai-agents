import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import { PrismaClient } from '@prisma/client';
import { newsRoutes } from './routes/newsRoutes';
import logger, { logStep } from './utils/logger';

// Initialize Prisma client
logStep('Initializing Prisma client');
const prisma = new PrismaClient();

// Create Express app
logStep('Creating Express app');
const app = express();
const port = process.env.PORT || 3000;

// Middleware
logStep('Setting up middleware');
app.use(cors());
logger.info('CORS middleware enabled');

app.use(helmet());
logger.info('Helmet security middleware enabled');

app.use(morgan('dev'));
logger.info('Morgan logging middleware enabled');

app.use(express.json());
logger.info('JSON body parser enabled');

// Routes
logStep('Registering routes');
app.use('/api', newsRoutes);
logger.info('News routes registered at /api');

// Health check endpoint
logStep('Setting up health check endpoint');
app.get('/health', (req, res) => {
  logger.info('Health check endpoint called');
  try {
    res.status(200).json({ status: 'ok' });
    logger.info('Health check returned OK status');
  } catch (error: any) {
    logger.error('Error in health check endpoint', error);
    res.status(500).json({
      error: 'Internal server error',
      details: error?.message || 'Unknown error occurred'
    });
  }
});

// Global error handler
logStep('Setting up global error handler');
app.use((err: any, req: express.Request, res: express.Response, next: express.NextFunction) => {
  logger.error('Unhandled error in request', err, {
    path: req.path,
    method: req.method
  });
  res.status(500).json({
    error: 'Internal server error',
    details: err?.message || 'Unknown error occurred'
  });
});

// Start server
logStep('Starting server');
app.listen(port, () => {
  logger.info(`Server is running on port ${port}`);
});

// Handle graceful shutdown
logStep('Setting up graceful shutdown handlers');
process.on('SIGTERM', async () => {
  logger.info('SIGTERM signal received: closing HTTP server');
  await prisma.$disconnect();
  logger.info('Prisma client disconnected');
  process.exit(0);
});

process.on('SIGINT', async () => {
  logger.info('SIGINT signal received: closing HTTP server');
  await prisma.$disconnect();
  logger.info('Prisma client disconnected');
  process.exit(0);
});

export default app;
