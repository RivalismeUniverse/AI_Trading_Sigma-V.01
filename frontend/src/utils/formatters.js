/**
 * Formatting utilities for display
 */
import { format, formatDistanceToNow, parseISO } from 'date-fns';

// ===== NUMBER FORMATTING =====

/**
 * Format currency
 */
export const formatCurrency = (value, currency = 'USD', decimals = 2) => {
  if (value == null || isNaN(value)) return '$0.00';
  
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
};

/**
 * Format percentage
 */
export const formatPercent = (value, decimals = 2, showSign = true) => {
  if (value == null || isNaN(value)) return '0.00%';
  
  const sign = showSign && value > 0 ? '+' : '';
  return `${sign}${value.toFixed(decimals)}%`;
};

/**
 * Format number with thousands separator
 */
export const formatNumber = (value, decimals = 2) => {
  if (value == null || isNaN(value)) return '0';
  
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
};

/**
 * Format large numbers with K, M, B suffixes
 */
export const formatCompactNumber = (value) => {
  if (value == null || isNaN(value)) return '0';
  
  return new Intl.NumberFormat('en-US', {
    notation: 'compact',
    compactDisplay: 'short',
  }).format(value);
};

/**
 * Format crypto amount
 */
export const formatCrypto = (value, symbol = 'BTC', decimals = 8) => {
  if (value == null || isNaN(value)) return `0 ${symbol}`;
  
  return `${value.toFixed(decimals)} ${symbol}`;
};

// ===== DATE/TIME FORMATTING =====

/**
 * Format date
 */
export const formatDate = (date, formatString = 'MMM dd, yyyy') => {
  if (!date) return 'N/A';
  
  try {
    const dateObj = typeof date === 'string' ? parseISO(date) : date;
    return format(dateObj, formatString);
  } catch (error) {
    console.error('Date formatting error:', error);
    return 'Invalid date';
  }
};

/**
 * Format date and time
 */
export const formatDateTime = (date, formatString = 'MMM dd, yyyy HH:mm:ss') => {
  return formatDate(date, formatString);
};

/**
 * Format time
 */
export const formatTime = (date, formatString = 'HH:mm:ss') => {
  return formatDate(date, formatString);
};

/**
 * Format relative time (e.g., "5 minutes ago")
 */
export const formatRelativeTime = (date) => {
  if (!date) return 'N/A';
  
  try {
    const dateObj = typeof date === 'string' ? parseISO(date) : date;
    return formatDistanceToNow(dateObj, { addSuffix: true });
  } catch (error) {
    console.error('Relative time formatting error:', error);
    return 'Invalid date';
  }
};

/**
 * Format duration in seconds to readable format
 */
export const formatDuration = (seconds) => {
  if (!seconds || isNaN(seconds)) return '0s';
  
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  
  const parts = [];
  if (hours > 0) parts.push(`${hours}h`);
  if (minutes > 0) parts.push(`${minutes}m`);
  if (secs > 0 || parts.length === 0) parts.push(`${secs}s`);
  
  return parts.join(' ');
};

// ===== TRADING SPECIFIC =====

/**
 * Format symbol (e.g., BTC/USDT:USDT -> BTC/USDT)
 */
export const formatSymbol = (symbol) => {
  if (!symbol) return 'N/A';
  return symbol.split(':')[0];
};

/**
 * Format side (long/short) with emoji
 */
export const formatSide = (side) => {
  if (!side) return 'N/A';
  
  const formatted = {
    long: '📈 Long',
    short: '📉 Short',
    buy: '📈 Buy',
    sell: '📉 Sell',
  };
  
  return formatted[side.toLowerCase()] || side;
};

/**
 * Format status with badge
 */
export const formatStatus = (status) => {
  if (!status) return 'Unknown';
  
  const statusMap = {
    open: 'Open',
    closed: 'Closed',
    pending: 'Pending',
    cancelled: 'Cancelled',
    running: 'Running',
    stopped: 'Stopped',
  };
  
  return statusMap[status.toLowerCase()] || status;
};

/**
 * Format P&L with color indicator
 */
export const formatPnL = (pnl, withSign = true) => {
  if (pnl == null || isNaN(pnl)) return '$0.00';
  
  const formatted = formatCurrency(Math.abs(pnl));
  const sign = pnl > 0 ? '+' : pnl < 0 ? '-' : '';
  
  return withSign ? `${sign}${formatted}` : formatted;
};

/**
 * Get color class for P&L
 */
export const getPnLColorClass = (pnl) => {
  if (pnl > 0) return 'text-success-400';
  if (pnl < 0) return 'text-danger-400';
  return 'text-gray-400';
};

/**
 * Get color class for percentage change
 */
export const getPercentColorClass = (percent) => {
  if (percent > 0) return 'text-success-400';
  if (percent < 0) return 'text-danger-400';
  return 'text-gray-400';
};

// ===== TEXT FORMATTING =====

/**
 * Truncate text
 */
export const truncate = (text, maxLength = 50) => {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return `${text.substring(0, maxLength)}...`;
};

/**
 * Capitalize first letter
 */
export const capitalize = (text) => {
  if (!text) return '';
  return text.charAt(0).toUpperCase() + text.slice(1).toLowerCase();
};

/**
 * Title case
 */
export const titleCase = (text) => {
  if (!text) return '';
  return text
    .toLowerCase()
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

// ===== VALIDATION =====

/**
 * Check if value is valid number
 */
export const isValidNumber = (value) => {
  return value != null && !isNaN(value) && isFinite(value);
};

/**
 * Check if value is positive
 */
export const isPositive = (value) => {
  return isValidNumber(value) && value > 0;
};

/**
 * Check if value is negative
 */
export const isNegative = (value) => {
  return isValidNumber(value) && value < 0;
};

// ===== EXPORT ALL =====

export default {
  formatCurrency,
  formatPercent,
  formatNumber,
  formatCompactNumber,
  formatCrypto,
  formatDate,
  formatDateTime,
  formatTime,
  formatRelativeTime,
  formatDuration,
  formatSymbol,
  formatSide,
  formatStatus,
  formatPnL,
  getPnLColorClass,
  getPercentColorClass,
  truncate,
  capitalize,
  titleCase,
  isValidNumber,
  isPositive,
  isNegative,
};
