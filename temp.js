
        const canvas = document.getElementById('mapCanvas');
        const ctx = canvas.getContext('2d');
        
        // Grid properties
        const sideLength = 7;
        const h = sideLength * Math.sqrt(3) / 2; // height of an equilateral triangle
        
        // Terrain Types
        const TERRAIN = {
            OCEAN: { color: '#2c3e50', name: 'Ocean' },
            CITY: { color: '#ffffff', name: 'City' },
            MOUNTAIN: { color: '#555555', name: 'Impassable Peaks' },
            RIVER: { color: '#3498db', name: 'River' },
            TERRANOVA: { color: '#27ae60', name: 'Terranova (Plains)' },
            SOLARIA: { color: '#f1c40f', name: 'Solaria (Savanna)' },
            KAELEN: { color: '#16a085', name: 'Kaelen (Swamp)' },
            VALDORIA: { color: '#f39c12', name: 'Valdoria (Desert)' },
            ZEPHYRIA: { color: '#d35400', name: 'Zephyria (Hills)' },
            NORDVIK: { color: '#aed6f1', name: 'Nordvik (Tundra)' },
            AETHELGARD: { color: '#228b22', name: 'Aethelgard (Forest)' },
            DRAKMOOR: { color: '#7f8c8d', name: 'Drakmoor (Mountains)' }
        };

        // Data structures
        let triangles = []; // Stores triangle polygons
        let edges = [];     // Stores all unique edges between nodes
        let totalCost = 0;
        let zoom = 1;
        let panX = 0;
        let panY = 0;
        let isDragging = false;
        let dragStartX = 0;
        let dragStartY = 0;
        let hasDragged = false;

        const countries = [
            { id: 'TERRANOVA', name: 'Terranova', x: 480, y: 320, labelX: 740, labelY: 350, terrain: TERRAIN.TERRANOVA },
            { id: 'SOLARIA', name: 'Solaria', x: 420, y: 440, labelX: 620, labelY: 580, terrain: TERRAIN.SOLARIA },
            { id: 'KAELEN', name: 'Kaelen', x: 320, y: 420, labelX: 320, labelY: 580, terrain: TERRAIN.KAELEN },
            { id: 'VALDORIA', name: 'Valdoria', x: 280, y: 300, labelX: 80, labelY: 250, terrain: TERRAIN.VALDORIA },
            { id: 'NORDVIK', name: 'Nordvik', x: 340, y: 180, labelX: 250, labelY: 40, terrain: TERRAIN.NORDVIK },
            { id: 'AETHELGARD', name: 'Aethelgard', x: 450, y: 160, labelX: 550, labelY: 40, terrain: TERRAIN.AETHELGARD },
            { id: 'DRAKMOOR', name: 'Drakmoor', x: 520, y: 220, labelX: 720, labelY: 130, terrain: TERRAIN.DRAKMOOR },
            { id: 'ZEPHYRIA', name: 'Zephyria', x: 140, y: 460, labelX: 40, labelY: 540, terrain: TERRAIN.ZEPHYRIA } // Island!
        ];

        function getVoronoiCountry(x, y) {
            let closest = null;
            let minDist = Infinity;
            countries.forEach(c => {
                let noise = Math.sin(x * 0.05) * Math.cos(y * 0.05) * 40; 
                let d = Math.sqrt(Math.pow(c.x - x, 2) + Math.pow(c.y - y, 2)) + noise;
                if (d < minDist) {
                    minDist = d;
                    closest = c;
                }
            });
            return closest;
        }

        const zoomSlider = document.getElementById('zoomSlider');
        zoomSlider.addEventListener('input', (e) => {
            zoom = parseFloat(e.target.value);
            render();
        });

        // Initialize grid
        function initGrid() {
            const rows = Math.ceil(canvas.height / h) + 1;
            const cols = Math.ceil(canvas.width / (sideLength / 2)) + 2;
            
            // 1. Generate Triangles
            for (let row = 0; row < rows; row++) {
                for (let col = 0; col < cols; col++) {
                    const isPointingUp = (row + col) % 2 === 0;
                    
                    let x1, y1, x2, y2, x3, y3;
                    
                    if (isPointingUp) {
                        x1 = col * sideLength / 2;
                        y1 = row * h + h;
                        x2 = x1 + sideLength;
                        y2 = y1;
                        x3 = x1 + sideLength / 2;
                        y3 = row * h;
                    } else {
                        x1 = col * sideLength / 2;
                        y1 = row * h;
                        x2 = x1 + sideLength;
                        y2 = y1;
                        x3 = x1 + sideLength / 2;
                        y3 = row * h + h;
                    }

                    // Calculate true center of the triangle
                    let cx = (x1 + x2 + x3) / 3;
                    let cy = (y1 + y2 + y3) / 3;

                    // Procedural map generation based on coordinates
                    let terrain = TERRAIN.OCEAN;
                    
                    // Main continent
                    let distFromMain = Math.sqrt(Math.pow(cx - 400, 2) + Math.pow(cy - 300, 2));
                    let angleMain = Math.atan2(cy - 300, cx - 400);
                    let mainRadius = 180 
                        + 35 * Math.sin(angleMain) 
                        + 25 * Math.cos(2 * angleMain) 
                        + 20 * Math.sin(3 * angleMain) 
                        + 15 * Math.cos(5 * angleMain);

                    // Zephyria Island
                    let distFromIsland = Math.sqrt(Math.pow(cx - 140, 2) + Math.pow(cy - 460, 2));
                    let angleIsland = Math.atan2(cy - 460, cx - 140);
                    let islandRadius = 70 
                        + 15 * Math.sin(angleIsland * 2) 
                        + 10 * Math.cos(angleIsland * 3);

                    if (distFromMain < mainRadius || distFromIsland < islandRadius) {
                        let country = getVoronoiCountry(cx, cy);
                        terrain = country.terrain;
                    }

                    // Generate mountain ranges using coherent noise 
                    if (terrain !== TERRAIN.OCEAN) {
                        let mNoise1 = Math.sin(cx * 0.02 + Math.cos(cy * 0.025) * 2);
                        let mNoise2 = Math.cos(cx * 0.015 - cy * 0.02);
                        
                        // Create distinct ridges when mNoise1 is close to 0, masked by mNoise2 to create patches
                        if (Math.abs(mNoise1) < 0.15 && mNoise2 > 0) {
                            // Add a tiny bit of random chance to make the ridge edges look natural and rocky
                            if (Math.random() > 0.2) {
                                terrain = TERRAIN.MOUNTAIN;
                            }
                        }
                    }

                    if (terrain === TERRAIN.OCEAN) {
                        continue; // Skip generating and rendering ocean triangles to save resources
                    }

                    const tri = {
                        id: `${row}-${col}`,
                        points: [
                            {x: x1, y: y1},
                            {x: x2, y: y2},
                            {x: x3, y: y3}
                        ],
                        terrain: terrain,
                        center: {
                            x: cx,
                            y: cy
                        }
                    };
                    triangles.push(tri);
                    
                    // Add edges
                    addEdge(tri.points[0], tri.points[1], tri);
                    addEdge(tri.points[1], tri.points[2], tri);
                    addEdge(tri.points[2], tri.points[0], tri);
                }
            }
            
            // 2. Procedural Continuous Rivers
            // Build adjacency list
            triangles.forEach(t => t.neighbors = []);
            edges.forEach(e => {
                if (e.triangles.length === 2) {
                    e.triangles[0].neighbors.push(e.triangles[1]);
                    e.triangles[1].neighbors.push(e.triangles[0]);
                }
            });

            // Generate rivers flowing outwards, capped at 8% of landmass
            let maxRiverTriangles = triangles.length * 0.08;
            let currentRiverTriangles = 0;

            for(let i = 0; i < 500; i++) {
                if (currentRiverTriangles >= maxRiverTriangles) break;

                let startTri = triangles[Math.floor(Math.random() * triangles.length)];
                if (startTri.terrain === TERRAIN.MOUNTAIN || startTri.terrain === TERRAIN.RIVER) continue;
                
                let currentTri = startTri;
                let length = 0;
                let maxLength = 10 + Math.floor(Math.random() * 20); // Random length between 10 and 30
                while(currentTri && length < maxLength) {
                    if (currentRiverTriangles >= maxRiverTriangles) break;

                    if (currentTri.terrain !== TERRAIN.RIVER) {
                        currentTri.terrain = TERRAIN.RIVER;
                        currentRiverTriangles++;
                    }
                    length++;
                    
                    if (currentTri.neighbors.length < 3) break; // Reached coast/ocean

                    
                    let validNeighbors = currentTri.neighbors.filter(n => 
                        n.terrain !== TERRAIN.MOUNTAIN && n.terrain !== TERRAIN.RIVER
                    );
                    
                    if (validNeighbors.length === 0) break;
                    
                    // Bias towards outward flow
                    validNeighbors.sort((a, b) => {
                        let distA = Math.pow(a.center.x - 400, 2) + Math.pow(a.center.y - 300, 2);
                        let distB = Math.pow(b.center.x - 400, 2) + Math.pow(b.center.y - 300, 2);
                        return distB - distA; 
                    });
                    
                    currentTri = validNeighbors[0];
                    if (validNeighbors.length > 1 && Math.random() > 0.6) {
                        currentTri = validNeighbors[1];
                    }
                }
            }

            // 3. Procedural Rivers & Impassable Edges
            edges.forEach(edge => {
                // If an edge only connects to one triangle, it borders the un-generated ocean
                edge.isImpassable = edge.triangles.length === 1;
                // Mark edge as river if it borders or intersects a river triangle
                if (edge.triangles.some(t => t.terrain === TERRAIN.RIVER)) {
                    edge.isRiver = true;
                }
            });

            // 3. Mountains block 2 out of 3 edges randomly to create mazes
            triangles.forEach(tri => {
                if (tri.terrain === TERRAIN.MOUNTAIN) {
                    let triEdges = edges.filter(e => e.triangles.includes(tri));
                    triEdges.sort(() => Math.random() - 0.5);
                    if (triEdges.length > 0) triEdges[0].isImpassable = true;
                    if (triEdges.length > 1) triEdges[1].isImpassable = true;
                }
            });

            // City Placement
            let numCompanies = 12;
            let minCityDist = 35;
            let allCities = [];
            
            countries.forEach(country => {
                let validTris = triangles.filter(t => t.terrain === country.terrain && t.neighbors.some(n => n.terrain !== TERRAIN.RIVER));
                let coastalTris = validTris.filter(t => t.neighbors.some(n => n.terrain === TERRAIN.OCEAN));
                
                let port1, port2;
                if (coastalTris.length >= 2) {
                    if (country.id === 'LUNARA') {
                        let mx = 480, my = 320;
                        coastalTris.sort((a,b) => ( (a.center.x-mx)**2 + (a.center.y-my)**2 ) - ( (b.center.x-mx)**2 + (b.center.y-my)**2 ));
                        port1 = coastalTris[0];
                        for(let i=1; i<coastalTris.length; i++) {
                            let cand = coastalTris[i];
                            if ( Math.sqrt((cand.center.x-port1.center.x)**2 + (cand.center.y-port1.center.y)**2) >= minCityDist ) {
                                port2 = cand;
                                break;
                            }
                        }
                    } else {
                        let maxD = -1;
                        for(let i=0; i<coastalTris.length; i++) {
                            for(let j=i+1; j<coastalTris.length; j++) {
                                let d = (coastalTris[i].center.x-coastalTris[j].center.x)**2 + (coastalTris[i].center.y-coastalTris[j].center.y)**2;
                                if (d > maxD) { maxD = d; port1 = coastalTris[i]; port2 = coastalTris[j]; }
                            }
                        }
                    }
                    if (port1) { port1.isPort = true; port1.isCity = true; port1.country = country; allCities.push(port1); }
                    if (port2) { port2.isPort = true; port2.isCity = true; port2.country = country; allCities.push(port2); }
                }
                
                validTris.sort((a, b) => {
                    let distA = Math.pow(a.center.x - country.x, 2) + Math.pow(a.center.y - country.y, 2);
                    let distB = Math.pow(b.center.x - country.x, 2) + Math.pow(b.center.y - country.y, 2);
                    return distA - distB;
                });
                
                let countryCities = [port1, port2].filter(x => x);
                
                for (let i = 0; i < validTris.length; i++) {
                    if (countryCities.length >= numCompanies) break;
                    let candidate = validTris[i];
                    if (candidate.isPort) continue;
                    
                    let tooClose = false;
                    for (let city of countryCities) {
                        if (Math.sqrt(Math.pow(candidate.center.x - city.center.x, 2) + Math.pow(candidate.center.y - city.center.y, 2)) < minCityDist) {
                            tooClose = true;
                            break;
                        }
                    }
                    if (!tooClose) {
                        candidate.isCity = true;
                        candidate.country = country;
                        countryCities.push(candidate);
                        allCities.push(candidate);
                    }
                }
                
                // Categorize
                countryCities.forEach(city => {
                    let madeBig = false;
                    if (Math.random() > 0.75) {
                        let validNeighbor = city.neighbors.find(n => n.terrain === country.terrain && !n.isCity);
                        if (validNeighbor) {
                            validNeighbor.isCity = true;
                            validNeighbor.country = country;
                            madeBig = true;
                        }
                    }
                    if (madeBig) {
                        city.isBigCity = true;
                        city.hasAirport = true;
                    } else {
                        city.isSmallCity = true;
                    }
                });
            });
            
            // Dijkstra railroads
            let bigCities = allCities.filter(c => c.isBigCity);
            let smallCities = allCities.filter(c => c.isSmallCity);
            
            let graph = {};
            edges.forEach(edge => {
                if (edge.isImpassable) return;
                let p1Id = edge.p1.x.toFixed(1) + ',' + edge.p1.y.toFixed(1);
                let p2Id = edge.p2.x.toFixed(1) + ',' + edge.p2.y.toFixed(1);
                if (!graph[p1Id]) graph[p1Id] = [];
                if (!graph[p2Id]) graph[p2Id] = [];
                
                let cost = 1 + (Math.random() * 0.01); // microscopic noise to prevent parallel DNA
                if (edge.isRiver) cost = 3;
                if (edge.triangles.some(t => t.terrain === TERRAIN.MOUNTAIN)) cost = 1.5;
                
                graph[p1Id].push({node: p2Id, cost: cost, edge: edge});
                graph[p2Id].push({node: p1Id, cost: cost, edge: edge});
            });
            
            function shortestPath(startId, endId) {
                let dist = {}; let prev = {}; let pq = [];
                for (let v in graph) { dist[v] = Infinity; prev[v] = null; }
                dist[startId] = 0;
                pq.push({node: startId, d: 0});
                
                while(pq.length > 0) {
                    pq.sort((a,b) => a.d - b.d);
                    let u = pq.shift().node;
                    if (u === endId) break;
                    
                    for (let neighbor of graph[u]) {
                        let alt = dist[u] + neighbor.cost;
                        if (alt < dist[neighbor.node]) {
                            dist[neighbor.node] = alt;
                            prev[neighbor.node] = neighbor;
                            pq.push({node: neighbor.node, d: alt});
                        }
                    }
                }
                
                let curr = endId;
                while (prev[curr]) {
                    prev[curr].edge.hasRailroad = true;
                    curr = prev[curr].node === curr ? null : prev[curr].edge.p1.x.toFixed(1) + ',' + prev[curr].edge.p1.y.toFixed(1) === curr ? prev[curr].edge.p2.x.toFixed(1) + ',' + prev[curr].edge.p2.y.toFixed(1) : prev[curr].edge.p1.x.toFixed(1) + ',' + prev[curr].edge.p1.y.toFixed(1); // simplified tracking
                    
                    // Simple path trace
                    let edge = prev[curr];
                }
            }
            
            // Simple direct greedy pathing for railroad to prevent huge hangs
            smallCities.forEach(sc => {
                let closestBig = null; let minDist = Infinity;
                bigCities.forEach(bc => {
                    if (bc.country === sc.country) {
                        let d = Math.pow(bc.center.x - sc.center.x, 2) + Math.pow(bc.center.y - sc.center.y, 2);
                        if (d < minDist) { minDist = d; closestBig = bc; }
                    }
                });
                if (closestBig) {
                    // Start from small city center and greedy walk to big city center
                    let currTri = sc;
                    for (let i = 0; i < 100; i++) {
                        let bestN = null; let bDist = Infinity; let bestEdge = null;
                        
                        let relevantEdges = edges.filter(e => e.triangles.includes(currTri));
                        relevantEdges.forEach(e => {
                            if (e.isImpassable) return;
                            let otherTri = e.triangles.find(t => t !== currTri);
                            if (otherTri) {
                                let d = Math.pow(otherTri.center.x - closestBig.center.x, 2) + Math.pow(otherTri.center.y - closestBig.center.y, 2);
                                if (d < bDist) { bDist = d; bestN = otherTri; bestEdge = e; }
                            }
                        });
                        
                        if (bestEdge) {
                            bestEdge.hasRailroad = true;
                            currTri = bestN;
                        }
                        if (currTri === closestBig) break;
                    }
                }
            });

        }

        // Helper to add unique edges
        function addEdge(p1, p2, tri) {
            // Standardize edge direction to find duplicates
            let xA = Math.min(p1.x, p2.x);
            let xB = Math.max(p1.x, p2.x);
            let yA = p1.x < p2.x ? p1.y : p2.y;
            let yB = p1.x < p2.x ? p2.y : p1.y;
            
            if (p1.x === p2.x) {
                yA = Math.min(p1.y, p2.y);
                yB = Math.max(p1.y, p2.y);
            }

            const id = `${xA.toFixed(1)},${yA.toFixed(1)}-${xB.toFixed(1)},${yB.toFixed(1)}`;
            
            let existingEdge = edges.find(e => e.id === id);
            if (!existingEdge) {
                edges.push({
                    id: id,
                    p1: {x: xA, y: yA},
                    p2: {x: xB, y: yB},
                    triangles: [tri],
                    hasRailroad: false,
                    isRiver: false,
                    isHovered: false
                });
            } else {
                existingEdge.triangles.push(tri);
            }
        }

        // Draw everything
        function render() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            ctx.save();
            ctx.translate(canvas.width / 2 + panX, canvas.height / 2 + panY);
            ctx.scale(zoom, zoom);
            ctx.translate(-canvas.width / 2, -canvas.height / 2);
            
            // 1. Draw Triangles
            triangles.forEach(tri => {
                ctx.beginPath();
                ctx.moveTo(tri.points[0].x, tri.points[0].y);
                ctx.lineTo(tri.points[1].x, tri.points[1].y);
                ctx.lineTo(tri.points[2].x, tri.points[2].y);
                ctx.closePath();
                ctx.fillStyle = (tri.isCity && tri.country) ? tri.country.cityColor : tri.terrain.color;
                ctx.fill();
                ctx.strokeStyle = 'rgba(0,0,0,0.03)'; // Made outlines more subtle
                ctx.lineWidth = 1;
                ctx.stroke();

                if (tri.isPort) {
                    let timePulse = Date.now() / 300;
                    let pulseRadius = 3.5 + Math.sin(timePulse) * 1.5;
                    ctx.beginPath();
                    ctx.arc(tri.center.x, tri.center.y, pulseRadius, 0, Math.PI * 2);
                    ctx.fillStyle = '#ff0000'; 
                    ctx.fill();
                    ctx.strokeStyle = '#ffffff'; 
                    ctx.lineWidth = 1.5;
                    ctx.stroke();
                    
                    ctx.beginPath();
                    ctx.moveTo(tri.center.x - 3, tri.center.y);
                    ctx.lineTo(tri.center.x + 3, tri.center.y);
                    ctx.moveTo(tri.center.x, tri.center.y - 3);
                    ctx.lineTo(tri.center.x, tri.center.y + 3);
                    ctx.strokeStyle = '#ffffff';
                    ctx.lineWidth = 1.5;
                    ctx.stroke();
                }

            });

            // 2. Draw Edges (Rivers & Roads)
            edges.forEach(edge => {
                const isImpassable = edge.isImpassable;
                
                if (edge.hasRailroad) {
                    ctx.beginPath();
                    ctx.moveTo(edge.p1.x, edge.p1.y);
                    ctx.lineTo(edge.p2.x, edge.p2.y);
                    ctx.strokeStyle = '#ecf0f1'; // White road
                    ctx.lineWidth = 1;
                    ctx.stroke();
                } else if (edge.isRiver && !isImpassable) {
                    ctx.beginPath();
                    ctx.moveTo(edge.p1.x, edge.p1.y);
                    ctx.lineTo(edge.p2.x, edge.p2.y);
                    ctx.strokeStyle = '#3498db'; // Blue river
                    ctx.lineWidth = 1;
                    ctx.stroke();
                } else if (edge.isHovered && !isImpassable) {
                    ctx.beginPath();
                    ctx.moveTo(edge.p1.x, edge.p1.y);
                    ctx.lineTo(edge.p2.x, edge.p2.y);
                    ctx.strokeStyle = edge.isRiver ? '#f1c40f' : '#333333'; // Preview color
                    ctx.lineWidth = 1.5;
                    ctx.stroke();
                }
            });
            
            // Draw nodes
            edges.forEach(edge => {
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

            // Draw country names
            ctx.font = 'bold 26px "Segoe UI", Tahoma, Geneva, Verdana, sans-serif';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.lineWidth = 4;
            ctx.strokeStyle = 'rgba(0, 0, 0, 0.75)';
            ctx.fillStyle = 'rgba(255, 255, 255, 0.95)';

            const regions = countries;

            regions.forEach(region => {
                // Draw connecting line to region center
                ctx.beginPath();
                // removed line to center to keep it over ocean
                // ctx.lineTo(region.x, region.y);
                ctx.strokeStyle = 'rgba(255, 255, 255, 0.4)';
                ctx.lineWidth = 2;
                ctx.stroke();
                
                // Draw small dot at the center
                ctx.beginPath();
                // removed dot at center
                ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
                ctx.fill();

                // Draw text at the label position
                ctx.lineWidth = 4;
                ctx.strokeStyle = 'rgba(0, 0, 0, 0.75)';
                ctx.fillStyle = 'rgba(255, 255, 255, 0.95)';
                ctx.strokeText(region.name, region.labelX, region.labelY);
                ctx.fillText(region.name, region.labelX, region.labelY);
            });
            
            ctx.restore();
        }

        // Distance from point to line segment
        function distToSegment(p, v, w) {
            let l2 = Math.pow(v.x - w.x, 2) + Math.pow(v.y - w.y, 2);
            if (l2 === 0) return Math.sqrt(Math.pow(p.x - v.x, 2) + Math.pow(p.y - v.y, 2));
            let t = ((p.x - v.x) * (w.x - v.x) + (p.y - v.y) * (w.y - v.y)) / l2;
            t = Math.max(0, Math.min(1, t));
            return Math.sqrt(Math.pow(p.x - (v.x + t * (w.x - v.x)), 2) + Math.pow(p.y - (v.y + t * (w.y - v.y)), 2));
        }

        // Get closest edge to mouse
        function getClosestEdge(mx, my) {
            let closest = null;
            let minDist = 4 / zoom; // Hitbox radius

            edges.forEach(edge => {
                if (edge.isImpassable) return;

                let d = distToSegment({x: mx, y: my}, edge.p1, edge.p2);
                if (d < minDist) {
                    minDist = d;
                    closest = edge;
                }
            });
            return closest;
        }

        // Event Listeners
        canvas.addEventListener('mousedown', (e) => {
            isDragging = true;
            hasDragged = false;
            dragStartX = e.clientX;
            dragStartY = e.clientY;
        });

        canvas.addEventListener('mouseup', () => {
            isDragging = false;
        });

        canvas.addEventListener('mouseleave', () => {
            isDragging = false;
        });

        canvas.addEventListener('mousemove', (e) => {
            if (isDragging) {
                let dx = e.clientX - dragStartX;
                let dy = e.clientY - dragStartY;
                if (Math.abs(dx) > 2 || Math.abs(dy) > 2) hasDragged = true;
                panX += dx;
                panY += dy;
                dragStartX = e.clientX;
                dragStartY = e.clientY;
                render();
                return;
            }

            const rect = canvas.getBoundingClientRect();
            let mx = e.clientX - rect.left;
            let my = e.clientY - rect.top;

            // Apply inverse zoom and pan
            mx = (mx - canvas.width / 2 - panX) / zoom + canvas.width / 2;
            my = (my - canvas.height / 2 - panY) / zoom + canvas.height / 2;

            let redraw = false;
            
            const closest = getClosestEdge(mx, my);
            
            edges.forEach(edge => {
                if (edge.isHovered && edge !== closest) {
                    edge.isHovered = false;
                    redraw = true;
                }
            });

            if (closest && !closest.isHovered && !closest.hasRailroad) {
                closest.isHovered = true;
                redraw = true;
            }

            if (redraw) render();
        });

        canvas.addEventListener('click', (e) => {
            if (hasDragged) {
                hasDragged = false;
                return;
            }

            const rect = canvas.getBoundingClientRect();
            let mx = e.clientX - rect.left;
            let my = e.clientY - rect.top;

            // Apply inverse zoom and pan
            mx = (mx - canvas.width / 2 - panX) / zoom + canvas.width / 2;
            my = (my - canvas.height / 2 - panY) / zoom + canvas.height / 2;

            const closest = getClosestEdge(mx, my);
            if (closest && !closest.hasRailroad) {
                closest.hasRailroad = true;
                closest.isHovered = false;
                
                // Calculate cost
                let cost = 1;
                if (closest.isRiver) cost = 3; // Bridge cost 3x
                
                // If adjacent to mountain, cost increases
                if (closest.triangles.some(t => t.terrain === TERRAIN.MOUNTAIN)) {
                    cost += 2; 
                }

                totalCost += cost;
                document.getElementById('cost-display').innerText = `$${totalCost}M`;
                
                render();
            }
        });

        function clearRoads() {
            edges.forEach(e => e.hasRailroad = false);
            totalCost = 0;
            document.getElementById('cost-display').innerText = `$0M`;
            render();
        }

        // Run
        initGrid();
        render();

    