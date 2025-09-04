import { render, screen } from '@testing-library/react';
import App from './App';

test('renders PL8WRDS game title', () => {
  render(<App />);
  const titleElement = screen.getByText(/PL8WRDS/i);
  expect(titleElement).toBeInTheDocument();
});
