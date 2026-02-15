import { Spin } from 'antd';
import React, { Suspense } from 'react';

interface LoadingFallbackProps {
  tip?: string;
}

const LoadingFallback: React.FC<LoadingFallbackProps> = ({ tip = '加载中...' }) => {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '400px',
      width: '100%'
    }}>
      <Spin size="large" tip={tip} />
    </div>
  );
};

interface LazyLoadProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export const LazyLoad: React.FC<LazyLoadProps> = ({ children, fallback }) => {
  return (
    <Suspense fallback={fallback || <LoadingFallback />}>
      {children}
    </Suspense>
  );
};

export default LoadingFallback;

