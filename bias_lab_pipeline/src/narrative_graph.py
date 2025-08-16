"""Narrative Graph with Signed Edges - Clustering articles by framing similarity."""
import numpy as np
from typing import List, Dict, Tuple
from collections import defaultdict
import networkx as nx
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import community as community_louvain

class NarrativeGraph:
    """
    Build a graph of articles with signed edges showing directional framing differences.
    Uses Louvain community detection to find narrative clusters.
    """
    
    def __init__(self):
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.graph = nx.Graph()
        
    def build_graph(self, articles: List[Dict], scores: List[Dict]) -> nx.Graph:
        """
        Build graph with articles as nodes, cosine similarity as edge weights,
        and ideological difference as edge signs.
        """
        # Embed all articles
        texts = [a.get('full_text', a.get('content', ''))[:1000] for a in articles]
        embeddings = self.embedder.encode(texts)
        
        # Create nodes
        for i, article in enumerate(articles):
            self.graph.add_node(i, 
                              title=article['title'],
                              source=article['source'],
                              url=article['url'],
                              embedding=embeddings[i],
                              ideology_score=scores[i]['scores']['ideological_stance'])
        
        # Create edges with weights and signs
        for i in range(len(articles)):
            for j in range(i + 1, len(articles)):
                # Edge weight = cosine similarity
                weight = cosine_similarity([embeddings[i]], [embeddings[j]])[0][0]
                
                # Edge sign = ideological difference direction
                ideology_diff = scores[i]['scores']['ideological_stance'] - \
                               scores[j]['scores']['ideological_stance']
                sign = np.sign(ideology_diff) if abs(ideology_diff) > 10 else 0
                
                if weight > 0.3:  # Only connect sufficiently similar articles
                    self.graph.add_edge(i, j, 
                                       weight=weight,
                                       sign=sign,
                                       ideology_diff=ideology_diff)
        
        return self.graph
    
    def detect_communities(self) -> Dict[int, List[int]]:
        """
        Run Louvain community detection on the unsigned graph.
        Returns mapping of community_id -> [article_indices].
        """
        # Create unsigned graph for community detection
        unsigned_graph = nx.Graph()
        for u, v, data in self.graph.edges(data=True):
            unsigned_graph.add_edge(u, v, weight=abs(data['weight']))
        
        # Run Louvain
        partition = community_louvain.best_partition(unsigned_graph)
        
        # Group nodes by community
        communities = defaultdict(list)
        for node, comm_id in partition.items():
            communities[comm_id].append(node)
        
        return dict(communities)
    
    def compute_cluster_polarity(self, community: List[int]) -> Dict:
        """
        Compute the ideological polarity and framing characteristics of a cluster.
        """
        if not community:
            return {}
            
        # Get ideology scores for community members
        ideology_scores = [self.graph.nodes[n]['ideology_score'] for n in community]
        
        # Compute statistics
        mean_ideology = np.mean(ideology_scores)
        std_ideology = np.std(ideology_scores)
        
        # Determine cluster lean
        if mean_ideology < 35:
            lean = "left-leaning"
        elif mean_ideology > 65:
            lean = "right-leaning"
        else:
            lean = "centrist"
        
        # Check for consensus vs division
        if std_ideology < 10:
            consensus = "high consensus"
        elif std_ideology < 20:
            consensus = "moderate consensus"
        else:
            consensus = "divided"
        
        return {
            'mean_ideology': round(mean_ideology, 1),
            'std_ideology': round(std_ideology, 1),
            'lean': lean,
            'consensus': consensus,
            'size': len(community)
        }
    
    def generate_cluster_descriptor(self, community: List[int], articles: List[Dict]) -> str:
        """
        Generate a natural language descriptor for a narrative cluster.
        """
        # Get sources in this cluster
        sources = [self.graph.nodes[n]['source'] for n in community]
        unique_sources = list(set(sources))
        
        # Get polarity info
        polarity = self.compute_cluster_polarity(community)
        
        # Get representative headlines
        headlines = [self.graph.nodes[n]['title'] for n in community[:3]]
        
        # Build descriptor
        descriptor = f"Cluster of {polarity['size']} articles from {', '.join(unique_sources[:3])}. "
        descriptor += f"Framing: {polarity['lean']} with {polarity['consensus']}. "
        
        # Add example headline theme
        if headlines:
            # Find common words in headlines
            all_words = ' '.join(headlines).lower().split()
            word_freq = defaultdict(int)
            for word in all_words:
                if len(word) > 4:  # Skip short words
                    word_freq[word] += 1
            
            # Get top theme words
            theme_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:3]
            if theme_words:
                themes = [w[0] for w in theme_words]
                descriptor += f"Key themes: {', '.join(themes)}."
        
        return descriptor
    
    def compute_framing_axis(self, articles: List[Dict]) -> np.ndarray:
        """
        Project articles onto a 1-D framing axis between neutral and biased anchors.
        """
        texts = [a.get('full_text', a.get('content', ''))[:1000] for a in articles]
        embeddings = self.embedder.encode(texts)
        
        # Define anchor texts
        neutral_anchor = "The event occurred. Officials provided statements. Data shows results."
        biased_anchor = "Shocking developments reveal disturbing pattern. Critics slam decision. Experts warn of dire consequences."
        
        anchor_embeddings = self.embedder.encode([neutral_anchor, biased_anchor])
        
        # Project onto axis between anchors
        axis_vector = anchor_embeddings[1] - anchor_embeddings[0]
        axis_vector = axis_vector / np.linalg.norm(axis_vector)
        
        projections = np.dot(embeddings, axis_vector)
        
        return projections
    
    def get_narrative_clusters(self, articles: List[Dict], scores: List[Dict]) -> List[Dict]:
        """
        Main method: Build graph, detect communities, and return cluster information.
        """
        # Build the graph
        self.build_graph(articles, scores)
        
        # Detect communities
        communities = self.detect_communities()
        
        # Compute framing axis
        framing_projections = self.compute_framing_axis(articles)
        
        # Build cluster information
        clusters = []
        for comm_id, members in communities.items():
            cluster_info = {
                'cluster_id': comm_id,
                'article_ids': members,
                'articles': [articles[i] for i in members],
                'polarity': self.compute_cluster_polarity(members),
                'descriptor': self.generate_cluster_descriptor(members, articles),
                'mean_framing_score': float(np.mean([framing_projections[i] for i in members])),
                'sources': list(set([articles[i]['source'] for i in members]))
            }
            clusters.append(cluster_info)
        
        # Sort by size
        clusters.sort(key=lambda x: x['polarity']['size'], reverse=True)
        
        return clusters