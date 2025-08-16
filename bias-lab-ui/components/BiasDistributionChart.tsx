'use client';

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface Article {
  scores?: Record<string, number>;
}

interface BiasDistributionChartProps {
  articles: Article[];
}

export default function BiasDistributionChart({ articles }: BiasDistributionChartProps) {
  
  // Calculate bias distribution
  const distribution = {
    'Far Left': 0,
    'Left': 0,
    'Center': 0,
    'Right': 0,
    'Far Right': 0
  };

  articles.forEach(article => {
    const ideologicalScore = article.scores?.ideological_stance || 50;
    if (ideologicalScore < 20) distribution['Far Left']++;
    else if (ideologicalScore < 40) distribution['Left']++;
    else if (ideologicalScore < 60) distribution['Center']++;
    else if (ideologicalScore < 80) distribution['Right']++;
    else distribution['Far Right']++;
  });

  const data = Object.entries(distribution).map(([label, count]) => ({
    name: label,
    count: count,
    percentage: articles.length > 0 ? Math.round((count / articles.length) * 100) : 0
  }));



  const colors = {
    'Far Left': '#10b981',
    'Left': '#34d399',
    'Center': '#94a3b8',
    'Right': '#f87171',
    'Far Right': '#ef4444'
  };

  const CustomTooltip = ({ active, payload }: {
    active?: boolean;
    payload?: Array<{
      value: number;
      payload: {
        name: string;
        percentage: number;
      };
    }>;
  }) => {
    if (active && payload && payload[0]) {
      return (
        <div style={{
          backgroundColor: 'white',
          border: '1px solid #e2e8f0',
          borderRadius: '0.5rem',
          padding: '0.75rem',
          boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)'
        }}>
          <p style={{ fontSize: '0.875rem', fontWeight: '500', color: '#1f2937' }}>
            {payload[0].payload.name}
          </p>
          <p style={{ fontSize: '0.75rem', color: '#6b7280' }}>
            Articles: {payload[0].value} ({payload[0].payload.percentage}%)
          </p>
        </div>
      );
    }
    return null;
  };

  if (!articles.length) {
    return (
      <div style={{ 
        width: '100%', 
        height: '100%', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center', 
        color: '#6b7280' 
      }}>
        <div style={{ textAlign: 'center' }}>
          <p>No articles to analyze</p>
          <p style={{ fontSize: '0.875rem' }}>Load some articles first</p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ width: '100%', height: '100%' }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis 
            dataKey="name" 
            tick={{ fill: '#64748b', fontSize: 12 }}
            axisLine={{ stroke: '#cbd5e1' }}
          />
          <YAxis 
            tick={{ fill: '#64748b', fontSize: 12 }}
            axisLine={{ stroke: '#cbd5e1' }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="count" radius={[8, 8, 0, 0]}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={colors[entry.name as keyof typeof colors]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
