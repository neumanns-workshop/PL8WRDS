// FloatingScore component - Shows animated +points when scoring
import React, { useEffect, useState } from 'react';

interface FloatingScoreProps {
  points: number;
  isVisible: boolean;
  onAnimationComplete: () => void;
}

export const FloatingScore: React.FC<FloatingScoreProps> = ({
  points,
  isVisible,
  onAnimationComplete,
}) => {
  const [shouldRender, setShouldRender] = useState(false);

  useEffect(() => {
    if (isVisible) {
      setShouldRender(true);
      // Clean up after animation completes
      const timer = setTimeout(() => {
        setShouldRender(false);
        onAnimationComplete();
      }, 2000); // Match animation duration

      return () => clearTimeout(timer);
    }
  }, [isVisible, onAnimationComplete]);

  if (!shouldRender || points <= 0) return null;

  return (
    <div className={`floating-score ${isVisible ? 'animate' : ''}`}>
      +{Math.round(points * 10)}
    </div>
  );
};

export default FloatingScore;
