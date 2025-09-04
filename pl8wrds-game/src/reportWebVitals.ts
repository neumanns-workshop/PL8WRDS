import { ReportHandler } from 'web-vitals';

/**
 * Report web vitals metrics for performance monitoring
 * @param onPerfEntry - Callback function to handle performance entries
 */
const reportWebVitals = (onPerfEntry?: ReportHandler): void => {
  if (onPerfEntry && typeof onPerfEntry === 'function') {
    import('web-vitals').then(({ getCLS, getFID, getFCP, getLCP, getTTFB }) => {
      getCLS(onPerfEntry);
      getFID(onPerfEntry);
      getFCP(onPerfEntry);
      getLCP(onPerfEntry);
      getTTFB(onPerfEntry);
    }).catch((error) => {
      console.warn('Failed to load web-vitals:', error);
    });
  }
};

export default reportWebVitals;
