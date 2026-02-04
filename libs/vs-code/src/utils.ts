/**
 * Utility functions for the Legesher VS Code extension
 */

import { execFile } from 'child_process';
import { Logger } from './logger';

/**
 * Validate that the command appears to be a Legesher-related executable
 * This provides basic protection against arbitrary command execution
 */
function isValidLegesherCommand(command: string): boolean {
    // Command should contain 'legesher' or end with 'lsp'
    const lowerCommand = command.toLowerCase();
    return lowerCommand.includes('legesher') || lowerCommand.endsWith('lsp');
}

/**
 * Check if the language server command is available
 * Uses execFile to prevent command injection vulnerabilities
 * Validates command appears to be Legesher-related before execution
 */
export async function isServerAvailable(command: string): Promise<boolean> {
    // Validate command before executing
    if (!isValidLegesherCommand(command)) {
        Logger.warn(`Command '${command}' does not appear to be a Legesher executable. Skipping availability check.`);
        return false;
    }

    try {
        await new Promise<void>((resolve, reject) => {
            execFile(command, ['--version'], (error: Error | null) => {
                if (error) {
                    reject(error);
                } else {
                    resolve();
                }
            });
        });
        return true;
    } catch {
        return false;
    }
}
