import { createApp } from 'vue'
import App from './App.vue'
import './style.css'

// Register service worker for PWA
/*
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js', { scope: '/' }).then(registration => {
      console.log('SW registered: ', registration);
    }).catch(registrationError => {
      console.log('SW registration failed: ', registrationError);
    });
  });
}
*/

// Create Vue app
const app = createApp(App)

// Global error handler for mobile debugging
app.config.errorHandler = (err, instance, info) => {
  console.error('Vue error:', err, info)
  // In production, you might want to send errors to a service
}

// Mount app
app.mount('#app') 