import { countriesDef, TERRAIN } from './MapGenerator.js';

const terrainByName = new Map(Object.values(TERRAIN).map((terrain) => [terrain.name, terrain]));

function centerOf(points) {
    return {
        x: points.reduce((sum, point) => sum + Number(point.x), 0) / points.length,
        y: points.reduce((sum, point) => sum + Number(point.y), 0) / points.length,
    };
}

function nearestCountry(countries, center) {
    return countries.reduce((nearest, country) => {
        const distance = (country.x - center.x) ** 2 + (country.y - center.y) ** 2;
        return !nearest || distance < nearest.distance ? { country, distance } : nearest;
    }, null)?.country || null;
}

function edgePointsFromId(id) {
    const match = String(id).match(/^(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)-(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)$/);
    if (!match) throw new Error(`Map snapshot edge ${id} has no stored geometry`);
    return [{ x: Number(match[1]), y: Number(match[2]) }, { x: Number(match[3]), y: Number(match[4]) }];
}

function snapshotCountryId(triangle, countries) {
    if (triangle.country?.id) return triangle.country.id;
    const terrainCountry = countries.find((country) => country.terrain === triangle.terrain);
    if (terrainCountry) return terrainCountry.id;
    if (triangle.terrain === TERRAIN.OCEAN) return null;
    return nearestCountry(countries, triangle.center)?.id || null;
}

export function serializeMapSnapshot(map, seed) {
    return {
        version: 2,
        seed,
        triangles: map.triangles.map((triangle) => ({
            id: triangle.id,
            terrain: triangle.terrain.name,
            points: triangle.points.map((point) => ({ x: point.x, y: point.y })),
            country_id: snapshotCountryId(triangle, map.countries),
            is_small_city: Boolean(triangle.isSmallCity),
            is_big_city: Boolean(triangle.isBigCity),
            is_big_city_part: Boolean(triangle.isBigCityPart),
            is_port: Boolean(triangle.isPort),
            has_airport: Boolean(triangle.hasAirport),
        })),
        edges: map.edges.map((edge) => ({
            id: edge.id,
            p1: { x: edge.p1.x, y: edge.p1.y },
            p2: { x: edge.p2.x, y: edge.p2.y },
            triangle_ids: edge.triangles.map((triangle) => triangle.id),
            has_railroad: Boolean(edge.hasRailroad),
            is_river: Boolean(edge.isRiver),
            is_impassable: Boolean(edge.isImpassable),
        })),
        countries: map.countries.map((country) => ({
            id: country.id,
            name: country.name,
            x: country.x,
            y: country.y,
            labelX: country.labelX,
            labelY: country.labelY,
        })),
        cities: map.triangles
            .filter((triangle) => triangle.isSmallCity || triangle.isBigCity)
            .map((triangle) => ({
                id: triangle.id,
                triangle_id: triangle.id,
                country_id: snapshotCountryId(triangle, map.countries),
                is_port: Boolean(triangle.isPort),
                is_big_city: Boolean(triangle.isBigCity),
            })),
    };
}

export function hydrateMapSnapshot(snapshot) {
    if (!snapshot?.triangles?.length || !snapshot?.edges?.length || !snapshot?.countries?.length) {
        throw new Error('This game does not have a complete persisted map snapshot.');
    }

    const countries = snapshot.countries.map((saved) => {
        const design = countriesDef.find((country) => String(country.id) === String(saved.id));
        if (!design) throw new Error(`Unknown country ${saved.id} in map snapshot`);
        return {
            ...design,
            name: saved.name,
            x: Number(saved.x ?? design.x),
            y: Number(saved.y ?? design.y),
            labelX: Number(saved.labelX ?? design.labelX),
            labelY: Number(saved.labelY ?? design.labelY),
        };
    });
    const countriesById = new Map(countries.map((country) => [String(country.id), country]));
    const citiesByTriangle = new Map((snapshot.cities || []).map((city) => [String(city.triangle_id), city]));

    const triangles = snapshot.triangles.map((saved) => {
        const points = (saved.points || []).map((point) => ({ x: Number(point.x), y: Number(point.y) }));
        if (points.length !== 3 || points.some((point) => !Number.isFinite(point.x) || !Number.isFinite(point.y))) {
            throw new Error(`Map snapshot triangle ${saved.id} has invalid geometry`);
        }
        const terrain = terrainByName.get(saved.terrain);
        if (!terrain) throw new Error(`Map snapshot triangle ${saved.id} has unknown terrain`);
        const city = citiesByTriangle.get(String(saved.id));
        const center = centerOf(points);
        const terrainCountry = countries.find((country) => country.terrain === terrain);
        const country = countriesById.get(String(saved.country_id ?? city?.country_id))
            || terrainCountry
            || (terrain !== TERRAIN.OCEAN ? nearestCountry(countries, center) : null);
        return {
            id: saved.id,
            points,
            center,
            terrain,
            country,
            neighbors: [],
            isSmallCity: Boolean(saved.is_small_city ?? (city && !city.is_big_city)),
            isBigCity: Boolean(saved.is_big_city ?? city?.is_big_city),
            isBigCityPart: Boolean(saved.is_big_city_part),
            isPort: Boolean(saved.is_port ?? city?.is_port),
            hasAirport: Boolean(saved.has_airport ?? city?.is_big_city),
        };
    });
    const trianglesById = new Map(triangles.map((triangle) => [String(triangle.id), triangle]));
    const edges = snapshot.edges.map((saved) => {
        const [derivedP1, derivedP2] = saved.p1 && saved.p2 ? [saved.p1, saved.p2] : edgePointsFromId(saved.id);
        const linkedTriangles = (saved.triangle_ids || []).map((id) => trianglesById.get(String(id)));
        if (!linkedTriangles.length || linkedTriangles.some((triangle) => !triangle)) {
            throw new Error(`Map snapshot edge ${saved.id} references an unknown triangle`);
        }
        if (linkedTriangles.length === 2) {
            linkedTriangles[0].neighbors.push(linkedTriangles[1]);
            linkedTriangles[1].neighbors.push(linkedTriangles[0]);
        }
        return {
            id: saved.id,
            p1: { x: Number(derivedP1.x), y: Number(derivedP1.y) },
            p2: { x: Number(derivedP2.x), y: Number(derivedP2.y) },
            triangles: linkedTriangles,
            hasRailroad: Boolean(saved.has_railroad),
            isRiver: Boolean(saved.is_river),
            isImpassable: Boolean(saved.is_impassable),
            isHovered: false,
        };
    });

    return { triangles, edges, countries };
}
