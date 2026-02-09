const esbuild = require('esbuild');
const fs = require('fs');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '..', '..', '.env') });

const production = process.argv.includes('--production');
const watch = process.argv.includes('--watch');

// Get telemetry connection string for production builds
const telemetryConnectionString = process.env.LEGESHER_TELEMETRY_CONNECTION_STRING || '';
if (production && telemetryConnectionString) {
    console.log('[build] Telemetry connection string will be embedded in production build');
} else if (production && !telemetryConnectionString) {
    console.warn('[build] WARNING: No telemetry connection string found - telemetry will be disabled in production');
}

/**
 * Copy a file, creating parent directories as needed
 */
function copyFile(src, dest) {
    try {
        fs.mkdirSync(path.dirname(dest), { recursive: true });
        fs.copyFileSync(src, dest);
    } catch (err) {
        const message = `Failed to copy file from "${src}" to "${dest}": ${err && err.message ? err.message : err}`;
        const error = new Error(message);
        error.originalError = err;
        throw error;
    }
}

/**
 * Copy webview assets and prismjs files to output directory
 */
function copyAssets() {
    const outDir = path.join(__dirname, 'out');

    // Copy webview UI assets
    const webviewSrc = path.join(__dirname, 'src', 'webview', 'ui');
    const webviewDest = path.join(outDir, 'webview', 'ui');

    const webviewFiles = ['styles.css', 'main.js'];
    for (const file of webviewFiles) {
        const srcPath = path.join(webviewSrc, file);
        const destPath = path.join(webviewDest, file);
        if (fs.existsSync(srcPath)) {
            copyFile(srcPath, destPath);
            console.log(`Copied: webview/ui/${file}`);
        } else {
            console.warn(`Warning: Webview asset not found: ${srcPath}`);
        }
    }

    // Copy prismjs files for webview syntax highlighting
    const prismSrc = path.join(__dirname, 'node_modules', 'prismjs');
    const prismDest = path.join(outDir, 'prismjs');

    const prismFiles = [
        { src: 'themes/prism-tomorrow.min.css', dest: 'themes/prism-tomorrow.min.css' },
        { src: 'prism.js', dest: 'prism.js' },
        { src: 'components/prism-python.min.js', dest: 'components/prism-python.min.js' }
    ];

    for (const { src, dest } of prismFiles) {
        const srcPath = path.join(prismSrc, src);
        const destPath = path.join(prismDest, dest);
        if (fs.existsSync(srcPath)) {
            copyFile(srcPath, destPath);
            console.log(`Copied: prismjs/${src}`);
        } else {
            console.warn(`Warning: Prism file not found: ${srcPath}`);
        }
    }
}

/**
 * Plugin to copy assets after build
 */
const copyAssetsPlugin = {
    name: 'copy-assets',
    setup(build) {
        build.onEnd(result => {
            if (result.errors.length === 0) {
                copyAssets();
            }
        });
    }
};

/**
 * Plugin to report build status (useful for watch mode)
 */
const esbuildProblemMatcherPlugin = {
    name: 'esbuild-problem-matcher',
    setup(build) {
        build.onStart(() => {
            console.log('[build] started');
        });
        build.onEnd(result => {
            result.errors.forEach(({ text, location }) => {
                console.error(`✘ [ERROR] ${text}`);
                if (location) {
                    console.error(`    ${location.file}:${location.line}:${location.column}:`);
                }
            });
            console.log('[build] finished');
        });
    }
};

async function main() {
    const ctx = await esbuild.context({
        entryPoints: ['src/extension.ts'],
        bundle: true,
        format: 'cjs',
        minify: production,
        sourcemap: !production,
        sourcesContent: false,
        platform: 'node',
        outfile: 'out/extension.js',
        external: ['vscode'],
        logLevel: 'info',
        // Inject telemetry connection string at build time for production only.
        // In development, leave process.env intact so launch.json envFile works at runtime.
        ...(production ? {
            define: {
                'process.env.LEGESHER_TELEMETRY_CONNECTION_STRING': JSON.stringify(telemetryConnectionString),
            },
        } : {}),
        plugins: [
            copyAssetsPlugin,
            esbuildProblemMatcherPlugin
        ]
    });

    if (watch) {
        await ctx.watch();
        console.log('Watching for changes...');
    } else {
        await ctx.rebuild();
        await ctx.dispose();
    }
}

main().catch(e => {
    console.error(e);
    process.exit(1);
});
