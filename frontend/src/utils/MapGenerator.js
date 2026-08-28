// Simple Linear Congruential Generator (LCG) for deterministic randomization
export function seededRandom(seedStr) {
    let seed = 0;
    for (let i = 0; i < seedStr.length; i++) {
        seed = (seed * 31 + seedStr.charCodeAt(i)) >>> 0;
    }
    
    return function() {
        seed = (seed * 1664525 + 1013904223) >>> 0;
        return seed / 4294967296;
    };
}

// Terrain Types
export const TERRAIN = {
    OCEAN: { color: '#2c3e50', name: 'Ocean' },
    MOUNTAIN: { color: '#555555', texture: 'rock', name: 'Impassable Peaks' },
    RIVER: { color: '#3498db', name: 'River' },
    TERRANOVA: { color: '#27ae60', texture: 'grass', name: 'Terranova (Plains)' },
    SOLHAVEN: { color: '#f1c40f', texture: 'sand', name: 'Solhaven' },
    KORVATH: { color: '#16a085', texture: 'rock', name: 'Korvath' },
    VALDORIA: { color: '#f39c12', texture: 'sand', name: 'Valdoria (Desert)' },
    LUNARA: { color: '#d35400', texture: 'rock', name: 'Lunara' },
    NORDVIK: { color: '#aed6f1', texture: 'snow', name: 'Nordvik (Tundra)' },
    ZEPHYRIA: { color: '#228b22', texture: 'grass', name: 'Zephyria' },
    DRAKMOOR: { color: '#7f8c8d', texture: 'rock', name: 'Drakmoor (Mountains)' },
    CITY: { color: '#ffffff', name: 'Company City' } 
};

export const countriesDef = [
    { id: 'TERRANOVA', name: 'Terranova', x: 480, y: 320, labelX: 740, labelY: 350, terrain: TERRAIN.TERRANOVA, cityColor: '#ae2775' },
    { id: 'SOLHAVEN', name: 'Solhaven', x: 420, y: 440, labelX: 620, labelY: 580, terrain: TERRAIN.SOLHAVEN, cityColor: '#000080' },
    { id: 'KORVATH', name: 'Korvath', x: 320, y: 420, labelX: 320, labelY: 580, terrain: TERRAIN.KORVATH, cityColor: '#a01631' },
    { id: 'VALDORIA', name: 'Valdoria', x: 280, y: 300, labelX: 80, labelY: 250, terrain: TERRAIN.VALDORIA, cityColor: '#000080' },
    { id: 'NORDVIK', name: 'Nordvik', x: 340, y: 180, labelX: 250, labelY: 40, terrain: TERRAIN.NORDVIK, cityColor: '#000080' },
    { id: 'ZEPHYRIA', name: 'Zephyria', x: 450, y: 160, labelX: 550, labelY: 40, terrain: TERRAIN.ZEPHYRIA, cityColor: '#8b228b' },
    { id: 'DRAKMOOR', name: 'Drakmoor', x: 520, y: 220, labelX: 720, labelY: 130, terrain: TERRAIN.DRAKMOOR, cityColor: '#e74c3c' },
    { id: 'LUNARA', name: 'Lunara', x: 140, y: 460, labelX: 40, labelY: 540, terrain: TERRAIN.LUNARA, cityColor: '#000080' } 
];

function getVoronoiCountry(x, y) {
    let closest = null;
    let minDist = Infinity;
    countriesDef.forEach(c => {
        let noise = Math.sin(x * 0.05) * Math.cos(y * 0.05) * 40; 
        let d = Math.sqrt(Math.pow(c.x - x, 2) + Math.pow(c.y - y, 2)) + noise;
        if (d < minDist) {
            minDist = d;
            closest = c;
        }
    });
    return closest;
}

// Distance from point to line segment
export function distToSegment(p, v, w) {
    let l2 = Math.pow(v.x - w.x, 2) + Math.pow(v.y - w.y, 2);
    if (l2 === 0) return Math.sqrt(Math.pow(p.x - v.x, 2) + Math.pow(p.y - v.y, 2));
    let t = ((p.x - v.x) * (w.x - v.x) + (p.y - v.y) * (w.y - v.y)) / l2;
    t = Math.max(0, Math.min(1, t));
    return Math.sqrt(Math.pow(p.x - (v.x + t * (w.x - v.x)), 2) + Math.pow(p.y - (v.y + t * (w.y - v.y)), 2));
}

export function generateMapData(seedStr = 'default', width = 800, height = 600) {
    const rnd = seededRandom(seedStr);
    
    // Grid properties
    const sideLength = 7;
    const h = sideLength * Math.sqrt(3) / 2; // height of an equilateral triangle
    
    let triangles = []; 
    let edges = [];     
    let edgeMap = new Map();

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
        
        let existingEdge = edgeMap.get(id);
        if (!existingEdge) {
            existingEdge = {
                id: id,
                p1: {x: xA, y: yA},
                p2: {x: xB, y: yB},
                triangles: [tri],
                hasRailroad: false,
                isRiver: false,
                isHovered: false
            };
            edges.push(existingEdge);
            edgeMap.set(id, existingEdge);
        } else {
            existingEdge.triangles.push(tri);
        }
    }

    const rows = Math.ceil(height / h) + 1;
    const cols = Math.ceil(width / (sideLength / 2)) + 2;
    
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

            // Lunara Island
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
                let isMountain = false;
                
                let mNoise1 = Math.sin(cx * 0.02 + Math.cos(cy * 0.025) * 2);
                let mNoise2 = Math.cos(cx * 0.015 - cy * 0.02);
                
                // Create distinct ridges when mNoise1 is close to 0, masked by mNoise2 to create patches
                if (Math.abs(mNoise1) < 0.15 && mNoise2 > 0) {
                    // Add a tiny bit of random chance to make the ridge edges look natural and rocky
                    if (rnd() > 0.2) {
                        isMountain = true;
                    }
                }

                // Lunara South Coast Mountains
                if (terrain === TERRAIN.LUNARA) {
                    // Southern coast: angle between roughly 0 (East) and PI (West)
                    if (angleIsland > 0.1 && angleIsland < Math.PI - 0.2) {
                        // 2-3 triangles thick is ~20-30 pixels from the edge (islandRadius)
                        if (islandRadius - distFromIsland < 32 && islandRadius - distFromIsland >= 0) {
                            if (rnd() > 0.15) {
                                isMountain = true;
                            }
                        }
                    }
                }

                if (isMountain) {
                    terrain = TERRAIN.MOUNTAIN;
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

        let startTri = triangles[Math.floor(rnd() * triangles.length)];
        if (startTri.terrain === TERRAIN.MOUNTAIN || startTri.terrain === TERRAIN.RIVER) continue;
        
        let currentTri = startTri;
        let length = 0;
        let maxLength = 10 + Math.floor(rnd() * 20); // Random length between 10 and 30
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
            if (validNeighbors.length > 1 && rnd() > 0.6) {
                currentTri = validNeighbors[1];
            }
        }
    }

    // 3. Procedural Rivers & Impassable Edges
    edges.forEach(edge => {
        // If an edge only connects to one triangle, it borders the un-generated ocean
        edge.isImpassable = edge.triangles.length === 1;
        // Mark edge as river (requiring a bridge) ONLY if it crosses the river, 
        // meaning BOTH sides of the edge are River triangles.
        if (edge.triangles.length === 2 && edge.triangles.every(t => t.terrain === TERRAIN.RIVER)) {
            edge.isRiver = true;
        }
    });

    // 3. Mountains: every mountain should have exactly 1 passible edge to create mazes
    edges.forEach(e => {
        if (e.triangles.some(t => t.terrain === TERRAIN.MOUNTAIN)) {
            e.isImpassable = true;
        }
    });

    let mountains = triangles.filter(t => t.terrain === TERRAIN.MOUNTAIN);
    mountains.sort(() => rnd() - 0.5); // Shuffle for random maze generation

    mountains.forEach(m => {
        let mEdges = edges.filter(e => e.triangles.includes(m));
        let passibleEdges = mEdges.filter(e => !e.isImpassable);
        
        if (passibleEdges.length === 0) {
            let validEdges = mEdges.filter(e => {
                let other = e.triangles.find(t => t !== m);
                if (!other) return true; 
                if (other.terrain !== TERRAIN.MOUNTAIN) return true; 
                
                let otherPassible = edges.filter(oe => oe.triangles.includes(other) && !oe.isImpassable).length;
                return otherPassible === 0;
            });

            let edgeToMakePassible;
            if (validEdges.length > 0) {
                edgeToMakePassible = validEdges[Math.floor(rnd() * validEdges.length)];
            } else {
                edgeToMakePassible = mEdges[Math.floor(rnd() * mEdges.length)];
            }
            
            if (edgeToMakePassible) {
                edgeToMakePassible.isImpassable = false;
            }
        }
    });

    function getDist(startTri, conditionFn, maxD) {
        let queue = [{ tri: startTri, d: 0 }];
        let visited = new Set([startTri.id]);
        while (queue.length > 0) {
            let { tri, d } = queue.shift();
            if (conditionFn(tri)) return d;
            if (d < maxD) {
                for (let n of tri.neighbors) {
                    if (!visited.has(n.id)) {
                        visited.add(n.id);
                        queue.push({ tri: n, d: d + 1 });
                    }
                }
            }
        }
        return Infinity;
    }

    function isTrapped(startTri, minSize) {
        let queue = [startTri];
        let visited = new Set([startTri.id]);
        let count = 0;
        while (queue.length > 0 && count < minSize) {
            let curr = queue.shift();
            count++;
            for (let n of curr.neighbors) {
                if (n.terrain !== TERRAIN.MOUNTAIN && n.terrain !== TERRAIN.OCEAN && !visited.has(n.id)) {
                    visited.add(n.id);
                    queue.push(n);
                }
            }
        }
        return count < minSize;
    }

    // 4. City placement (1 city for each company, 12 companies per country)
    // Positions are static within countries, distributed evenly
    countriesDef.forEach((country) => {
        let validTris = triangles.filter(t => {
            if (t.terrain !== country.terrain) return false;
            if (!t.neighbors.some(n => n.terrain !== TERRAIN.RIVER)) return false; // Rivers should not surround them completely
            if (t.neighbors.filter(n => n.terrain === TERRAIN.MOUNTAIN).length === 3) return false; // Shouldn't be fully enclosed by mountains
            if (isTrapped(t, 25)) return false; // Must not be trapped in a tiny pocket of land
            return true;
        });
        
        // Sort by distance to country center to have a deterministic "static" position
        validTris.sort((a, b) => {
            let distA = Math.pow(a.center.x - country.x, 2) + Math.pow(a.center.y - country.y, 2);
            let distB = Math.pow(b.center.x - country.x, 2) + Math.pow(b.center.y - country.y, 2);
            return distA - distB;
        });
        
        let numCompanies = 12;
        let cities = [];
        let minCityDist = 35; // Minimum pixel distance to spread cities out
        
        let allCoastalTris = validTris.filter(t => t.neighbors.length < 3);
        
        // Filter ports based on rules
        let coastalTris = allCoastalTris.filter(t => {
            if (country.id !== 'LUNARA') {
                let distToBorder = getDist(t, n => n.terrain !== country.terrain && n.terrain !== TERRAIN.OCEAN && n.terrain !== TERRAIN.MOUNTAIN && n.terrain !== TERRAIN.RIVER, 2);
                if (distToBorder <= 2) return false;
            }
            
            let distToMountain = getDist(t, n => n.terrain === TERRAIN.MOUNTAIN, 3);
            if (distToMountain <= 3) return false;
            
            return true;
        });
        
        // Fallback to less strict rules if not enough coastal triangles
        if (coastalTris.length < 2) {
            coastalTris = allCoastalTris.filter(t => {
                if (country.id !== 'LUNARA') {
                    let distToBorder = getDist(t, n => n.terrain !== country.terrain && n.terrain !== TERRAIN.OCEAN && n.terrain !== TERRAIN.MOUNTAIN && n.terrain !== TERRAIN.RIVER, 1);
                    if (distToBorder <= 1) return false;
                }
                let distToMountain = getDist(t, n => n.terrain === TERRAIN.MOUNTAIN, 2);
                if (distToMountain <= 2) return false;
                return true;
            });
        }
        // Ultimate fallback
        if (coastalTris.length < 2) {
            coastalTris = allCoastalTris;
        }

        let port1, port2;
        if (coastalTris.length >= 2) {
            if (country.id === 'LUNARA') {
                let lunaraValid = coastalTris.filter(t => {
                    let parts = t.id.split('-');
                    let r = parseInt(parts[0]);
                    let c = parseInt(parts[1]);
                    return r >= 65 && r <= 71 && c >= 40 && c <= 60;
                });
                
                // Fallback just in case generation shifts
                if (lunaraValid.length < 2) lunaraValid = coastalTris;
                
                let mx = 480, my = 320;
                lunaraValid.sort((a,b) => ( (a.center.x-mx)**2 + (a.center.y-my)**2 ) - ( (b.center.x-mx)**2 + (b.center.y-my)**2 ));
                port1 = lunaraValid[0];
                for(let i=1; i<lunaraValid.length; i++) {
                    let cand = lunaraValid[i];
                    if ( Math.sqrt((cand.center.x-port1.center.x)**2 + (cand.center.y-port1.center.y)**2) >= minCityDist ) {
                        port2 = cand;
                        break;
                    }
                }
            } else {
                // Find borders (the furthest apart points on the full coast)
                let maxD = -1;
                let b1, b2;
                for(let i=0; i<allCoastalTris.length; i++) {
                    for(let j=i+1; j<allCoastalTris.length; j++) {
                        let d = (allCoastalTris[i].center.x-allCoastalTris[j].center.x)**2 + (allCoastalTris[i].center.y-allCoastalTris[j].center.y)**2;
                        if (d > maxD) { maxD = d; b1 = allCoastalTris[i]; b2 = allCoastalTris[j]; }
                    }
                }
                
                if (b1 && b2) {
                    let t1x = b1.center.x + (b2.center.x - b1.center.x) / 3;
                    let t1y = b1.center.y + (b2.center.y - b1.center.y) / 3;
                    
                    let t2x = b1.center.x + (b2.center.x - b1.center.x) * 2 / 3;
                    let t2y = b1.center.y + (b2.center.y - b1.center.y) * 2 / 3;
                    
                    let minD1 = Infinity, minD2 = Infinity;
                    for(let cand of coastalTris) {
                        let d1 = (cand.center.x - t1x)**2 + (cand.center.y - t1y)**2;
                        if (d1 < minD1) { minD1 = d1; port1 = cand; }
                    }
                    
                    for(let cand of coastalTris) {
                        if (cand === port1) continue;
                        let d2 = (cand.center.x - t2x)**2 + (cand.center.y - t2y)**2;
                        if (d2 < minD2) { minD2 = d2; port2 = cand; }
                    }
                }
            }
        }

        let candidatesToProcess = [];
        if (port1) { port1.isPort = true; candidatesToProcess.push(port1); }
        if (port2) { port2.isPort = true; candidatesToProcess.push(port2); }
        
        candidatesToProcess.forEach(candidate => {
            candidate.terrain = TERRAIN.CITY;
            candidate.country = country;
            cities.push(candidate);
            
            let madeBig = false;
            if (rnd() > 0.75) {
                let validNeighbor = candidate.neighbors.find(n => n.terrain === country.terrain);
                if (validNeighbor) {
                    validNeighbor.terrain = TERRAIN.CITY;
                    validNeighbor.country = country;
                    madeBig = true;
                }
            }

            if (madeBig) {
                candidate.isBigCity = true;
                candidate.hasAirport = true;
            } else {
                candidate.isSmallCity = true;
            }
        });
        
        for (let i = 0; i < validTris.length; i++) {
            if (cities.length >= numCompanies) break;
            
            let candidate = validTris[i];
            if (candidate.terrain === TERRAIN.CITY) continue;

            let tooClose = false;
            for (let city of cities) {
                let dx = candidate.center.x - city.center.x;
                let dy = candidate.center.y - city.center.y;
                if (Math.sqrt(dx * dx + dy * dy) < minCityDist) {
                    tooClose = true;
                    break;
                }
            }
            
            if (!tooClose) {
                candidate.terrain = TERRAIN.CITY;
                candidate.country = country;
                cities.push(candidate);
                
                let madeBig = false;
                if (rnd() > 0.75) {
                    let validNeighbor = candidate.neighbors.find(n => n.terrain === country.terrain);
                    if (validNeighbor) {
                        validNeighbor.terrain = TERRAIN.CITY;
                        validNeighbor.country = country;
                        madeBig = true;
                    }
                }

                if (madeBig) {
                    candidate.isBigCity = true;
                    candidate.hasAirport = true;
                } else {
                    candidate.isSmallCity = true;
                }
            }
        }

        if (!cities.some(c => c.isBigCity)) {
            for (let c of cities) {
                let validNeighbor = c.neighbors.find(n => n.terrain === country.terrain);
                if (validNeighbor) {
                    validNeighbor.terrain = TERRAIN.CITY;
                    validNeighbor.country = country;
                    c.isBigCity = true;
                    c.hasAirport = true;
                    c.isSmallCity = false;
                    break;
                }
            }
        }
    });

    // 5. Pre-build railroads connecting small cities to big cities
    let graph = {};
    
    edges.forEach(edge => {
        if (edge.isImpassable) return;
        let p1Id = edge.p1.x.toFixed(1) + ',' + edge.p1.y.toFixed(1);
        let p2Id = edge.p2.x.toFixed(1) + ',' + edge.p2.y.toFixed(1);
        
        if (!graph[p1Id]) graph[p1Id] = [];
        if (!graph[p2Id]) graph[p2Id] = [];
        
        let cost = 1;
        if (edge.isRiver) cost = 3;
        else if (edge.triangles.some(t => t.terrain === TERRAIN.MOUNTAIN)) cost = 1.5;
        
        cost += (edge.p1.x * 0.00001) + (edge.p1.y * 0.00002) + (edge.p2.x * 0.00003);
        
        graph[p1Id].push({ to: p2Id, edge: edge, cost: cost });
        graph[p2Id].push({ to: p1Id, edge: edge, cost: cost });
    });

    function getTriVertices(tri) {
        return tri.points.map(p => p.x.toFixed(1) + ',' + p.y.toFixed(1));
    }

    countriesDef.forEach(country => {
        let countrySmallCities = triangles.filter(t => t.terrain === TERRAIN.CITY && t.country === country && t.isSmallCity);
        let countryBigCities = triangles.filter(t => t.terrain === TERRAIN.CITY && t.country === country && t.isBigCity);
        
        if (countryBigCities.length === 0 || countrySmallCities.length === 0) return;

        countrySmallCities.forEach(smallCity => {
            let minDist = Infinity;
            let nearestBig = null;
            countryBigCities.forEach(big => {
                let d = Math.pow(smallCity.center.x - big.center.x, 2) + Math.pow(smallCity.center.y - big.center.y, 2);
                if (d < minDist) {
                    minDist = d;
                    nearestBig = big;
                }
            });
            smallCity.distToNearestBig = minDist;
            smallCity.nearestBig = nearestBig;
        });

        countrySmallCities.sort((a, b) => a.distToNearestBig - b.distToNearestBig);
        let citiesToConnect = countrySmallCities.slice(0, Math.ceil(countrySmallCities.length / 2));

        citiesToConnect.forEach(smallCity => {
            let nearestBig = smallCity.nearestBig;
            let startNodes = getTriVertices(smallCity).filter(id => graph[id]);
            let targetNodes = new Set(getTriVertices(nearestBig));
            
            if (startNodes.length === 0) return;

            let distances = {};
            let previous = {}; 
            let queue = []; 
            
            startNodes.forEach(id => {
                distances[id] = 0;
                queue.push({ id: id, dist: 0 });
            });
            
            let foundTarget = null;
            
            while(queue.length > 0) {
                queue.sort((a, b) => b.dist - a.dist);
                let curr = queue.pop();
                
                if (targetNodes.has(curr.id)) {
                    foundTarget = curr.id;
                    break;
                }
                
                if (curr.dist > distances[curr.id]) continue;
                
                let neighbors = graph[curr.id] || [];
                neighbors.forEach(n => {
                    let inOtherCountry = n.edge.triangles.some(t => {
                        let tCountry = t.country || countriesDef.find(c => c.terrain === t.terrain);
                        return tCountry && tCountry !== country;
                    });
                    
                    if (inOtherCountry) return;

                    let passesThroughOtherCity = n.edge.triangles.some(t => {
                        return t.terrain === TERRAIN.CITY && t.isSmallCity && t !== smallCity;
                    });
                    let extraCost = passesThroughOtherCity ? 10000 : 0;

                    let newDist = distances[curr.id] + n.cost + extraCost;
                    if (distances[n.to] === undefined || newDist < distances[n.to]) {
                        distances[n.to] = newDist;
                        previous[n.to] = { prevId: curr.id, edge: n.edge };
                        queue.push({ id: n.to, dist: newDist });
                    }
                });
            }
            
            if (foundTarget) {
                let currId = foundTarget;
                while(previous[currId]) {
                    let edge = previous[currId].edge;
                    edge.hasRailroad = true;
                    currId = previous[currId].prevId;
                }
            }
        });
    });

    return { triangles, edges, countries: countriesDef };
}
