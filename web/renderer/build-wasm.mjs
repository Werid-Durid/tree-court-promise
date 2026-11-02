import * as esbuild from 'esbuild-wasm';
await esbuild.initialize({ worker: false });
await esbuild.build({ entryPoints: ['story-scene.js'], bundle: true, format: 'esm', minify: true, outfile: '../frontend/scene.bundle.js', logLevel: 'info' });
console.log('BUILD_OK');
