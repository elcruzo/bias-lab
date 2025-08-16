'use client';

import { motion } from 'framer-motion';
import { ArrowUp, ArrowDown, Minus, Info } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';

interface CFAContribution {
  span: string;
  dimension: string;
  delta: number;
  confidence?: number;
  reason?: string;
}

interface CFAVisualizationProps {
  data: {
    base_scores?: Record<string, number>;
    neutral_scores?: Record<string, number>;
    contributions?: CFAContribution[];
    neutral_rewrite_preview?: string;
  };
}

export default function CFAVisualization({ data }: CFAVisualizationProps) {
  if (!data || !data.contributions) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-400">
        <div className="text-center">
          <Info className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>No CFA data available</p>
        </div>
      </div>
    );
  }

  const dimensionColors = {
    ideological_stance: 'blue',
    factual_grounding: 'green',
    emotional_tone: 'purple',
    source_transparency: 'yellow',
    framing_choices: 'pink'
  };

  const dimensionLabels = {
    ideological_stance: 'Ideology',
    factual_grounding: 'Factual',
    emotional_tone: 'Emotional',
    source_transparency: 'Transparency',
    framing_choices: 'Framing'
  };

  // Group contributions by dimension
  const groupedContributions = data.contributions.reduce((acc, contrib) => {
    if (!acc[contrib.dimension]) {
      acc[contrib.dimension] = [];
    }
    acc[contrib.dimension].push(contrib);
    return acc;
  }, {} as Record<string, CFAContribution[]>);

  return (
    <div className="space-y-8">
      {/* Score Comparison */}
      <div>
        <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <div className="w-8 h-0.5 bg-gradient-to-r from-blue-500 to-purple-500" />
          Baseline Comparison
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Original Scores */}
          <div className="bg-white/5 border border-white/10 rounded-xl p-6">
            <h4 className="text-sm font-medium text-gray-400 mb-4">Original Article</h4>
            <div className="space-y-3">
              {data.base_scores && Object.entries(data.base_scores).map(([dim, scoreData]) => (
                <div key={dim} className="flex items-center justify-between">
                  <span className="text-sm text-gray-300">
                    {dimensionLabels[dim as keyof typeof dimensionLabels] || dim}
                  </span>
                  <div className="flex items-center gap-3">
                    <div className="w-32 h-2 bg-white/10 rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${scoreData || 0}%` }}
                        transition={{ duration: 1 }}
                        className={cn(
                          "h-full rounded-full",
                          `bg-${dimensionColors[dim as keyof typeof dimensionColors] || 'gray'}-500`
                        )}
                      />
                    </div>
                    <span className="text-sm font-medium w-10 text-right">
                      {scoreData || 0}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Neutral Baseline */}
          <div className="bg-white/5 border border-white/10 rounded-xl p-6">
            <h4 className="text-sm font-medium text-gray-400 mb-4">Neutral Baseline</h4>
            <div className="space-y-3">
              {data.neutral_scores && Object.entries(data.neutral_scores).map(([dim, scoreData]) => (
                <div key={dim} className="flex items-center justify-between">
                  <span className="text-sm text-gray-300">
                    {dimensionLabels[dim as keyof typeof dimensionLabels] || dim}
                  </span>
                  <div className="flex items-center gap-3">
                    <div className="w-32 h-2 bg-white/10 rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${scoreData || 0}%` }}
                        transition={{ duration: 1, delay: 0.2 }}
                        className="h-full bg-gray-500 rounded-full"
                      />
                    </div>
                    <span className="text-sm font-medium w-10 text-right">
                      {scoreData || 0}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Phrase Contributions */}
      <div>
        <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <div className="w-8 h-0.5 bg-gradient-to-r from-purple-500 to-pink-500" />
          Phrase Contributions
        </h3>
        <div className="space-y-4">
          {Object.entries(groupedContributions).map(([dimension, contribs]) => (
            <div key={dimension} className="space-y-3">
              <div className="flex items-center gap-2 mb-2">
                <Badge 
                  variant="outline" 
                  className={cn(
                    "border-white/20",
                    `text-${dimensionColors[dimension as keyof typeof dimensionColors] || 'gray'}-400`
                  )}
                >
                  {dimensionLabels[dimension as keyof typeof dimensionLabels] || dimension}
                </Badge>
                <span className="text-xs text-gray-400">
                  {contribs.length} influential phrases
                </span>
              </div>
              
              {contribs.map((contrib, idx) => (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.05 }}
                  className="bg-white/5 border border-white/10 rounded-lg p-4 hover:border-white/20 transition-all"
                >
                  <div className="flex items-start justify-between mb-2">
                    <p className="text-sm text-gray-300 italic flex-1 mr-4">
                      &ldquo;{contrib.span}...&rdquo;
                    </p>
                    <div className="flex items-center gap-2">
                      <div className={cn(
                        "flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium",
                        contrib.delta > 0 
                          ? "bg-red-500/20 text-red-400"
                          : contrib.delta < 0
                          ? "bg-green-500/20 text-green-400"
                          : "bg-gray-500/20 text-gray-400"
                      )}>
                        {contrib.delta > 0 ? (
                          <ArrowUp className="w-3 h-3" />
                        ) : contrib.delta < 0 ? (
                          <ArrowDown className="w-3 h-3" />
                        ) : (
                          <Minus className="w-3 h-3" />
                        )}
                        {Math.abs(contrib.delta).toFixed(1)}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <p className="text-xs text-gray-500">
                      {contrib.reason || `${contrib.delta > 0 ? 'Increases' : 'Decreases'} ${dimension.replace('_', ' ')}`}
                    </p>
                    <div className="flex items-center gap-1 text-xs text-gray-400">
                      <span>Confidence:</span>
                      <span className="font-medium">
                        {(contrib.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          ))}
        </div>
      </div>

      {/* Neutral Rewrite Preview */}
      {data.neutral_rewrite_preview && (
        <div>
          <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <div className="w-8 h-0.5 bg-gradient-to-r from-green-500 to-teal-500" />
            Neutral Baseline Text
          </h3>
          <div className="bg-white/5 border border-white/10 rounded-xl p-6">
            <p className="text-sm text-gray-300 leading-relaxed">
              {data.neutral_rewrite_preview}
            </p>
            <div className="mt-4 flex items-center gap-2 text-xs text-gray-500">
              <Info className="w-3 h-3" />
              <span>AI-generated neutral version with evaluative language removed</span>
            </div>
          </div>
        </div>
      )}

      {/* Methodology Note */}
      <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/20 rounded-xl p-6">
        <div className="flex items-start gap-3">
          <Info className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="font-semibold text-blue-400 mb-2">About CFA</h4>
            <p className="text-sm text-gray-300 leading-relaxed">
              Contrastive Framing Attribution identifies which specific phrases in an article 
              contribute most to its bias scores by comparing against a neutral baseline. 
              The delta values show how much each phrase pushes the bias score away from neutral, 
              with positive values indicating increased bias and negative values indicating decreased bias.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
