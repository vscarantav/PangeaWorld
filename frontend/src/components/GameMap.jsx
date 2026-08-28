import React, { useEffect, useRef, useState, useMemo } from 'react';
import { generateMapData, distToSegment, TERRAIN } from '../utils/MapGenerator';

// SVG Assets for Organic View
const mountainSvg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#555" stroke="#ccc" stroke-width="1"><path d="m8 3 4 8 5-5 5 15H2L8 3z"/></svg>`;
const citySvg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#333" stroke="#fff" stroke-width="1"><path d="M4 22V8h4v14M8 22V12h4v10M12 22V4h6v18M18 22v-8h2v8"/></svg>`;
const bigCitySvg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#f1c40f" stroke="#000" stroke-width="1"><path d="M4 22V8h4v14M8 22V12h4v10M12 22V4h6v18M18 22v-8h2v8"/><circle cx="15" cy="8" r="2" fill="#fff" /></svg>`;
const portSvg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#e74c3c" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="5" r="3"/><line x1="12" y1="22" x2="12" y2="8"/><path d="M5 12H2a10 10 0 0 0 20 0h-3"/></svg>`;

const createImg = (svgString) => {
    const img = new Image();
    img.src = 'data:image/svg+xml;base64,' + btoa(svgString);
    return img;
};

const icons = {
    mountain: createImg(mountainSvg),
    city: createImg(citySvg),
    bigCity: createImg(bigCitySvg),
    port: createImg(portSvg)
};

const textureImgs = {
    grass: new Image(),
    sand: new Image(),
    snow: new Image(),
    rock: new Image()
};
textureImgs.grass.src = '/grass.jpg';
textureImgs.sand.src = '/sand.jpg';
textureImgs.snow.src = '/snow.jpg';
textureImgs.rock.src = '/rock.jpg';

// --------------------------------------------------------
// TOPOLOGICAL BOUNDARY EXTRACTION
// Extracts guaranteed perfect polygon loops from a set of triangles
// --------------------------------------------------------
const extractRegionPolygons = (triangles) => {
    const edgeCounts = new Map();
    
    // Use fixed precision to guarantee matching identical edges
    const getEdgeKey = (p1, p2) => `${p1.x.toFixed(2)},${p1.y.toFixed(2)}->${p2.x.toFixed(2)},${p2.y.toFixed(2)}`;
    const getPointKey = (p) => `${p.x.toFixed(2)},${p.y.toFixed(2)}`;
    
    // Add directed edges
    triangles.forEach(tri => {
        // Enforce consistent CCW winding order so adjacent edges cancel out
        let [p1, p2, p3] = tri.points;
        const crossProduct = (p2.x - p1.x) * (p3.y - p1.y) - (p3.x - p1.x) * (p2.y - p1.y);
        if (crossProduct < 0) {
            p2 = tri.points[2];
            p3 = tri.points[1];
        }
        
        const pts = [p1, p2, p3];
        for(let i=0; i<3; i++) {
            const v1 = pts[i];
            const v2 = pts[(i+1)%3];
            const key = getEdgeKey(v1, v2);
            edgeCounts.set(key, { p1: v1, p2: v2 });
        }
    });
    
    // Filter to boundary edges (ones with no reverse edge in the same terrain group)
    const boundaryEdges = [];
    edgeCounts.forEach((edge, key) => {
        const reverseKey = getEdgeKey(edge.p2, edge.p1);
        if (!edgeCounts.has(reverseKey)) {
            boundaryEdges.push(edge);
        }
    });
    
    // Link boundary edges into continuous loops
    const nextEdgeMap = new Map();
    boundaryEdges.forEach(e => {
        const p1Key = getPointKey(e.p1);
        if (!nextEdgeMap.has(p1Key)) nextEdgeMap.set(p1Key, []);
        nextEdgeMap.get(p1Key).push(e);
    });
    
    const polygons = [];
    const visited = new Set();
    
    boundaryEdges.forEach(startEdge => {
        const startKey = getEdgeKey(startEdge.p1, startEdge.p2);
        if (visited.has(startKey)) return;
        
        const poly = [];
        let currEdge = startEdge;
        
        while (currEdge) {
            const currKey = getEdgeKey(currEdge.p1, currEdge.p2);
            if (visited.has(currKey)) break; 
            
            visited.add(currKey);
            poly.push(currEdge.p1);
            
            const nextEdges = nextEdgeMap.get(getPointKey(currEdge.p2));
            if (nextEdges && nextEdges.length > 0) {
                currEdge = nextEdges.find(e => !visited.has(getEdgeKey(e.p1, e.p2)));
            } else {
                currEdge = null;
            }
        }
        
        if (poly.length > 2) {
            polygons.push(poly);
        }
    });
    
    return polygons;
};

// Modifies the active path in `ctx` without starting a new one, 
// allowing Even-Odd/Non-Zero winding to naturally punch holes for lakes
const drawCurve = (ctx, points, tension = 0.4, isClosed = true) => {
    if (points.length < 2) return;
    
    if (isClosed) {
        const loopPts = [points[points.length-1], ...points, points[0], points[1]];
        ctx.moveTo(loopPts[1].x, loopPts[1].y);
        for (let i = 1; i < loopPts.length - 2; i++) {
            const p0 = loopPts[i - 1];
            const p1 = loopPts[i];
            const p2 = loopPts[i + 1];
            const p3 = loopPts[i + 2];
            
            const cp1x = p1.x + (p2.x - p0.x) / 6 * tension;
            const cp1y = p1.y + (p2.y - p0.y) / 6 * tension;
            const cp2x = p2.x - (p3.x - p1.x) / 6 * tension;
            const cp2y = p2.y - (p3.y - p1.y) / 6 * tension;
            
            ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, p2.x, p2.y);
        }
    } else {
        const linePts = [points[0], ...points, points[points.length-1]];
        ctx.moveTo(linePts[1].x, linePts[1].y);
        for (let i = 1; i < linePts.length - 2; i++) {
            const p0 = linePts[i - 1];
            const p1 = linePts[i];
            const p2 = linePts[i + 1];
            const p3 = linePts[i + 2];
            
            const cp1x = p1.x + (p2.x - p0.x) / 6 * tension;
            const cp1y = p1.y + (p2.y - p0.y) / 6 * tension;
            const cp2x = p2.x - (p3.x - p1.x) / 6 * tension;
            const cp2y = p2.y - (p3.y - p1.y) / 6 * tension;
            
            ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, p2.x, p2.y);
        }
    }
};

export default function GameMap({ seed = 'PangeaGameSeed123', width = 800, height = 600, isPlanningMode = false }) {
    const canvasRef = useRef(null);
    const [mapData, setMapData] = useState(null);
    const [organicDataCache, setOrganicDataCache] = useState(null);
    const [totalCost, setTotalCost] = useState(0);
    const [zoom, setZoom] = useState(1);
    const [pan, setPan] = useState({ x: 0, y: 0 });
    const [isDragging, setIsDragging] = useState(false);
    const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
    const [hasDragged, setHasDragged] = useState(false);
    const [imagesLoaded, setImagesLoaded] = useState(false);

    useEffect(() => {
        const data = generateMapData(seed, width, height);
        let initialCost = 0;
        data.edges.forEach(e => {
            if (e.hasRailroad) {
                let cost = 1;
                if (e.isRiver) cost = 3;
                else if (e.triangles.some(t => t.terrain === TERRAIN.MOUNTAIN)) cost = 1.5;
                initialCost += cost;
            }
        });
        setMapData(data);
        setTotalCost(initialCost);
        
        // --- Precalculate perfect polygons for the organic view ---
        const landTriangles = data.triangles.filter(t => t.terrain !== TERRAIN.OCEAN);
        const landRings = extractRegionPolygons(landTriangles);
        
        const terrainGroups = new Map();
        data.triangles.forEach(tri => {
            if (tri.terrain === TERRAIN.OCEAN) return;
            
            // Group logic: By Country if it exists, otherwise by Terrain.
            let key = tri.terrain.name;
            if (tri.terrain === TERRAIN.CITY && tri.country) {
                key = 'CITY_' + tri.country.id;
            } else if (tri.country) {
                key = 'COUNTRY_' + tri.country.id;
            }
            
            if (!terrainGroups.has(key)) terrainGroups.set(key, { 
                color: (tri.terrain === TERRAIN.CITY && tri.country) ? tri.country.cityColor : tri.terrain.color, 
                texture: (tri.terrain === TERRAIN.CITY && tri.country) ? tri.country.terrain.texture : tri.terrain.texture,
                triangles: [] 
            });
            terrainGroups.get(key).triangles.push(tri);
        });

        const organicPolys = [];
        terrainGroups.forEach(group => {
            const rings = extractRegionPolygons(group.triangles);
            organicPolys.push({ color: group.color, texture: group.texture, rings });
        });
        
        setOrganicDataCache({ landRings, organicPolys });

        Promise.all([
            new Promise(res => { icons.mountain.onload = res; if (icons.mountain.complete) res(); }),
            new Promise(res => { icons.city.onload = res; if (icons.city.complete) res(); }),
            new Promise(res => { icons.bigCity.onload = res; if (icons.bigCity.complete) res(); }),
            new Promise(res => { icons.port.onload = res; if (icons.port.complete) res(); }),
            new Promise(res => { textureImgs.grass.onload = res; if (textureImgs.grass.complete) res(); }),
            new Promise(res => { textureImgs.sand.onload = res; if (textureImgs.sand.complete) res(); }),
            new Promise(res => { textureImgs.snow.onload = res; if (textureImgs.snow.complete) res(); }),
            new Promise(res => { textureImgs.rock.onload = res; if (textureImgs.rock.complete) res(); })
        ]).then(() => setImagesLoaded(true));
    }, [seed, width, height]);

    useEffect(() => {
        if (!mapData || !canvasRef.current) return;
        
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.save();
        ctx.translate(canvas.width / 2 + pan.x, canvas.height / 2 + pan.y);
        ctx.scale(zoom, zoom);
        ctx.translate(-canvas.width / 2, -canvas.height / 2);
        
        if (isPlanningMode) {
            renderPlanningView(ctx, mapData);
        } else {
            renderOrganicView(ctx, mapData, organicDataCache);
        }
        
        drawCountryNames(ctx, mapData);
        ctx.restore();
    }, [mapData, organicDataCache, zoom, pan, isPlanningMode, imagesLoaded]);

    const renderPlanningView = (ctx, mapData) => {
        mapData.triangles.forEach(tri => {
            ctx.beginPath();
            ctx.moveTo(tri.points[0].x, tri.points[0].y);
            ctx.lineTo(tri.points[1].x, tri.points[1].y);
            ctx.lineTo(tri.points[2].x, tri.points[2].y);
            ctx.closePath();
            
            if (tri.terrain === TERRAIN.CITY && tri.country) ctx.fillStyle = tri.country.cityColor;
            else ctx.fillStyle = tri.terrain.color;
            ctx.fill();
            ctx.strokeStyle = 'rgba(0,0,0,0.03)';
            ctx.lineWidth = 1;
            ctx.stroke();
        });

        mapData.edges.forEach(edge => {
            const isImpassable = edge.isImpassable;
            if (edge.isRiver && !isImpassable) {
                ctx.beginPath();
                ctx.moveTo(edge.p1.x, edge.p1.y);
                ctx.lineTo(edge.p2.x, edge.p2.y);
                ctx.strokeStyle = '#3498db';
                ctx.lineWidth = 2;
                ctx.stroke();
            }

            if (edge.hasRailroad) {
                ctx.beginPath();
                ctx.moveTo(edge.p1.x, edge.p1.y);
                ctx.lineTo(edge.p2.x, edge.p2.y);
                ctx.strokeStyle = edge.isRiver ? '#f1c40f' : '#ecf0f1';
                ctx.lineWidth = 1.5;
                ctx.stroke();
            } else if (edge.isHovered && !isImpassable) {
                ctx.beginPath();
                ctx.moveTo(edge.p1.x, edge.p1.y);
                ctx.lineTo(edge.p2.x, edge.p2.y);
                ctx.strokeStyle = edge.isRiver ? '#f1c40f' : '#2ecc71';
                ctx.lineWidth = 2;
                ctx.stroke();
            }
        });
        
        mapData.edges.forEach(edge => {
           if(edge.hasRailroad) {
               ctx.beginPath();
               ctx.arc(edge.p1.x, edge.p1.y, 0.8, 0, Math.PI * 2);
               ctx.fillStyle = '#ecf0f1';
               ctx.fill();
               ctx.beginPath();
               ctx.arc(edge.p2.x, edge.p2.y, 0.8, 0, Math.PI * 2);
               ctx.fillStyle = '#ecf0f1';
               ctx.fill();
           } 
        });
        
        mapData.triangles.forEach(tri => {
            if (tri.isPort) {
                ctx.beginPath();
                ctx.arc(tri.center.x, tri.center.y, 1.5, 0, Math.PI * 2);
                ctx.fillStyle = (tri.country && tri.country.id === 'DRAKMOOR') ? '#000080' : 'rgba(255, 0, 0, 0.8)';
                ctx.fill();
            }
        });
    };

    const renderOrganicView = (ctx, mapData, cache) => {
        if (!cache) return;
        
        // 1. Draw perfectly extracted topological bounds with smooth Catmull-Rom splines
        ctx.fillStyle = '#111'; 
        ctx.beginPath();
        cache.landRings.forEach(ring => drawCurve(ctx, ring, 0.4, true));
        ctx.fill();

        cache.organicPolys.forEach(group => {
            if (group.texture && textureImgs[group.texture].complete) {
                const pattern = ctx.createPattern(textureImgs[group.texture], 'repeat');
                const matrix = new DOMMatrix().scale(0.3, 0.3); // Scale down the textures so they look like fine detail
                pattern.setTransform(matrix);
                ctx.fillStyle = pattern;
            } else {
                ctx.fillStyle = group.color;
            }

            ctx.strokeStyle = group.color;
            ctx.lineWidth = 4; // Soft, slightly thick cartographic border
            ctx.lineJoin = 'round';
            
            ctx.beginPath();
            group.rings.forEach(ring => drawCurve(ctx, ring, 0.4, true));
            ctx.fill();
            
            // Cartographic styling: drop a subtle shadow around the country boundaries
            ctx.shadowColor = "rgba(0,0,0,0.5)";
            ctx.shadowBlur = 10;
            ctx.stroke();
            ctx.shadowBlur = 0;

            // Highlight border on top of the shadow
            ctx.lineWidth = 1;
            ctx.strokeStyle = 'rgba(255,255,255,0.4)';
            ctx.stroke();
        });

        // 2. Straight Railroads (Contrasting the curved geography cleanly)
        const railroads = mapData.edges.filter(e => e.hasRailroad);
        if (railroads.length > 0) {
            ctx.beginPath();
            railroads.forEach(e => {
                ctx.moveTo(e.p1.x, e.p1.y);
                ctx.lineTo(e.p2.x, e.p2.y);
            });
            ctx.strokeStyle = '#2c3e50'; 
            ctx.lineWidth = 3.5;
            ctx.lineJoin = 'round';
            ctx.stroke();

            ctx.beginPath();
            railroads.forEach(e => {
                ctx.moveTo(e.p1.x, e.p1.y);
                ctx.lineTo(e.p2.x, e.p2.y);
            });
            ctx.strokeStyle = '#ecf0f1'; 
            ctx.lineWidth = 1.5;
            ctx.setLineDash([4, 4]);
            ctx.stroke();
            ctx.setLineDash([]); 
        }

        // 3. Clustered Icons
        ctx.shadowColor = "rgba(0, 0, 0, 0.4)";
        ctx.shadowBlur = 3;
        ctx.shadowOffsetX = 1;
        ctx.shadowOffsetY = 1;
        
        const drawnMountains = [];
        
        mapData.triangles.forEach((tri) => {
            if (tri.terrain === TERRAIN.MOUNTAIN && icons.mountain.complete) {
                let tooClose = false;
                for (let i = 0; i < drawnMountains.length; i++) {
                    const dx = tri.center.x - drawnMountains[i].x;
                    const dy = tri.center.y - drawnMountains[i].y;
                    if (dx*dx + dy*dy < 400) { // 20px radius
                        tooClose = true;
                        break;
                    }
                }
                
                if (!tooClose) {
                    let jitterX = (tri.center.x % 4) - 2;
                    let jitterY = (tri.center.y % 4) - 2;
                    ctx.drawImage(icons.mountain, tri.center.x - 12 + jitterX, tri.center.y - 12 + jitterY, 24, 24);
                    drawnMountains.push(tri.center);
                }
            }
        });
        
        mapData.triangles.forEach(tri => {
            if (tri.terrain === TERRAIN.CITY) {
                let img = tri.isBigCity ? icons.bigCity : icons.city;
                if (img.complete) {
                    let size = tri.isBigCity ? 20 : 14;
                    ctx.drawImage(img, tri.center.x - size/2, tri.center.y - size/2 - 2, size, size);
                }
            }
            if (tri.isPort && icons.port.complete) {
                ctx.drawImage(icons.port, tri.center.x - 7, tri.center.y - 7, 14, 14);
            }
        });
        
        ctx.shadowBlur = 0; 
    };

    const drawCountryNames = (ctx, mapData) => {
        ctx.font = 'bold 24px "Segoe UI", Tahoma, Geneva, Verdana, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        
        mapData.countries.forEach(region => {
            let closestTri = null;
            let minDist = Infinity;
            
            mapData.triangles.forEach(tri => {
                if (tri.terrain === region.terrain) {
                    let dx = tri.center.x - region.labelX;
                    let dy = tri.center.y - region.labelY;
                    let dist = dx * dx + dy * dy;
                    if (dist < minDist) {
                        minDist = dist;
                        closestTri = tri;
                    }
                }
            });

            let targetX = closestTri ? closestTri.center.x : region.x;
            let targetY = closestTri ? closestTri.center.y : region.y;

            ctx.beginPath();
            ctx.moveTo(region.labelX, region.labelY);
            ctx.lineTo(targetX, targetY);
            ctx.strokeStyle = isPlanningMode ? 'rgba(255, 255, 255, 0.4)' : 'rgba(255, 255, 255, 0.2)';
            ctx.lineWidth = 2;
            ctx.stroke();
            
            ctx.beginPath();
            ctx.arc(targetX, targetY, 4, 0, Math.PI * 2);
            ctx.fillStyle = isPlanningMode ? 'rgba(255, 255, 255, 0.6)' : 'rgba(255, 255, 255, 0.4)';
            ctx.fill();

            if (!isPlanningMode) {
                ctx.shadowColor = "rgba(0, 0, 0, 0.6)";
                ctx.shadowBlur = 4;
                ctx.shadowOffsetX = 1;
                ctx.shadowOffsetY = 1;
            }

            ctx.lineWidth = 4;
            ctx.strokeStyle = 'rgba(0, 0, 0, 0.75)';
            ctx.fillStyle = 'rgba(255, 255, 255, 0.95)';
            
            if (isPlanningMode) ctx.strokeText(region.name, region.labelX, region.labelY);
            ctx.fillText(region.name, region.labelX, region.labelY);
            
            ctx.shadowBlur = 0; 
        });
    };

    const getClosestEdge = (mx, my) => {
        if (!mapData) return null;
        let closest = null;
        let minDist = 4 / zoom; 

        mapData.edges.forEach(edge => {
            if (edge.isImpassable) return;
            let d = distToSegment({x: mx, y: my}, edge.p1, edge.p2);
            if (d < minDist) {
                minDist = d;
                closest = edge;
            }
        });
        return closest;
    };

    const handleMouseDown = (e) => {
        setIsDragging(true);
        setHasDragged(false);
        setDragStart({ x: e.clientX, y: e.clientY });
    };

    const handleMouseUp = () => setIsDragging(false);

    const handleMouseLeave = () => {
        setIsDragging(false);
        if (mapData && isPlanningMode) {
            let needsRender = false;
            mapData.edges.forEach(edge => {
                if (edge.isHovered) {
                    edge.isHovered = false;
                    needsRender = true;
                }
            });
            if (needsRender) setMapData({ ...mapData });
        }
    };

    const handleMouseMove = (e) => {
        if (isDragging) {
            let dx = e.clientX - dragStart.x;
            let dy = e.clientY - dragStart.y;
            if (Math.abs(dx) > 2 || Math.abs(dy) > 2) setHasDragged(true);
            
            setPan(prev => ({ x: prev.x + dx, y: prev.y + dy }));
            setDragStart({ x: e.clientX, y: e.clientY });
            return;
        }

        if (!isPlanningMode || !mapData || !canvasRef.current) return;

        const canvas = canvasRef.current;
        const rect = canvas.getBoundingClientRect();
        let mx = e.clientX - rect.left;
        let my = e.clientY - rect.top;

        mx = (mx - canvas.width / 2 - pan.x) / zoom + canvas.width / 2;
        my = (my - canvas.height / 2 - pan.y) / zoom + canvas.height / 2;

        let needsRender = false;
        const closest = getClosestEdge(mx, my);
        
        mapData.edges.forEach(edge => {
            if (edge.isHovered && edge !== closest) {
                edge.isHovered = false;
                needsRender = true;
            }
        });

        if (closest && !closest.isHovered && !closest.hasRailroad) {
            closest.isHovered = true;
            needsRender = true;
        }

        if (needsRender) setMapData({ ...mapData });
    };

    const handleClick = (e) => {
        if (hasDragged) {
            setHasDragged(false);
            return;
        }

        if (!isPlanningMode || !mapData || !canvasRef.current) return;

        const canvas = canvasRef.current;
        const rect = canvas.getBoundingClientRect();
        let mx = e.clientX - rect.left;
        let my = e.clientY - rect.top;

        mx = (mx - canvas.width / 2 - pan.x) / zoom + canvas.width / 2;
        my = (my - canvas.height / 2 - pan.y) / zoom + canvas.height / 2;

        const closest = getClosestEdge(mx, my);
        if (closest && !closest.hasRailroad) {
            closest.hasRailroad = true;
            closest.isHovered = false;
            
            let cost = 1;
            if (closest.isRiver) cost = 3; 
            else if (closest.triangles.some(t => t.terrain === TERRAIN.MOUNTAIN)) cost = 1.5; 

            setTotalCost(prev => prev + cost);
            setMapData({ ...mapData });
        }
    };
    
    const handleWheel = (e) => {
        e.preventDefault();
        const zoomDelta = e.deltaY > 0 ? -0.1 : 0.1;
        setZoom(prev => Math.max(1, Math.min(5, prev + zoomDelta)));
    };

    return (
        <div style={{ position: 'relative', width: '100%', maxWidth: '800px' }}>
            <div style={{
                position: 'absolute',
                top: 10,
                right: 10,
                backgroundColor: 'rgba(30, 30, 30, 0.8)',
                padding: '10px',
                borderRadius: '5px',
                color: 'white',
                pointerEvents: 'none',
                boxShadow: '0 2px 10px rgba(0,0,0,0.5)',
                transition: 'opacity 0.3s',
                opacity: isPlanningMode ? 1 : 0.7
            }}>
                <div style={{ fontSize: '14px', marginBottom: '5px' }}>Total Project Cost:</div>
                <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#FFD700' }}>${totalCost.toFixed(1)}M</div>
            </div>
            
            <canvas 
                ref={canvasRef}
                width={width} 
                height={height}
                onMouseDown={handleMouseDown}
                onMouseUp={handleMouseUp}
                onMouseLeave={handleMouseLeave}
                onMouseMove={handleMouseMove}
                onClick={handleClick}
                onWheel={handleWheel}
                style={{
                    backgroundColor: '#2c3e50',
                    backgroundImage: 'url(/ocean-color.jpg)',
                    backgroundSize: 'cover',
                    border: '2px solid #333',
                    borderRadius: '8px',
                    display: 'block',
                    cursor: isPlanningMode ? 'crosshair' : 'grab',
                    width: '100%',
                    height: 'auto',
                    boxShadow: '0 10px 30px rgba(0,0,0,0.7)'
                }}
            />
        </div>
    );
}
