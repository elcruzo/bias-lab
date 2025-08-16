# The Bias Lab - Frontend UI

A news bias analysis platform that helps users understand media perspectives through AI-powered analysis.

## 🎨 Design Philosophy

**2025 Aesthetic**: Dark mode, glassmorphism, gradient accents, and smooth animations create a premium, futuristic feel that matches the sophistication of the AI backend.

## 🚀 Features

### Core Functionality

#### 1. **Smart Search**
- Real-time news analysis for any topic
- Quick suggestion buttons for trending topics
- Triggers complete bias analysis pipeline
- Loading states with animations

#### 2. **Article Grid/List View**
- Toggle between grid and list layouts
- Live bias score visualizations
- Color-coded severity indicators
- Confidence intervals displayed
- Source badges and metadata

#### 3. **Article Detail Modal**
- **5D Bias Breakdown**: Detailed scores with explanations
- **CFA Analysis**: Shows which phrases contribute to bias
- **Transparency Metrics**: Source quality indicators
- **Primary Sources**: Extracted links to documents
- **Confidence Bands**: Statistical uncertainty visualization

#### 4. **Advanced Visualizations**

**Narrative Network Graph** (D3.js)
- Force-directed graph showing article relationships
- Clusters represent different narrative framings
- Interactive zoom and pan
- Color-coded by ideological stance

**CFA Visualization**
- Phrase-level bias attribution
- Color intensity shows contribution strength
- Hover for detailed explanations
- Sortable by impact

**Confidence Bands Chart**
- Conformal prediction intervals
- Visual uncertainty for each dimension
- Comparative view across articles

### UI Components

#### Glassmorphism Design System
```css
/* Glass effect with backdrop blur */
.glass-panel {
  background: rgba(15, 23, 42, 0.8);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(100, 116, 139, 0.2);
}
```

#### Gradient Accents
- Blue → Purple for primary actions
- Green for positive/factual indicators
- Red for high bias warnings
- Yellow for caution/uncertainty

#### Animation System (Framer Motion)
- Smooth page transitions
- Staggered list animations
- Hover effects on cards
- Loading skeletons

## 🛠 Technical Stack

### Core Technologies
- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript 5.x
- **Styling**: Tailwind CSS 3.4
- **Components**: Shadcn/ui
- **State**: React hooks (useState, useEffect)

### Visualization Libraries
- **Charts**: Recharts (radar charts, bars)
- **Graphs**: D3.js (network visualization)
- **Animation**: Framer Motion
- **Icons**: Lucide React

### Data Fetching
- **API Client**: Native fetch with type safety
- **Caching**: React query patterns
- **Error Handling**: Try-catch with user feedback
- **Loading States**: Skeleton components

## 📁 Project Structure

```
bias-lab-ui/
├── app/
│   ├── page.tsx         # Main application page
│   ├── layout.tsx        # Root layout with providers
│   └── globals.css       # Global styles & themes
├── components/
│   ├── ArticleCard.tsx   # Article display card
│   ├── ArticleDetailModal.tsx  # Full analysis modal
│   ├── BiasDistributionChart.tsx  # Bias visualization
│   ├── CFAVisualization.tsx  # Phrase attribution
│   ├── ConfidenceBands.tsx   # Uncertainty charts
│   ├── NarrativeNetwork.tsx  # D3 graph component
│   └── ui/               # Shadcn components
├── lib/
│   ├── utils.ts          # Helper functions
│   └── config.ts         # App configuration
└── public/               # Static assets
```

## 🔌 Backend Integration

### API Endpoints Used

```typescript
// Fetch all articles with scores
GET /articles → Article[]

// Get detailed analysis
GET /articles/{id} → ArticleDetail (triggers CFA)

// Search for new topic
POST /search?query={q} → Success message

// Get narrative clusters
GET /narratives → Narrative[]

// System health check
GET /health → HealthStatus

// Get errors/warnings
GET /errors → ErrorResponse
```

### Type Definitions

```typescript
interface Article {
  article_id: string | number;
  title: string;
  source: string;
  scores: Record<string, number>;
  confidence_interval?: ConfidenceInterval;
  highlighted_phrases?: Record<string, string[]>;
  stale?: boolean;
}

interface ArticleDetailResponse extends Article {
  cfa_analysis?: CFAAnalysis;
  transparency_analysis?: TransparencyMetrics;
  primary_source_links?: string[];
  reasoning?: Record<string, string>;
}
```

## 🎯 User Flows

### Search Flow
1. User enters query (e.g., "climate change")
2. Click search or press Enter
3. Loading animation (~60s analysis)
4. Articles appear with bias scores
5. Can toggle views, sort, filter

### Article Analysis Flow
1. Click any article card
2. Modal opens with loading state
3. Backend computes CFA if needed (~36s)
4. Full analysis displayed
5. Can explore different tabs/visualizations

### Advanced Features Toggle
1. Click "Show Advanced" button
2. Reveals network graph, CFA details, confidence bands
3. Interactive exploration of data
4. Can hide to simplify view

## ⚡ Performance

### Optimizations
- **Dynamic imports** for heavy components
- **Lazy loading** of visualizations
- **Memoization** of expensive computations
- **Debounced** search input
- **Virtual scrolling** for long lists (planned)

### Metrics
- **Initial Load**: < 2s (cached data)
- **Search Response**: Visual feedback < 100ms
- **Article Click**: Modal opens instantly
- **CFA Loading**: Progressive with skeleton
- **Animations**: 60fps on modern devices

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ 
- npm or yarn
- Backend API running on port 8000

### Installation

```bash
# Clone and enter directory
cd bias-lab-ui

# Install dependencies
npm install

# Set up environment
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Run development server
npm run dev
```

Visit `http://localhost:3000` to see the app!

### Build for Production

```bash
# Create optimized build
npm run build

# Run production server
npm start
```

## 🎨 Customization

### Theme Colors
Edit `tailwind.config.ts`:
```javascript
colors: {
  primary: { /* your colors */ },
  accent: { /* your colors */ }
}
```

### Component Styling
All components use Tailwind classes for easy customization:
```tsx
<div className="bg-gray-900/50 backdrop-blur-xl rounded-2xl p-6">
  {/* Your content */}
</div>
```

## 📊 Features in Action

### What Users See

1. **Search Bar**: Prominent, with suggestions
2. **Article Cards**: Rich preview with inline scores
3. **Bias Meters**: Visual 0-100 scales
4. **Narrative Clusters**: Grouped by framing
5. **Detailed Modal**: Everything about an article
6. **System Status**: Real-time health indicator

### What's Connected

✅ **All Backend Features**:
- Search triggers full pipeline
- Articles show real scores
- Click loads CFA analysis
- Narratives display clusters
- Errors shown to user
- Health monitored live

The frontend successfully surfaces all the sophisticated AI analysis in an intuitive, beautiful interface that makes media bias analysis accessible to everyone.

## 🐛 Troubleshooting

### Common Issues

**"Failed to connect to API"**
- Ensure backend is running on port 8000
- Check CORS settings in backend
- Verify network connectivity

**Slow Loading**
- First load fetches all data
- CFA computation takes ~36s
- Consider implementing pagination

**Missing Visualizations**
- Check browser console for errors
- Ensure D3.js loaded correctly
- Verify data format from API

## 🚧 Future Enhancements

- Real-time updates with WebSockets
- User accounts and saved searches
- Export reports as PDF
- Mobile app version
- Dark/light theme toggle
- Internationalization (i18n)

---

*Built with ❤️ for The Bias Lab - Making AI-powered media analysis beautiful and accessible.*