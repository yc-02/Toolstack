#!/usr/bin/env node
// convert.mjs
// Turn a bitmap into a stylized SVG using sharp + imagetracerjs (+ optional SVGO).
//
// Usage examples:
//   node convert.mjs input.png output.svg --mode=fidelity --layers=14 --svgo
//   node convert.mjs input.png output.svg --mode=poster --layers=5 --preblur=0.6 --mergecolors=16 --svgo
//   node convert.mjs input.png output.svg --palette=#000000,#7d7e80,#ffffff --svgo
//
// One-time install (in your project):
//   npm i sharp imagetracerjs svgo
//
// If you see issues with SVGO not found by npx, also try:
//   npm i -g svgo

import fs from 'node:fs';
import sharp from 'sharp';
import ImageTracer from 'imagetracerjs';
import { optimize } from 'svgo';

// ---------- args ----------
const input = process.argv[2] || 'input.png';
const output = process.argv[3] || 'output.svg';

const flags = Object.fromEntries(
    process.argv.slice(4).map(s => {
        const m = s.match(/^--([^=]+)(?:=(.*))?$/);
        return m ? [m[1], m[2] ?? true] : [s, true];
    })
);

const mode = (flags.mode || 'fidelity').toString(); // 'fidelity' | 'poster'
const layers = Math.max(2, Number(flags.layers || 6));
const upscale = Number(flags.upscale || 1);
const preblur = flags.preblur ? Number(flags.preblur) : 0;  // 0.4–1.0 typical for posterizing
const median = flags.median ? Number(flags.median) : 0;    // 1–3
const mergeTol = flags.mergecolors ? Number(flags.mergecolors) : 0; // ΔRGB (0–255)
const dropWhite = !!flags.dropwhite;
const doSvgo = !!flags.svgo;

// ---------- preprocess (sharp) ----------
let img = sharp(input, { unlimited: true })
    .toColourspace('srgb')               // lock to sRGB to avoid profile shifts
    .ensureAlpha()
    .flatten({ background: '#ffffff' }); // flatten alpha to stabilize edge colors for palette

if (upscale > 1) {
    const meta = await img.metadata();
    img = img.resize({
        width: Math.round((meta.width || 0) * upscale),
        kernel: 'nearest', // keeps edges crisp for tracing
    });
}
if (median > 0) img = img.median(median); // kill salt-pepper specks
if (preblur > 0) img = img.blur(preblur); // gently merge tiny regions

const { data, info } = await img.raw().toBuffer({ resolveWithObject: true });
const imgd = { width: info.width, height: info.height, data: new Uint8ClampedArray(data) };

// ---------- imagetracer options ----------
const optsBase = {
    numberofcolors: layers,
    roundcoords: 1,
    blurradius: 0,   // we handle blur in sharp
    blurdelta: 20,
};

let opts;
if (mode === 'poster') {
    // Stylized/poster look: fewer colors, looser fit, ignore tiny paths
    opts = {
        ...optsBase,
        pathomit: 12,        // raise to 14–18 if you still see tiny bits
        ltres: 1.3,
        qtres: 1.3,
        linefilter: true,
        colorsampling: 1,    // deterministic sampling
        colorquantcycles: 3, // fewer cycles OK for stylized
        mincolorratio: 0.02, // drop very rare colors
    };
} else {
    // Fidelity mode: closer to original colors
    opts = {
        ...optsBase,
        pathomit: 8,         // keep small bits for color fidelity
        ltres: 1.0,
        qtres: 1.0,
        linefilter: false,
        colorsampling: 1,    // deterministic sampling
        colorquantcycles: 6, // spend more effort picking palette
        mincolorratio: 0,    // don’t drop rare colors prematurely
    };
}

// Optional fixed palette (overrides color picking)
function hexToRgbObj(hex) {
    let h = String(hex).trim().replace(/^#/, '');
    if (h.length === 3) h = h.split('').map(c => c + c).join('');
    let r = 0, g = 0, b = 0, a = 255;
    if (h.length === 6 || h.length === 8) {
        r = parseInt(h.slice(0, 2), 16);
        g = parseInt(h.slice(2, 4), 16);
        b = parseInt(h.slice(4, 6), 16);
        if (h.length === 8) a = parseInt(h.slice(6, 8), 16);
    } else {
        throw new Error(`Bad hex color: ${hex}`);
    }
    return { r, g, b, a };
}

if (flags.palette) {
    const hexes = String(flags.palette).split(',').map(s => s.trim()).filter(Boolean);
    opts.colorsampling = 0;            // use custom palette
    opts.pal = hexes.map(hexToRgbObj); // [{r,g,b,a}, ...]
    opts.numberofcolors = opts.pal.length;
}

// ---------- trace to SVG ----------
let svg = ImageTracer.imagedataToSVG(imgd, opts);

// Optional: drop pure white fills (simple BG removal if your page is white)
if (dropWhite) {
    svg = svg
        .replace(/<path[^>]*fill="#ffffff"[^>]*\/>/gi, '')
        .replace(/<path[^>]*fill="rgb\(255,\s*255,\s*255\)"[^>]*\/>/gi, '');
}

// ---------- merge similar colors to reduce layers ----------
if (mergeTol > 0) {
    const fills = Array.from(new Set(
        (svg.match(/fill="(#[0-9a-fA-F]{6}|rgb\(\d+,\s*\d+,\s*\d+\))"/g) || [])
            .map(m => m.slice(6, -1).toLowerCase())
    ));
    const toRGB = c => c.startsWith('#')
        ? [parseInt(c.slice(1, 3), 16), parseInt(c.slice(3, 5), 16), parseInt(c.slice(5, 7), 16)]
        : c.match(/\d+/g).map(Number);

    const rgb = fills.map(toRGB);
    const reps = [];
    for (let i = 0; i < rgb.length; i++) {
        let assigned = false;
        for (const rep of reps) {
            const d = Math.abs(rgb[i][0] - rep[0]) + Math.abs(rgb[i][1] - rep[1]) + Math.abs(rgb[i][2] - rep[2]);
            if (d <= mergeTol) { rep.members.push(fills[i]); assigned = true; break; }
        }
        if (!assigned) reps.push({ 0: rgb[i][0], 1: rgb[i][1], 2: rgb[i][2], members: [fills[i]] });
    }
    for (const rep of reps) {
        const target = rep.members[0];
        for (const c of rep.members) {
            if (c === target) continue;
            const re = new RegExp(`fill="${c.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}"`, 'gi');
            svg = svg.replace(re, `fill="${target}"`);
        }
    }
}

// ---------- SVGO optimize ----------
if (doSvgo) {
    const result = optimize(svg, {
        multipass: true,
        plugins: [
            { name: 'mergePaths' },
            { name: 'convertPathData', params: { floatPrecision: 1 } },
            { name: 'cleanupNumericValues', params: { floatPrecision: 1 } },
            { name: 'removeUselessStrokeAndFill' },
            { name: 'removeUselessDefs' },
            { name: 'collapseGroups' },
        ],
    });
    svg = result.data;
}

// ---------- write ----------
fs.writeFileSync(output, svg, 'utf8');
console.log(`Saved → ${output}  (mode=${mode}, layers=${layers}, upscale=${upscale}x, preblur=${preblur}, median=${median}, mergeTol=${mergeTol})`);