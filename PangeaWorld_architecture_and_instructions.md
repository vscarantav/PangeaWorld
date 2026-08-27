# PangeaWorld Architecture & Instructions

> **Reference**: [PangeaWorld Implementation Plan](./PangeaWorld_Implementation_Plan.md)

## File Map
The current structure of the PangeaWorld repository:

```
PangeaWorld/
├── PangeaWorld_Implementation_Plan.html / .md (Design & Planning Docs)
├── PangeaWorld_Stakeholder_Presentation.pptx  (Pitch Deck)
├── backend/
│   └── main.py                                (Initial FastAPI backend setup)
└── frontend/
    ├── package.json / vite.config.js          (Vite tooling configuration)
    ├── index.html                             (Vite entry point)
    ├── src/                                   (React source code directory)
    └── public/
        ├── favicon.svg / icons.svg
        └── map_prototype.html                 (Monolithic HTML/JS/CSS Canvas Map Prototype)
```

## Tools Used
- **Map Prototype**: Built entirely with Vanilla JavaScript, HTML5 `<canvas>`, and CSS.
- **Procedural Generation**: Utilizes pure math (composite sine/cosine waves, Voronoi partitioning, and distance calculations) instead of external noise libraries (like Perlin) to generate natural shapes and borders.
- **Frontend Framework**: Scaffolded using Vite and React (for the future application dashboards).
- **Backend Framework**: Scaffolded using Python FastAPI.

## Expected Behaviors
- **Organic Procedural Generation**: The `map_prototype.html` generates a uniquely shaped continent upon every reload. The continent shape is calculated using complex sine waves.
- **Natural Borders**: The 8 countries are divided using a Voronoi diagram based on fixed capital anchor points, enhanced with 2D noise to create squiggly, organic borders.
- **Island Generation**: Zephyria is generated as a distinct island landmass off the coast of the main continent.
- **Interactive Grid**: The map renders an equilateral triangle grid. Players can hover over the edges (which highlight in green/yellow) and click to permanently build roads.
- **Dynamic Labels**: The country labels (e.g. "Terranova") dynamically position themselves deep within their respective borders based on the procedural shape formula.
- **Zoom Controls**: The sidebar features a "Map Controls" panel with a slider to zoom the canvas in and out, preserving interaction accuracy.

## Game Rules (As implemented in prototype)
- **Road Construction**: Building a standard road costs **$1M** per segment.
- **Bridges**: Roads built over river edges cost **$3M** per segment (3x multiplier).
- **Impassable Ocean**: Edges touching ocean triangles cannot be built upon.
- **Mountain Mazes**: Mountain generation creates clustered mountain ranges. Crucially, every mountain triangle randomly blocks **2 out of its 3 edges**, preventing any road construction on those edges. This forces players to navigate winding valleys and find specific "passes" through mountain ranges, making logistics a strategic challenge.
- **Dynamic Cost Calculation**: The UI updates the "Total Project Cost" automatically as roads are placed.

## Applied vs. Not Yet Applied Planned Features

### ✅ Applied Features (Phase 1 Map Foundations)
- **Grid-Based Construction**: The map is successfully divided into a fine grid where presidents "trace the route" line-by-line.
- **Distance & Terrain Costs**: Baseline edge traversal costs are implemented (roads vs. bridges vs. impassable mountains).
- **8 Nations Geography**: The 8 nations (including Drakmoor and the Zephyria island) are fully defined and geographically distributed.
- **Mountain Ranges**: Distinct, restrictive mountain barriers are implemented.

### ⏳ Not Yet Applied Planned Features (Pending Future Phases)
- **Multiplayer Turn System**: The 48-hour staggered round system (Presidential vs. Company phases) is not yet built.
- **Macro/Micro Economy Engine**: GDP, CPI, inflation, pricing, and company profitability loops are not yet implemented.
- **AI Agent Integration**: The embedded Gemini AI Advisor and the Drakmoor AI antagonist bot are not yet wired up.
- **Dashboards**: The President dashboard, Company Executive dashboard, FMI portal, and UN Assembly chat are pending React implementation.
- **Military Mechanics**: Attack/Defense indices, troop deployments, and intelligence operations are pending.
- **Logistics Math**: The complex "Landed Cost" math (shipping rate × distance × mode multiplier) is pending the routing algorithm layer.
