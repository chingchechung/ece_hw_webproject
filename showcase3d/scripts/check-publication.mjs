import { readPublication } from './publication.mjs';
if(!process.argv[2])throw new Error('Usage: node check-publication.mjs <published-assignments-directory>');
console.log(JSON.stringify([...readPublication(process.argv[2]).keys()]));
