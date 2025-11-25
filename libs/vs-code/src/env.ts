/**
 * Environment variable loader for Legesher VS Code extension
 *
 * Loads environment variables from .env file in development.
 * In production (packaged extension), env vars should be injected at build time.
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

    // Debug: write to temp file
    const debugLog = (msg: string) => {
        try {
            fs.appendFileSync('/tmp/env-debug.log', `${new Date().toISOString()} ${msg}\n`);
        } catch (e) {
            // Ignore
        }
        console.log(msg);
    };

    debugLog(`[Legesher Env] Extension path: ${extensionPath}`);

    // Try to find .env file in monorepo root
    const possiblePaths = [
        // Development: extensionPath is /tmp/CORE-XXX/libs/vs-code or /path/to/legesher/libs/vs-code
        path.join(extensionPath, '..', '..', '.env'),
        // Packaged extension fallback
        path.join(extensionPath, '.env'),
    ];

    debugLog(`[Legesher Env] Checking paths: ${possiblePaths.join(', ')}`);

    for (const envPath of possiblePaths) {
        const exists = fs.existsSync(envPath);
        debugLog(`[Legesher Env] Checking: ${envPath} (exists: ${exists})`);
        if (exists) {
            debugLog(`[Legesher Env] Loading environment variables from: ${envPath}`);
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

                debugLog('[Legesher Env] Environment variables loaded successfully');
                debugLog(`[Legesher Env] LEGESHER_TELEMETRY_CONNECTION_STRING: ${process.env.LEGESHER_TELEMETRY_CONNECTION_STRING ? 'SET' : 'NOT SET'}`);
                debugLog(`[Legesher Env] LEGESHER_FEEDBACK_URL: ${process.env.LEGESHER_FEEDBACK_URL ? 'SET' : 'NOT SET'}`);
                _envLoaded = true;
                return;
            } catch (error) {
                debugLog(`[Legesher Env] Error loading .env file: ${error}`);
            }
        }
    }

    debugLog(`[Legesher Env] No .env file found (checked: ${possiblePaths.join(', ')})`);
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
