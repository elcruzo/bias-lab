'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Search, Brain, BarChart3, FileText, Network, 
  RefreshCw, Grid, List, TrendingUp, AlertTriangle,
  Settings, Eye, X, ExternalLink, Star,
  ChevronRight, Activity, User
} from 'lucide-react';
import BiasDistributionChart from '@/components/BiasDistributionChart';
import NarrativeNetwork from '@/components/NarrativeNetwork';
import CFAVisualization from '@/components/CFAVisualization';

// Types
interface Article {
  article_id: string | number;
  title: string;
  source: string;
  url: string;
  published_at?: string;
  scores: {
    ideological_stance: number;
    factual_grounding: number;
    framing_choices: number;
    emotional_tone: number;
    source_transparency: number;
  };
  confidence_interval?: {
    confidence: number;
    lower: number;
    upper: number;
  };
  stale?: boolean;
  full_text?: string;
  description?: string;
}

interface ArticleDetail extends Article {
  cfa_analysis?: {
    contributions?: Array<{
      span: string;
      dimension: string;
      delta: number;
      confidence?: number;
    }>;
    base_scores?: Record<string, number>;
    neutral_scores?: Record<string, number>;
  };
  transparency_analysis?: Record<string, unknown>;
}

interface Narrative {
  cluster_id: number;
  descriptor: string;
  article_ids: string[];
  sources: string[];
  polarity: {
    mean_ideology: number;
    std_ideology: number;
    lean: string;
    consensus: string;
    size: number;
  };
  mean_framing_score: number;
}

interface HealthMetrics {
  status: string;
  uptime_seconds: number;
  metrics: {
    requests_total: number;
    avg_latency_ms: number;
  };
}

export default function Dashboard() {
  // State
  const [articles, setArticles] = useState<Article[]>([]);
  const [narratives, setNarratives] = useState<Narrative[]>([]);
  const [health, setHealth] = useState<HealthMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedArticle, setSelectedArticle] = useState<ArticleDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  // Fetch data from backend
  const fetchData = useCallback(async () => {
    if (!API_URL) {
      setError('Backend API URL not configured. Please check your environment variables.');
      return;
    }

    setLoading(true);
    setError(null);
    
    try {
      const [articlesRes, narrativesRes, healthRes] = await Promise.all([
        fetch(`${API_URL}/articles`),
        fetch(`${API_URL}/narratives`),
        fetch(`${API_URL}/health`)
      ]);

      if (articlesRes.ok) {
      const articlesData = await articlesRes.json();
      setArticles(articlesData);
      }

      if (narrativesRes.ok) {
        const narrativesData = await narrativesRes.json();
      setNarratives(narrativesData);
      }

      if (healthRes.ok) {
        const healthData = await healthRes.json();
      setHealth(healthData);
      }

    } catch (err) {
      console.error('Backend connection failed:', err);
      setError(`Backend connection failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  }, [API_URL]);

  // Debounced fetch data to prevent multiple rapid calls
  const debouncedFetchData = useCallback(() => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }
    
    debounceRef.current = setTimeout(() => {
      fetchData();
    }, 300); // 300ms debounce
  }, [fetchData]);

  // Fetch article details
  const fetchArticleDetail = async (articleId: string | number) => {
    if (!API_URL) {
      setError('Backend API URL not configured.');
      return;
    }

    setLoadingDetail(true);
    try {
      const response = await fetch(`${API_URL}/articles/${articleId}`);
      if (response.ok) {
        const data: ArticleDetail = await response.json();
        setSelectedArticle(data);
      } else {
        throw new Error('Failed to fetch article details');
      }
    } catch (err) {
      console.error('Failed to fetch article detail:', err);
      setError('Failed to load article details');
    } finally {
      setLoadingDetail(false);
    }
  };

  // Handle article click
  const handleArticleClick = (article: Article) => {
    if (loadingDetail) return; // Prevent multiple clicks while loading
    
    console.log('Article clicked:', article.title);
    console.log('Article ID being sent:', article.article_id, typeof article.article_id);
    
    // Show modal immediately with basic article info
    setSelectedArticle({
      ...article,
      full_text: '',
      cfa_analysis: null
    });
    
    // Then fetch the detailed data
    fetchArticleDetail(article.article_id);
  };

    // Search function
  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    if (!API_URL) {
      setError('Backend API URL not configured.');
      return;
    }

    setSearching(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_URL}/search?query=${encodeURIComponent(searchQuery)}&max_articles=20`, {
        method: 'POST'
      });
      
      if (response.ok) {
        // After search, fetch updated data
        setTimeout(() => debouncedFetchData(), 2000); // Give backend time to process
      } else {
        throw new Error(`Search failed: ${response.status}`);
      }
    } catch (err) {
      setError(`Search failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setSearching(false);
    }
  };

  // Load data on mount
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, []);

  // Get bias score color
  const getScoreColor = (score: number) => {
    if (score < 30) return '#10b981'; // green
    if (score < 60) return '#f59e0b'; // yellow
    return '#ef4444'; // red
  };

  // Get score description
  const getScoreDescription = (score: number) => {
    if (score < 30) return 'Low bias';
    if (score < 60) return 'Moderate bias';
    return 'High bias';
  };

  return (
    <>
      <style jsx global>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
        @keyframes shimmer {
          0% { background-position: -200px 0; }
          100% { background-position: calc(200px + 100%) 0; }
        }
        .shimmer {
          background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
          background-size: 200px 100%;
          animation: shimmer 1.5s infinite;
        }
        .modal-scroll::-webkit-scrollbar {
          width: 8px;
        }
        .modal-scroll::-webkit-scrollbar-track {
          background: #f1f5f9;
          border-radius: 10px;
          margin: 10px 0;
        }
        .modal-scroll::-webkit-scrollbar-thumb {
          background: #cbd5e1;
          border-radius: 10px;
          border: 2px solid #f1f5f9;
        }
        .modal-scroll::-webkit-scrollbar-thumb:hover {
          background: #94a3b8;
        }
      `}</style>
      

      <div style={{ 
        minHeight: '100vh', 
        backgroundColor: 'white', 
        color: '#1f2937',
        fontFamily: '-apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", "Roboto", sans-serif'
      }}>
      {/* Header */}
      <header style={{
        borderBottom: '1px solid #e5e7eb',
        backgroundColor: 'rgba(249, 250, 251, 0.95)',
        backdropFilter: 'blur(12px)',
        padding: '1rem 0',
        position: 'sticky',
        top: 0,
        zIndex: 50
      }}>
        <div style={{
          maxWidth: '1200px',
          margin: '0 auto',
          padding: '0 1.5rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{ position: 'relative' }}>
              <div style={{
                position: 'absolute',
                inset: 0,
                background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                borderRadius: '0.5rem',
                filter: 'blur(4px)',
                opacity: 0.3
              }} />
              <div style={{
                position: 'relative',
                padding: '0.5rem',
                background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                borderRadius: '0.5rem'
              }}>
                <Brain style={{ height: '1.5rem', width: '1.5rem', color: 'white' }} />
              </div>
              </div>
              <div>
              <h1 style={{ fontSize: '1.25rem', fontWeight: 'bold', margin: 0 }}>Bias Lab</h1>
              <p style={{ fontSize: '0.875rem', color: '#6b7280', margin: 0 }}>AI-Powered Media Analysis</p>
              </div>
            </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            {health && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem' }}>
                <div style={{ 
                  height: '0.5rem', 
                  width: '0.5rem', 
                  backgroundColor: '#10b981', 
                  borderRadius: '50%',
                  animation: 'pulse 2s infinite'
                }} />
                <span style={{ color: '#10b981', fontWeight: '500' }}>
                  Active ({Math.round(health.metrics?.avg_latency_ms || 0)}ms)
                </span>
              </div>
            )}
            
              <button
              onClick={() => {
                window.location.href = '/profile';
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.5rem',
                backgroundColor: 'transparent',
                border: '1px solid #e5e7eb',
                borderRadius: '0.5rem',
                color: '#6b7280',
                cursor: 'pointer',
                fontSize: '0.875rem',
                fontWeight: '500',
                transition: 'all 0.2s'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#f9fafb';
                e.currentTarget.style.borderColor = '#3b82f6';
                e.currentTarget.style.color = '#3b82f6';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'transparent';
                e.currentTarget.style.borderColor = '#e5e7eb';
                e.currentTarget.style.color = '#6b7280';
              }}
            >
              <User style={{ height: '1rem', width: '1rem' }} />
              Profile
              </button>
            
              <button
              onClick={debouncedFetchData}
              disabled={loading}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.5rem 1rem',
                backgroundColor: loading ? '#f3f4f6' : '#3b82f6',
                border: 'none',
                borderRadius: '0.5rem',
                color: loading ? '#9ca3af' : 'white',
                cursor: loading ? 'not-allowed' : 'pointer',
                fontSize: '0.875rem',
                fontWeight: '500',
                transition: 'all 0.2s'
              }}
            >
              <RefreshCw style={{ 
                height: '1rem', 
                width: '1rem',
                animation: loading ? 'spin 1s linear infinite' : 'none'
              }} />
              {loading ? 'Loading...' : 'Refresh'}
              </button>
          </div>
        </div>
      </header>

            {/* Search Section */}
      <section style={{
        borderBottom: '1px solid #e5e7eb',
        backgroundColor: 'linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)',
        padding: '1.5rem 0'
      }}>
        <div style={{
          maxWidth: '1200px',
          margin: '0 auto',
          padding: '0 1.5rem'
        }}>
          <div style={{ marginBottom: '1rem' }}>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', margin: '0 0 0.5rem 0' }}>
              Analyze Media Bias
                  </h2>
            <p style={{ color: '#6b7280', margin: 0 }}>
              Search any topic to get AI-powered bias analysis across multiple news sources
                  </p>
                </div>
                
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            {/* Search Bar - Full Width */}
            <div style={{ position: 'relative', width: '100%' }}>
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Enter any topic: 'Trump tariffs', 'TikTok ban', 'Climate change', 'AI regulation'..."
                      disabled={searching}
                style={{
                  width: '100%',
                  padding: '0.875rem 3rem 0.875rem 1rem',
                  backgroundColor: 'white',
                  border: '2px solid #e5e7eb',
                  borderRadius: '0.75rem',
                  color: '#374151',
                  fontSize: '1rem',
                  outline: 'none',
                  transition: 'all 0.2s',
                  boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
                  boxSizing: 'border-box'
                }}
                onFocus={(e) => {
                  e.target.style.borderColor = '#3b82f6';
                  e.target.style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.1)';
                }}
                onBlur={(e) => {
                  e.target.style.borderColor = '#e5e7eb';
                  e.target.style.boxShadow = '0 1px 3px rgba(0, 0, 0, 0.1)';
                }}
                    />
                    <button
                onClick={handleSearch}
                disabled={searching || !searchQuery.trim()}
                style={{
                  position: 'absolute',
                  right: '0.5rem',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  padding: '0.5rem',
                  backgroundColor: searching ? '#f3f4f6' : '#3b82f6',
                  border: 'none',
                  borderRadius: '0.5rem',
                  color: 'white',
                  cursor: searching ? 'not-allowed' : 'pointer',
                  transition: 'all 0.2s'
                }}
                    >
                      {searching ? (
                  <div style={{
                    width: '1.25rem',
                    height: '1.25rem',
                    border: '2px solid white',
                    borderTop: '2px solid transparent',
                    borderRadius: '50%',
                    animation: 'spin 1s linear infinite'
                  }} />
                ) : (
                  <Search style={{ height: '1.25rem', width: '1.25rem' }} />
                      )}
                    </button>
                  </div>
                  
            {/* Quick Search Buttons - Below Search Bar */}
            <div style={{ 
              display: 'flex', 
              gap: '0.75rem', 
              flexWrap: 'wrap', 
              justifyContent: 'center',
              alignItems: 'center'
            }}>
              <span style={{
                fontSize: '0.875rem',
                color: '#6b7280',
                fontWeight: '500',
                marginRight: '0.5rem'
              }}>
                Quick searches:
              </span>
              {['Trump tariffs', 'TikTok ban', 'Climate change', 'AI regulation'].map((suggestion) => (
                      <button
                        key={suggestion}
                        onClick={() => {
                          setSearchQuery(suggestion);
                    setTimeout(() => handleSearch(), 100);
                        }}
                        disabled={searching}
                  style={{
                    padding: '0.5rem 1rem',
                    backgroundColor: searching ? '#f3f4f6' : 'white',
                    border: '1px solid #d1d5db',
                    borderRadius: '1.5rem',
                    color: searching ? '#9ca3af' : '#374151',
                    cursor: searching ? 'not-allowed' : 'pointer',
                    fontSize: '0.875rem',
                    fontWeight: '500',
                    whiteSpace: 'nowrap',
                    transition: 'all 0.2s',
                    boxShadow: searching ? 'none' : '0 1px 3px rgba(0, 0, 0, 0.1)',
                    transform: searching ? 'none' : 'translateY(0)',
                  }}
                  onMouseEnter={(e) => {
                    if (!searching) {
                      e.currentTarget.style.backgroundColor = '#f8fafc';
                      e.currentTarget.style.borderColor = '#3b82f6';
                      e.currentTarget.style.transform = 'translateY(-1px)';
                      e.currentTarget.style.boxShadow = '0 4px 12px rgba(59, 130, 246, 0.15)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!searching) {
                      e.currentTarget.style.backgroundColor = 'white';
                      e.currentTarget.style.borderColor = '#d1d5db';
                      e.currentTarget.style.transform = 'translateY(0)';
                      e.currentTarget.style.boxShadow = '0 1px 3px rgba(0, 0, 0, 0.1)';
                    }
                  }}
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </section>

      {/* Error Display */}
      <AnimatePresence>
        {error && (
                  <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            style={{
              margin: '1rem 1.5rem 0',
              maxWidth: '1200px',
              marginLeft: 'auto',
              marginRight: 'auto',
              padding: '1rem',
              backgroundColor: '#fef2f2',
              border: '1px solid #fecaca',
              borderRadius: '0.5rem'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <AlertTriangle style={{ height: '1.25rem', width: '1.25rem', color: '#ef4444' }} />
                <span style={{ color: '#dc2626', fontWeight: '500' }}>{error}</span>
                      </div>
              <button 
                onClick={() => setError(null)}
                style={{ background: 'none', border: 'none', color: '#dc2626', cursor: 'pointer', padding: '0.25rem' }}
              >
                <X style={{ height: '1rem', width: '1rem' }} />
              </button>
                    </div>
                  </motion.div>
                )}
      </AnimatePresence>

      {/* Main Dashboard */}
      <main style={{
        maxWidth: '1200px',
        margin: '0 auto',
        padding: '2rem 1.5rem',
        display: loading ? 'flex' : 'grid',
        gridTemplateColumns: loading ? '1fr' : '320px 1fr',
        gap: '2rem',
        alignItems: loading ? 'center' : 'flex-start',
        justifyContent: loading ? 'center' : 'normal',
        minHeight: loading ? '24rem' : 'auto'
      }}>
        {loading ? (
          <div style={{ textAlign: 'center' }}>
            <div style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '5rem',
              height: '5rem',
              backgroundColor: '#f3f4f6',
              borderRadius: '50%',
              marginBottom: '1rem'
            }}>
              <Brain style={{ 
                height: '2.5rem', 
                width: '2.5rem', 
                color: '#3b82f6',
                animation: 'spin 1s linear infinite'
              }} />
                      </div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: '600', margin: '0 0 0.5rem 0' }}>
              Loading Analysis
            </h3>
            <p style={{ color: '#6b7280', margin: 0 }}>Connecting to AI backend...</p>
                    </div>
        ) : (
          <>
            {/* Left Sidebar */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              {/* Stats */}
              <div style={{
                backgroundColor: 'white',
                border: '1px solid #e5e7eb',
                borderRadius: '1rem',
                padding: '1.5rem',
                boxShadow: '0 4px 6px rgba(0, 0, 0, 0.05)'
              }}>
                <h3 style={{
                  margin: '0 0 1.5rem 0',
                  fontSize: '1.125rem',
                  fontWeight: '600',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}>
                  <BarChart3 style={{ height: '1.25rem', width: '1.25rem', color: '#3b82f6' }} />
                  Analysis Overview
                </h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  {[
                    { label: 'Articles', value: articles.length, icon: FileText, color: '#3b82f6' },
                    { label: 'Sources', value: new Set(articles.map(a => a.source)).size, icon: Network, color: '#10b981' },
                    { label: 'Narratives', value: narratives.length, icon: Activity, color: '#8b5cf6' },
                    { label: 'AI Scored', value: articles.filter(a => !a.stale).length, icon: Star, color: '#f59e0b' }
                  ].map((stat, idx) => (
                    <div key={idx} style={{
                      backgroundColor: '#f8fafc',
                      borderRadius: '0.75rem',
                      padding: '1rem',
                      textAlign: 'center'
                    }}>
                      <stat.icon style={{ 
                        height: '1.5rem', 
                        width: '1.5rem', 
                        color: stat.color,
                        margin: '0 auto 0.5rem'
                      }} />
                      <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#1f2937' }}>
                        {stat.value}
              </div>
                      <div style={{ fontSize: '0.75rem', color: '#6b7280', fontWeight: '500' }}>
                        {stat.label}
                  </div>
                  </div>
                  ))}
                </div>
              </div>

              {/* Controls */}
              <div style={{
                backgroundColor: 'white',
                border: '1px solid #e5e7eb',
                borderRadius: '1rem',
                padding: '1.5rem',
                boxShadow: '0 4px 6px rgba(0, 0, 0, 0.05)'
              }}>
                <h3 style={{
                  margin: '0 0 1rem 0',
                  fontSize: '1.125rem',
                  fontWeight: '600',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}>
                  <Settings style={{ height: '1.25rem', width: '1.25rem', color: '#8b5cf6' }} />
                  View Options
                </h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  <div>
                    <label style={{ fontSize: '0.875rem', color: '#6b7280', fontWeight: '500', display: 'block', marginBottom: '0.5rem' }}>
                      Layout
                    </label>
                    <div style={{
                      display: 'flex',
                      backgroundColor: '#f3f4f6',
                      borderRadius: '0.5rem',
                      padding: '0.25rem'
                    }}>
                      {[
                        { mode: 'grid', icon: Grid, label: 'Grid' },
                        { mode: 'list', icon: List, label: 'List' }
                      ].map(({ mode, icon: Icon, label }) => (
                        <button
                          key={mode}
                          onClick={() => setViewMode(mode as 'grid' | 'list')}
                          style={{
                            flex: 1,
                            padding: '0.5rem',
                            backgroundColor: viewMode === mode ? '#3b82f6' : 'transparent',
                            border: 'none',
                            borderRadius: '0.25rem',
                            color: viewMode === mode ? 'white' : '#6b7280',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: '0.5rem',
                            fontSize: '0.875rem',
                            fontWeight: '500',
                            transition: 'all 0.2s'
                          }}
                        >
                          <Icon style={{ height: '1rem', width: '1rem' }} />
                          {label}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div>
                    <label style={{ fontSize: '0.875rem', color: '#6b7280', fontWeight: '500', display: 'block', marginBottom: '0.5rem' }}>
                      Advanced Features
                    </label>
                    <button
                      onClick={() => {
                        const newState = !showAdvanced;
                        setShowAdvanced(newState);
                        if (newState) {
                          fetchData();
                        }
                      }}
                      style={{
                        width: '100%',
                        padding: '0.75rem',
                        backgroundColor: showAdvanced ? '#3b82f6' : '#f3f4f6',
                        border: 'none',
                        borderRadius: '0.5rem',
                        color: showAdvanced ? 'white' : '#374151',
                        cursor: 'pointer',
                        fontSize: '0.875rem',
                        fontWeight: '500',
                        transition: 'all 0.2s',
                        position: 'relative'
                      }}
                    >
                      {showAdvanced ? 'Hide Advanced Analytics' : 'Show Advanced Analytics'}
                      {!showAdvanced && (
                        <div style={{
                          fontSize: '0.75rem',
                          color: '#6b7280',
                          marginTop: '0.25rem'
                        }}>
                          Charts & Network Graphs
                  </div>
                      )}
                    </button>
                  </div>
                </div>
                </div>

              {/* Narrative Clusters */}
              {narratives.length > 0 && (
                <div style={{
                  backgroundColor: 'white',
                  border: '1px solid #e5e7eb',
                  borderRadius: '1rem',
                  padding: '1.5rem',
                  boxShadow: '0 4px 6px rgba(0, 0, 0, 0.05)'
                }}>
                  <h3 style={{
                    margin: '0 0 1rem 0',
                    fontSize: '1.125rem',
                    fontWeight: '600',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem'
                  }}>
                    <Network style={{ height: '1.25rem', width: '1.25rem', color: '#10b981' }} />
                    Narrative Clusters
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    {narratives.map((narrative, idx) => (
                      <div key={idx} style={{
                        backgroundColor: '#f8fafc',
                        border: '1px solid #e2e8f0',
                        borderRadius: '0.75rem',
                        padding: '1rem'
                      }}>
                        <div style={{ 
                          display: 'flex', 
                          justifyContent: 'space-between', 
                          alignItems: 'center',
                          marginBottom: '0.5rem'
                        }}>
                          <span style={{ fontSize: '0.875rem', fontWeight: '600', color: '#1f2937' }}>
                            Cluster {idx + 1}
                          </span>
                          <span style={{ 
                            fontSize: '0.75rem', 
                            color: '#6b7280',
                            backgroundColor: '#e5e7eb',
                            padding: '0.25rem 0.5rem',
                            borderRadius: '1rem'
                          }}>
                            {narrative.article_ids?.length || 0} articles
                          </span>
                        </div>
                        <p style={{
                          fontSize: '0.75rem',
                          color: '#6b7280',
                          margin: '0 0 0.75rem 0',
                          lineHeight: '1.4',
                          display: '-webkit-box',
                          WebkitLineClamp: 3,
                          WebkitBoxOrient: 'vertical',
                          overflow: 'hidden'
                        }}>
                          {narrative.descriptor}
                        </p>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.25rem' }}>
                          {narrative.sources?.slice(0, 3).map((source, sidx) => (
                            <span key={sidx} style={{
                              fontSize: '0.75rem',
                              backgroundColor: '#dbeafe',
                              color: '#1e40af',
                              padding: '0.25rem 0.5rem',
                              borderRadius: '0.25rem',
                              fontWeight: '500'
                            }}>
                              {source}
                            </span>
                          ))}
                  </div>
                </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Main Content */}
            <div style={{
              backgroundColor: 'white',
              border: '1px solid #e5e7eb',
              borderRadius: '1rem',
              padding: '2rem',
              boxShadow: '0 4px 6px rgba(0, 0, 0, 0.05)'
            }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: '2rem'
              }}>
                <div>
                  <h2 style={{
                    margin: '0 0 0.5rem 0',
                    fontSize: '1.5rem',
                    fontWeight: '700',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem'
                  }}>
                    <FileText style={{ height: '1.5rem', width: '1.5rem', color: '#3b82f6' }} />
                    Analyzed Articles
                  </h2>
                  <p style={{ color: '#6b7280', margin: 0, fontSize: '0.875rem' }}>
                    {articles.length} articles analyzed • Click any article for detailed analysis
                  </p>
                    </div>
                  </div>

              {articles.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '4rem 2rem' }}>
                  <div style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: '4rem',
                    height: '4rem',
                    backgroundColor: '#f3f4f6',
                    borderRadius: '50%',
                    marginBottom: '1.5rem'
                  }}>
                    <Search style={{ height: '2rem', width: '2rem', color: '#9ca3af' }} />
                    </div>
                  <h3 style={{ fontSize: '1.25rem', fontWeight: '600', margin: '0 0 0.5rem 0' }}>
                    No Articles Loaded
                  </h3>
                  <p style={{ color: '#6b7280', marginBottom: '1.5rem' }}>
                    Search for a topic above to begin analysis or check your backend connection.
                  </p>
                  <button
                    onClick={debouncedFetchData}
                    style={{
                      padding: '0.75rem 1.5rem',
                      backgroundColor: '#3b82f6',
                      border: 'none',
                      borderRadius: '0.5rem',
                      color: 'white',
                      cursor: 'pointer',
                      fontSize: '0.875rem',
                      fontWeight: '500'
                    }}
                  >
                    Try Again
                  </button>
                  </div>
              ) : (
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: viewMode === 'grid' ? 'repeat(auto-fit, minmax(350px, 1fr))' : '1fr',
                  gap: '1.5rem'
                }}>
                    {articles.map((article, index) => (
                      <motion.div
                      key={article.article_id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.1 }}
                      onClick={() => handleArticleClick(article)}
                      style={{
                        backgroundColor: '#fafbfc',
                        border: '1px solid #e2e8f0',
                        borderRadius: '1rem',
                        padding: '1.5rem',
                        cursor: 'pointer',
                        transition: 'all 0.2s',
                        position: 'relative',
                        overflow: 'hidden'
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.borderColor = '#3b82f6';
                        e.currentTarget.style.boxShadow = '0 8px 25px rgba(59, 130, 246, 0.15)';
                        e.currentTarget.style.transform = 'translateY(-2px)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.borderColor = '#e2e8f0';
                        e.currentTarget.style.boxShadow = 'none';
                        e.currentTarget.style.transform = 'translateY(0)';
                      }}
                    >
                      {/* Article Header */}
                      <div style={{
                        display: 'flex',
                        alignItems: 'flex-start',
                        justifyContent: 'space-between',
                        marginBottom: '1rem'
                      }}>
                        <div style={{ flex: 1 }}>
                          <h3 style={{
                            fontWeight: '600',
                            margin: '0 0 0.5rem 0',
                            lineHeight: '1.4',
                            fontSize: '1rem',
                            display: '-webkit-box',
                            WebkitLineClamp: 2,
                            WebkitBoxOrient: 'vertical',
                            overflow: 'hidden'
                          }}>
                            {article.title}
                          </h3>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                            <span style={{ 
                              fontSize: '0.875rem', 
                              color: '#3b82f6',
                              fontWeight: '600'
                            }}>
                                {article.source}
                            </span>
                            {article.published_at && (
                              <>
                                <span style={{ color: '#d1d5db' }}>•</span>
                                <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>
                                  {new Date(article.published_at).toLocaleDateString()}
                                </span>
                              </>
                            )}
                          </div>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                              {article.stale && (
                            <span style={{
                              fontSize: '0.75rem',
                              backgroundColor: '#fef3c7',
                              color: '#d97706',
                              padding: '0.25rem 0.5rem',
                              borderRadius: '0.375rem',
                              fontWeight: '500'
                            }}>
                              Heuristic
                            </span>
                          )}
                          <ChevronRight style={{ height: '1rem', width: '1rem', color: '#9ca3af' }} />
                            </div>
                      </div>

                      {/* Bias Scores */}
                      <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(2, 1fr)',
                        gap: '0.75rem',
                        marginBottom: '1rem'
                      }}>
                        {[
                          { label: 'Ideology', value: article.scores.ideological_stance, key: 'ideological_stance' },
                          { label: 'Factual', value: article.scores.factual_grounding, key: 'factual_grounding' },
                          { label: 'Framing', value: article.scores.framing_choices, key: 'framing_choices' },
                          { label: 'Emotion', value: article.scores.emotional_tone, key: 'emotional_tone' }
                        ].map((score, idx) => (
                          <div key={idx} style={{
                            backgroundColor: 'white',
                            borderRadius: '0.5rem',
                            padding: '0.75rem',
                            border: '1px solid #f1f5f9'
                          }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
                              <span style={{ fontSize: '0.75rem', color: '#6b7280', fontWeight: '500' }}>
                                {score.label}
                              </span>
                              <span style={{ 
                                fontSize: '0.875rem',
                                color: getScoreColor(score.value), 
                                fontWeight: '700'
                              }}>
                                {score.value}
                              </span>
                                  </div>
                            <div style={{
                              width: '100%',
                              height: '0.25rem',
                              backgroundColor: '#f1f5f9',
                              borderRadius: '0.125rem',
                              overflow: 'hidden'
                            }}>
                              <div style={{
                                width: `${score.value}%`,
                                height: '100%',
                                backgroundColor: getScoreColor(score.value),
                                borderRadius: '0.125rem',
                                transition: 'width 0.3s ease'
                              }} />
                                  </div>
                                </div>
                              ))}
                            </div>
                            
                      {/* Confidence & Actions */}
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        {article.confidence_interval ? (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                            <Activity style={{ height: '0.875rem', width: '0.875rem', color: '#6b7280' }} />
                            <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>
                              {Math.round(article.confidence_interval.confidence * 100)}% confidence
                            </span>
                                </div>
                        ) : (
                          <div />
                        )}
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.75rem', color: '#3b82f6', fontWeight: '500' }}>
                          <Eye style={{ height: '0.875rem', width: '0.875rem' }} />
                          View Details
                                </div>
                              </div>
                      </motion.div>
                    ))}
              </div>
            )}

              {/* Advanced Analytics Hint */}
              {!showAdvanced && articles.length > 0 && (
                <div style={{
                  marginTop: '2rem',
                  backgroundColor: '#f8fafc',
                  border: '2px dashed #e2e8f0',
                  borderRadius: '1rem',
                  padding: '2rem',
                  textAlign: 'center'
                }}>
                  <div style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: '3rem',
                    height: '3rem',
                    backgroundColor: '#e2e8f0',
                    borderRadius: '50%',
                    marginBottom: '1rem'
                  }}>
                    <BarChart3 style={{ height: '1.5rem', width: '1.5rem', color: '#6b7280' }} />
                </div>
                  <h3 style={{
                    margin: '0 0 0.5rem 0',
                    fontSize: '1.125rem',
                    fontWeight: '600',
                    color: '#374151'
                  }}>
                    Advanced Analytics Available
                </h3>
                  <p style={{ 
                    color: '#6b7280', 
                    margin: '0 0 1rem 0',
                    lineHeight: '1.5'
                  }}>
                    Click &ldquo;Show Advanced Analytics&rdquo; in the sidebar to view bias distribution charts, narrative network graphs, and detailed CFA visualizations.
                  </p>
                  <button
                    onClick={() => {
                      setShowAdvanced(true);
                      fetchData();
                    }}
                    style={{
                      padding: '0.5rem 1rem',
                      backgroundColor: '#3b82f6',
                      border: 'none',
                      borderRadius: '0.5rem',
                      color: 'white',
                      cursor: 'pointer',
                      fontSize: '0.875rem',
                      fontWeight: '500',
                      transition: 'all 0.2s'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = '#2563eb';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = '#3b82f6';
                    }}
                  >
                    Show Advanced Analytics
                  </button>
              </div>
            )}

              {/* Advanced Visualizations */}
              {showAdvanced && articles.length > 0 && (
                  <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  style={{ marginTop: '2rem' }}
                >
                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(500px, 1fr))',
                    gap: '2rem'
                  }}>
                    {/* Bias Distribution Chart */}
                    <div style={{
                      backgroundColor: '#f8fafc',
                      border: '1px solid #e2e8f0',
                      borderRadius: '1rem',
                      padding: '2rem'
                    }}>
                      <h3 style={{
                        margin: '0 0 1.5rem 0',
                        fontSize: '1.25rem',
                        fontWeight: '600',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem'
                      }}>
                        <BarChart3 style={{ height: '1.25rem', width: '1.25rem', color: '#3b82f6' }} />
                        Bias Distribution
                      </h3>
                      <div style={{ height: '300px' }}>
                        <BiasDistributionChart articles={articles} />
                        </div>
                        </div>
                        
                    {/* Narrative Network */}
                    {narratives.length > 0 && (
                      <div style={{
                        backgroundColor: '#f8fafc',
                        border: '1px solid #e2e8f0',
                        borderRadius: '1rem',
                        padding: '2rem'
                      }}>
                        <h3 style={{
                          margin: '0 0 1.5rem 0',
                          fontSize: '1.25rem',
                          fontWeight: '600',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.5rem'
                        }}>
                          <Network style={{ height: '1.25rem', width: '1.25rem', color: '#10b981' }} />
                          Narrative Network
                        </h3>
                        <div style={{ height: '300px' }}>
                          <NarrativeNetwork narratives={narratives} articles={articles} />
                            </div>
                          </div>
                        )}
                  </div>

                  {/* Sample CFA Analysis */}
                  {selectedArticle?.cfa_analysis && (
                    <div style={{
                      marginTop: '2rem',
                      backgroundColor: '#f8fafc',
                      border: '1px solid #e2e8f0',
                      borderRadius: '1rem',
                      padding: '2rem'
                    }}>
                      <h3 style={{
                        margin: '0 0 1.5rem 0',
                        fontSize: '1.25rem',
                        fontWeight: '600',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem'
                      }}>
                        <TrendingUp style={{ height: '1.25rem', width: '1.25rem', color: '#8b5cf6' }} />
                        Contrastive Framing Analysis
                      </h3>
                      <CFAVisualization data={selectedArticle.cfa_analysis} />
                          </div>
                        )}
                  </motion.div>
              )}
        </div>
          </>
        )}
      </main>

      {/* Article Detail Modal */}
      <AnimatePresence>
      {selectedArticle && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={{
              position: 'fixed',
              inset: 0,
              backgroundColor: 'rgba(0, 0, 0, 0.5)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 100,
              padding: '2rem'
            }}
            onClick={() => setSelectedArticle(null)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              style={{
                backgroundColor: 'white',
                borderRadius: '1.25rem',
                padding: '2rem',
                maxWidth: '50rem',
                maxHeight: '80vh',
                overflowY: 'auto',
                boxShadow: '0 25px 50px rgba(0, 0, 0, 0.25)'
              }}
              className="modal-scroll"
            >
              {loadingDetail ? (
                <div style={{ textAlign: 'center', padding: '2rem' }}>
                  <Brain style={{ 
                    height: '2rem', 
                    width: '2rem', 
                    color: '#3b82f6',
                    animation: 'spin 1s linear infinite',
                    margin: '0 auto 1rem'
                  }} />
                  <p>Loading detailed analysis...</p>
                </div>
              ) : (
                <>
                  {/* Modal Header */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem' }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                        <h2 style={{ fontSize: '1.5rem', fontWeight: '700', margin: 0, lineHeight: '1.3' }}>
                          {selectedArticle.title}
                        </h2>
                        {loadingDetail && (
                          <div style={{
                            width: '20px',
                            height: '20px',
                            border: '2px solid #e5e7eb',
                            borderTop: '2px solid #3b82f6',
                            borderRadius: '50%',
                            animation: 'spin 1s linear infinite',
                            flexShrink: 0
                          }} />
                        )}
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
                        <span style={{ color: '#3b82f6', fontWeight: '600' }}>{selectedArticle.source}</span>
                        <a 
                          href={selectedArticle.url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          style={{ 
                            display: 'flex', 
                            alignItems: 'center', 
                            gap: '0.25rem', 
                            color: '#6b7280', 
                            textDecoration: 'none',
                            fontSize: '0.875rem'
                          }}
                        >
                          <ExternalLink style={{ height: '0.875rem', width: '0.875rem' }} />
                          Read Original
                        </a>
                      </div>
                    </div>
              <button
                      onClick={() => setSelectedArticle(null)}
                      style={{
                        padding: '0.5rem',
                        backgroundColor: '#f3f4f6',
                        border: 'none',
                        borderRadius: '0.5rem',
                        cursor: 'pointer',
                        marginLeft: '1rem'
                      }}
                    >
                      <X style={{ height: '1.25rem', width: '1.25rem', color: '#6b7280' }} />
              </button>
            </div>
            
                  {/* Bias Scores Detail */}
                  <div style={{ marginBottom: '2rem' }}>
                    <h3 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '1rem' }}>Bias Analysis</h3>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
                      {Object.entries(selectedArticle.scores).map(([key, value]) => (
                        <div key={key} style={{
                          backgroundColor: '#f8fafc',
                          borderRadius: '0.75rem',
                          padding: '1rem',
                          border: '1px solid #e2e8f0'
                        }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                            <span style={{ fontSize: '0.875rem', fontWeight: '500', color: '#374151' }}>
                              {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                            </span>
                            <span style={{ 
                              fontSize: '1.25rem',
                              fontWeight: '700',
                              color: getScoreColor(value)
                            }}>
                              {value}
                            </span>
              </div>
                          <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.5rem' }}>
                            {getScoreDescription(value)}
              </div>
                          <div style={{
                            width: '100%',
                            height: '0.5rem',
                            backgroundColor: '#e5e7eb',
                            borderRadius: '0.25rem',
                            overflow: 'hidden'
                          }}>
                            <div style={{
                              width: `${value}%`,
                              height: '100%',
                              backgroundColor: getScoreColor(value),
                              borderRadius: '0.25rem',
                              transition: 'width 0.5s ease'
                            }} />
              </div>
                  </div>
                      ))}
                </div>
              </div>

                  {/* CFA Analysis */}
                  <div style={{ marginBottom: '2rem' }}>
                    <h3 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '1rem' }}>
                      Contrastive Framing Attribution
                    </h3>
                    {loadingDetail ? (
                      // Loading shimmer for CFA
              <div>
                        <div className="shimmer" style={{ 
                          height: '1rem', 
                          borderRadius: '0.25rem', 
                          marginBottom: '1rem',
                          width: '80%' 
                        }} />
                        {[1, 2, 3].map(i => (
                          <div key={i} style={{
                            backgroundColor: '#f8fafc',
                            border: '1px solid #e2e8f0',
                            borderRadius: '0.5rem',
                            padding: '1rem',
                            marginBottom: '0.75rem'
                          }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                              <div className="shimmer" style={{ height: '0.75rem', width: '30%', borderRadius: '0.25rem' }} />
                              <div className="shimmer" style={{ height: '0.75rem', width: '20%', borderRadius: '0.25rem' }} />
              </div>
                            <div className="shimmer" style={{ height: '1rem', width: '90%', borderRadius: '0.25rem' }} />
                  </div>
                        ))}
                </div>
                    ) : selectedArticle.cfa_analysis?.contributions && selectedArticle.cfa_analysis.contributions.length > 0 ? (
                      <div>
                        <p style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '1rem' }}>
                          Key phrases that contribute to bias in this article:
                        </p>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                          {selectedArticle.cfa_analysis.contributions.slice(0, 5).map((contrib, idx) => (
                            <div key={idx} style={{
                              backgroundColor: '#f8fafc',
                              border: '1px solid #e2e8f0',
                              borderRadius: '0.5rem',
                              padding: '1rem'
                            }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                                <span style={{ 
                                  fontSize: '0.75rem', 
                                  fontWeight: '500',
                                  color: '#6b7280',
                                  textTransform: 'uppercase',
                                  letterSpacing: '0.05em'
                                }}>
                                  {contrib.dimension.replace(/_/g, ' ')}
                                </span>
                                <span style={{ 
                                  fontSize: '0.875rem',
                                  fontWeight: '600',
                                  color: contrib.delta > 0 ? '#ef4444' : '#10b981'
                                }}>
                                  {contrib.delta > 0 ? '+' : ''}{contrib.delta.toFixed(1)}
                                </span>
              </div>
                              <p style={{
                                fontSize: '0.875rem',
                                color: '#374151',
                                margin: 0,
                                fontStyle: 'italic',
                                lineHeight: '1.4'
                              }}>
                                &ldquo;{contrib.span}&rdquo;
                </p>
              </div>
                          ))}
            </div>
          </div>
                    ) : (
                      <p style={{ fontSize: '0.875rem', color: '#6b7280', fontStyle: 'italic' }}>
                        No bias analysis available for this article.
                      </p>
                    )}
                  </div>

                  {/* Full Article Text */}
                  <div style={{ marginBottom: '2rem' }}>
                    <h3 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '1rem' }}>
                      Full Article Text
                    </h3>
                    {loadingDetail ? (
                      // Loading shimmer for full text
                      <div>
                        {[1, 2, 3, 4, 5, 6, 7, 8].map(i => (
                          <div key={i} className="shimmer" style={{ 
                            height: '1rem', 
                            borderRadius: '0.25rem', 
                            marginBottom: '0.75rem',
                            width: i === 8 ? '60%' : '100%'
                          }} />
                        ))}
            </div>
                    ) : selectedArticle.full_text ? (
                      <div style={{
                        backgroundColor: '#f8fafc',
                        border: '1px solid #e2e8f0',
                        borderRadius: '0.75rem',
                        padding: '1.5rem',
                        maxHeight: '400px',
                        overflowY: 'auto'
                      }}>
                        <p style={{ 
                          color: '#374151', 
                          lineHeight: '1.7', 
                          margin: 0,
                          fontSize: '0.925rem'
                        }}>
                          {selectedArticle.full_text}
                        </p>
          </div>
                    ) : (
                      <p style={{ fontSize: '0.875rem', color: '#6b7280', fontStyle: 'italic' }}>
                        Full article text not available.
                      </p>
                    )}
        </div>

                  {/* Article Description */}
                  {selectedArticle.description && (
                    <div>
                      <h3 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '1rem' }}>Summary</h3>
                      <p style={{ color: '#6b7280', lineHeight: '1.6', margin: 0 }}>
                        {selectedArticle.description}
                      </p>
    </div>
                  )}
                </>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
          </div>
    </>
  );
}