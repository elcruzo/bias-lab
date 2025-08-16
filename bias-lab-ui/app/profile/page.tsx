'use client';

import { ArrowLeft, Github, Linkedin, Mail, Code, Brain, Trophy, ExternalLink } from 'lucide-react';
import Link from 'next/link';

export default function ProfilePage() {
  return (
    <>
      <style jsx global>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
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
            gap: '1rem'
          }}>
            <Link href="/" style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.5rem',
              backgroundColor: 'transparent',
              border: '1px solid #e5e7eb',
              borderRadius: '0.5rem',
              color: '#6b7280',
              textDecoration: 'none',
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
              <ArrowLeft style={{ height: '1rem', width: '1rem' }} />
              Back to Dashboard
            </Link>
            
            <div style={{
              height: '1.5rem',
              width: '1px',
              backgroundColor: '#e5e7eb'
            }} />
            
            <h1 style={{ 
              fontSize: '1.25rem', 
              fontWeight: 'bold', 
              margin: 0,
              color: '#1f2937'
            }}>
              Developer Profile
            </h1>
          </div>
        </header>

        {/* Main Content */}
        <main style={{
          maxWidth: '800px',
          margin: '0 auto',
          padding: '3rem 1.5rem'
        }}>
          {/* Profile Header */}
          <div style={{
            textAlign: 'center',
            marginBottom: '3rem',
            animation: 'fadeIn 0.6s ease-out'
          }}>
            <div style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '6rem',
              height: '6rem',
              backgroundColor: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
              borderRadius: '50%',
              marginBottom: '1.5rem',
              position: 'relative'
            }}>
              <div style={{
                position: 'absolute',
                inset: 0,
                background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                borderRadius: '50%',
                filter: 'blur(8px)',
                opacity: 0.3
              }} />
              <div style={{
                position: 'relative',
                padding: '1rem',
                // background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                borderRadius: '50%'
              }}>
                <Brain style={{ height: '2rem', width: '2rem', color: 'white' }} />
              </div>
            </div>
            
            <h1 style={{
              fontSize: '2.5rem',
              fontWeight: 'bold',
              margin: '0 0 0.5rem 0',
              background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text'
            }}>
              Ayomide Caleb Adekoya
            </h1>
            
            <p style={{
              fontSize: '1.25rem',
              color: '#6b7280',
              margin: '0 0 1rem 0'
            }}>
              AI Engineer & Full-Stack Developer
            </p>
            
            <p style={{
              fontSize: '1rem',
              color: '#374151',
              lineHeight: '1.6',
              maxWidth: '600px',
              margin: '0 auto'
            }}>
              building AI systems that work. from ml to fullstack, product to infra.
            </p>
          </div>

          {/* Skills & Technologies */}
          <div style={{
            backgroundColor: '#f8fafc',
            borderRadius: '1rem',
            padding: '2rem',
            marginBottom: '2rem',
            animation: 'fadeIn 0.6s ease-out 0.2s both'
          }}>
            <h2 style={{
              fontSize: '1.5rem',
              fontWeight: '600',
              margin: '0 0 1.5rem 0',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}>
              <Code style={{ height: '1.5rem', width: '1.5rem', color: '#3b82f6' }} />
              Technologies Used
            </h2>
            
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '1rem'
            }}>
              {[
                { category: 'Frontend', skills: ['Next.js 15', 'React', 'TypeScript', 'Tailwind CSS'] },
                { category: 'Backend', skills: ['FastAPI', 'Python', 'OpenAI GPT-3.5', 'NewsAPI'] },
                { category: 'AI/ML', skills: ['Transformers', 'spaCy', 'D3.js', 'Sentence Embeddings'] }
              ].map((tech, idx) => (
                <div key={idx} style={{
                  backgroundColor: 'white',
                  borderRadius: '0.75rem',
                  padding: '1.5rem',
                  border: '1px solid #e2e8f0'
                }}>
                  <h3 style={{
                    fontSize: '1rem',
                    fontWeight: '600',
                    margin: '0 0 0.75rem 0',
                    color: '#374151'
                  }}>
                    {tech.category}
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {tech.skills.map((skill, sidx) => (
                      <span key={sidx} style={{
                        fontSize: '0.875rem',
                        color: '#6b7280',
                        padding: '0.25rem 0.5rem',
                        backgroundColor: '#f1f5f9',
                        borderRadius: '0.375rem',
                        display: 'inline-block'
                      }}>
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Project Highlights */}
          <div style={{
            backgroundColor: '#f8fafc',
            borderRadius: '1rem',
            padding: '2rem',
            marginBottom: '2rem',
            animation: 'fadeIn 0.6s ease-out 0.4s both'
          }}>
            <h2 style={{
              fontSize: '1.5rem',
              fontWeight: '600',
              margin: '0 0 1.5rem 0',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}>
              <Trophy style={{ height: '1.5rem', width: '1.5rem', color: '#f59e0b' }} />
              Project Highlights
            </h2>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {[
                {
                  title: 'AI-Powered Bias Detection',
                  description: 'Implemented ensemble scoring combining LLM analysis with heuristic methods for comprehensive bias detection.'
                },
                {
                  title: 'Contrastive Framing Attribution',
                  description: 'Built CFA engine to identify specific phrases that contribute to media bias using advanced NLP techniques.'
                },
                {
                  title: 'Real-time News Analysis',
                  description: 'Created automated pipeline fetching and analyzing news from multiple sources with 99% uptime.'
                },
                {
                  title: 'Interactive Visualizations',
                  description: 'Developed D3.js network graphs and bias distribution charts for intuitive data exploration.'
                }
              ].map((highlight, idx) => (
                <div key={idx} style={{
                  backgroundColor: 'white',
                  borderRadius: '0.75rem',
                  padding: '1.5rem',
                  border: '1px solid #e2e8f0'
                }}>
                  <h3 style={{
                    fontSize: '1.125rem',
                    fontWeight: '600',
                    margin: '0 0 0.5rem 0',
                    color: '#374151'
                  }}>
                    {highlight.title}
                  </h3>
                  <p style={{
                    fontSize: '0.875rem',
                    color: '#6b7280',
                    margin: 0,
                    lineHeight: '1.5'
                  }}>
                    {highlight.description}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Contact & Links */}
          <div style={{
            backgroundColor: '#f8fafc',
            borderRadius: '1rem',
            padding: '2rem',
            textAlign: 'center',
            animation: 'fadeIn 0.6s ease-out 0.6s both'
          }}>
            <h2 style={{
              fontSize: '1.5rem',
              fontWeight: '600',
              margin: '0 0 1.5rem 0'
            }}>
              Get In Touch
            </h2>
            
            <p style={{
              fontSize: '0.875rem',
              color: '#6b7280',
              margin: '0 0 1.5rem 0'
            }}>
              Interested in ML/AI, Fullstack, or want to collaborate? Let&apos;s connect!
            </p>
            
            <div style={{
              display: 'flex',
              gap: '1rem',
              justifyContent: 'center',
              flexWrap: 'wrap'
            }}>
              {[
                { icon: Github, label: 'GitHub', href: 'https://github.com/elcruzo', color: '#374151' },
                { icon: Linkedin, label: 'LinkedIn', href: 'https://www.linkedin.com/in/elcruzo', color: '#0077b5' },
                { icon: Mail, label: 'Email', href: 'mailto:ayomideadekoya266@gmail.com', color: '#dc2626' }
              ].map((link, idx) => (
                <a
                  key={idx}
                  href={link.href}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    padding: '0.75rem 1.5rem',
                    backgroundColor: 'white',
                    border: '1px solid #e2e8f0',
                    borderRadius: '0.75rem',
                    color: link.color,
                    textDecoration: 'none',
                    fontSize: '0.875rem',
                    fontWeight: '500',
                    transition: 'all 0.2s'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = link.color;
                    e.currentTarget.style.boxShadow = `0 4px 12px ${link.color}20`;
                    e.currentTarget.style.transform = 'translateY(-2px)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = '#e2e8f0';
                    e.currentTarget.style.boxShadow = 'none';
                    e.currentTarget.style.transform = 'translateY(0)';
                  }}
                >
                  <link.icon style={{ height: '1rem', width: '1rem' }} />
                  {link.label}
                  <ExternalLink style={{ height: '0.75rem', width: '0.75rem' }} />
                </a>
              ))}
            </div>
          </div>
        </main>
      </div>
    </>
  );
}
