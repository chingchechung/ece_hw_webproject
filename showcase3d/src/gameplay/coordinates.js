// All authoritative vehicle positions are Lite WORLD PIXELS, never logical cells.
export const LITE_ROAD_TILE = 14;
export const METERS_PER_LITE_PIXEL = 0.7 / LITE_ROAD_TILE;
export const VIRTUAL_DISTANCE_FACTOR = 12;
export const liteToMeters = value => value * METERS_PER_LITE_PIXEL;
export const metersToLite = value => value / METERS_PER_LITE_PIXEL;
export const logicalToLite = p => ({ x: (2 * p.x + 1) * 28, y: (2 * p.y + 1) * 28 });
export const liteToThree = p => ({ x: liteToMeters(p.x), z: liteToMeters(p.y) });
export const virtualSpeedToMeters = speed => liteToMeters(speed / VIRTUAL_DISTANCE_FACTOR);
