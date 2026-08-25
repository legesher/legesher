/**
 * Environment variable loader for Legesher VS Code extension
 *
 * Loads environment variables from .env file in development.
 * In production (packaged extension), env vars should be injected at build time.
 *
 * NOTE: The telemetry connection string (LEGESHER_TELEMETRY_CONNECTION_STRING) is
 * injected at BUILD TIME by esbuild's `define` option for production builds.
 * Runtime .env loading only affects variables NOT injected at build time,
 * such as LEGESHER_FEEDBACK_URL, or for development with envFile in launch.json.
 */

import * as fs from 'fs';
import * as path from 'path';

// Store loaded env vars
let _envLoaded = false;

/**
 * Load environment variables from .env file
 * Searches for .env in the monorepo root (two levels up from extension directory)
 */
export function loadEnvVariables(extensionPath: string): void {
    if (_envLoaded) {
        return;
    }

    console.log('[Legesher Env] Loading environment configuration...');

    // Try to find .env file in monorepo root
    const possiblePaths = [
        // Development: extensionPath ends in libs/vs-code, so the repo root
        // holding .env is two levels up.
        path.join(extensionPath, '..', '..', '.env'),
        // Packaged extension fallback
        path.join(extensionPath, '.env'),
    ];

    for (const envPath of possiblePaths) {
        if (fs.existsSync(envPath)) {
            console.log('[Legesher Env] Found .env file, loading variables...');
            try {
                const envContent = fs.readFileSync(envPath, 'utf8');
                const lines = envContent.split('\n');

                for (const line of lines) {
                    // Skip empty lines and comments
                    const trimmed = line.trim();
                    if (!trimmed || trimmed.startsWith('#')) {
                        continue;
                    }

                    // Parse KEY=VALUE
                    const match = trimmed.match(/^([^=]+)=(.*)$/);
                    if (match) {
                        const key = match[1].trim();
                        const value = match[2].trim();

                        // Only set if not already defined (respect system env vars)
                        if (!process.env[key]) {
                            process.env[key] = value;
                        }
                    }
                }

                console.log('[Legesher Env] Environment variables loaded successfully');
                _envLoaded = true;
                return;
            } catch (error) {
                console.log(`[Legesher Env] Error loading .env file: ${error}`);
            }
        }
    }

    console.log('[Legesher Env] No .env file found');
    _envLoaded = true;
}

/**
 * Get an environment variable
 * @param key The environment variable key
 * @param defaultValue Optional default value if not found
 */
export function getEnvVar(key: string, defaultValue: string = ''): string {
    return process.env[key] || defaultValue;
}
