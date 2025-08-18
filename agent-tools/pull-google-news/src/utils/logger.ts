import winston from 'winston';

// Get the tool name from environment variable or default to 'pull-google-news'
const toolName = process.env.TOOL_NAME || 'pull-google-news';

// Create a custom format that includes the tool name and timestamp
const customFormat = winston.format.printf(({ level, message, timestamp, ...metadata }) => {
  const metaString = Object.keys(metadata).length ? JSON.stringify(metadata) : '';
  return `[${timestamp}] [${toolName}] [${level.toUpperCase()}]: ${message} ${metaString}`;
});

// Create the logger instance
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.colorize(),
    customFormat
  ),
  transports: [
    new winston.transports.Console()
  ]
});

// Helper function to log a step with the tool name
export const logStep = (step: string, metadata: Record<string, any> = {}) => {
  logger.info(`STEP: ${step}`, { ...metadata, tool: toolName });
};

// Export the logger methods
export default {
  info: (message: string, metadata: Record<string, any> = {}) => {
    logger.info(message, { ...metadata, tool: toolName });
  },
  error: (message: string, error?: any, metadata: Record<string, any> = {}) => {
    logger.error(message, { ...metadata, error: error?.message || error, stack: error?.stack, tool: toolName });
  },
  warn: (message: string, metadata: Record<string, any> = {}) => {
    logger.warn(message, { ...metadata, tool: toolName });
  },
  debug: (message: string, metadata: Record<string, any> = {}) => {
    logger.debug(message, { ...metadata, tool: toolName });
  },
  logStep
};
