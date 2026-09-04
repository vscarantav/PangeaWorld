import test from 'node:test';
import assert from 'node:assert/strict';

import { countriesDef, generateMapData, TERRAIN } from './MapGenerator.js';

function mapSignature(map) {
    const triangleState = map.triangles.map(triangle => [
        triangle.id,
        triangle.terrain.name,
        triangle.country?.id ?? '',
        Boolean(triangle.isSmallCity),
        Boolean(triangle.isBigCity),
        Boolean(triangle.isBigCityPart),
        Boolean(triangle.isPort)
    ].join(':')).join('|');
    const edgeState = map.edges.map(edge => [
        edge.id,
        Boolean(edge.isImpassable),
        Boolean(edge.isRiver),
        Boolean(edge.hasRailroad)
    ].join(':')).join('|');
    return `${triangleState}\n${edgeState}`;
}

function assertMapInvariants(seed) {
    const map = generateMapData(seed);
    const incidentEdges = new Map(map.triangles.map(triangle => [triangle.id, []]));
    map.edges.forEach(edge => {
        edge.triangles.forEach(triangle => incidentEdges.get(triangle.id).push(edge));
    });

    for (const mountain of map.triangles.filter(triangle => triangle.terrain === TERRAIN.MOUNTAIN)) {
        const passableEdges = incidentEdges.get(mountain.id).filter(edge => !edge.isImpassable);
        assert.equal(passableEdges.length, 1, `${seed}: mountain ${mountain.id} must have exactly one passable edge`);
    }

    for (const edge of map.edges.filter(candidate => !candidate.isImpassable)) {
        assert.equal(edge.triangles.length, 2, `${seed}: passable edge ${edge.id} touches the ungenerated boundary`);
        assert.ok(
            edge.triangles.every(triangle => triangle.terrain !== TERRAIN.OCEAN),
            `${seed}: passable edge ${edge.id} touches ocean`
        );
    }

    for (const country of countriesDef) {
        const anchors = map.triangles.filter(triangle => (
            triangle.country === country && (triangle.isSmallCity || triangle.isBigCity)
        ));
        const decorativeParts = map.triangles.filter(triangle => triangle.country === country && triangle.isBigCityPart);
        const ports = map.triangles.filter(triangle => triangle.country === country && triangle.isPort);
        // Only Nordvik (2), Lunara (2), and Drakmoor (1) get ports. All others get 0.
        const expectedPorts = (country.id === 'NORDVIK' || country.id === 'LUNARA') ? 2
            : country.id === 'DRAKMOOR' ? 1
            : 0;

        assert.equal(anchors.length, 8, `${seed}: ${country.name} must have exactly 8 city anchors`);
        assert.ok(
            decorativeParts.every(part => !part.isSmallCity && !part.isBigCity),
            `${seed}: ${country.name} big-city footprint triangles must not count as anchors`
        );
        assert.equal(ports.length, expectedPorts, `${seed}: ${country.name} has the wrong port count`);
        assert.ok(ports.every(port => anchors.includes(port)), `${seed}: every ${country.name} port must be a city anchor`);
        assert.ok(ports.every(port => (
            port.neighbors.length < 3 || port.neighbors.some(neighbor => neighbor.terrain === TERRAIN.OCEAN)
        )), `${seed}: every ${country.name} port must be coastal`);

        if (country.id === 'ZEPHYRIA') {
            const coastalZephyria = map.triangles.filter(t => t.terrain === TERRAIN.ZEPHYRIA && (t.neighbors.length < 3 || t.neighbors.some(n => n.terrain === TERRAIN.OCEAN)));
            assert.equal(coastalZephyria.length, 0, `${seed}: Zephyria must be landlocked with 0 coastal triangles`);
        }
    }
}

test('map generation is deterministic for a seed', () => {
    assert.equal(mapSignature(generateMapData('determinism-check')), mapSignature(generateMapData('determinism-check')));
});

test('map invariants hold across representative seeds', () => {
    assertMapInvariants('default');
    for (let index = 0; index < 24; index++) {
        assertMapInvariants(`invariant-seed-${index}`);
    }
});
