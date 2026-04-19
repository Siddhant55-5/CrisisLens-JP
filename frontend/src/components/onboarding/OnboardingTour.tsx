import { useState, useEffect } from 'react';
import Joyride, { CallBackProps, STATUS } from 'react-joyride';

export default function OnboardingTour() {
  const [run, setRun] = useState(false);

  useEffect(() => {
    const isTourCompleted = localStorage.getItem('cl_tour');
    if (!isTourCompleted) {
      // Delay slightly to let the UI render completely
      const timer = setTimeout(() => {
        setRun(true);
      }, 1500);
      return () => clearTimeout(timer);
    }
  }, []);

  const steps = [
    {
      target: '.gauge-mini',
      content: "This is your Global Risk Score. It combines Banking Instability, Market Crash Risk, and Liquidity Shortage into a single 0–100 index. The range in brackets is the 95% confidence interval.",
      disableBeacon: true,
    },
    {
      target: '.chart-card',
      content: "The shaded zone shows the predicted market direction based on active risk signals. Event pins mark when alerts fired.",
    },
    {
      target: '.chat-toggle-btn',
      content: "Ask the AI Analyst anything — 'Why is banking risk high?', 'What if oil spikes 30%?', or 'Walk me through the 2008 crisis'.",
    }
  ];

  const handleJoyrideCallback = (data: CallBackProps) => {
    const { status } = data;
    const finishedStatuses: string[] = [STATUS.FINISHED, STATUS.SKIPPED];

    if (finishedStatuses.includes(status)) {
      setRun(false);
      localStorage.setItem('cl_tour', 'completed');
    }
  };

  return (
    <Joyride
      steps={steps}
      run={run}
      continuous
      scrollToFirstStep
      showProgress
      showSkipButton
      callback={handleJoyrideCallback}
      styles={{
        options: {
          zIndex: 10000,
          primaryColor: '#22c55e',
          backgroundColor: '#0d1520',
          textColor: '#f1f5f9',
          arrowColor: '#0d1520',
        },
        tooltipContainer: {
          border: '1px solid #1e2e42',
          borderRadius: '8px',
          textAlign: 'left'
        },
        buttonNext: {
          backgroundColor: '#22c55e',
          color: '#000',
          fontWeight: 600,
        },
        buttonSkip: {
          color: '#94a3b8'
        }
      }}
    />
  );
}
