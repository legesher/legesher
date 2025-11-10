import * as vscode from 'vscode';

/**
 * Centralized logging utility for the Legesher extension.
 * Uses VS Code OutputChannel for production-ready logging.
 */
export class Logger {
    private static outputChannel: vscode.OutputChannel;

    /**
     * Initialize the logger with an output channel
     */
    public static init(outputChannel: vscode.OutputChannel): void {
        Logger.outputChannel = outputChannel;
    }

    /**
     * Log an informational message
     */
    public static info(message: string, ...args: unknown[]): void {
        const formattedMessage = Logger.format('INFO', message, args);
        Logger.outputChannel.appendLine(formattedMessage);
    }

    /**
     * Log a warning message
     */
    public static warn(message: string, ...args: unknown[]): void {
        const formattedMessage = Logger.format('WARN', message, args);
        Logger.outputChannel.appendLine(formattedMessage);
    }

    /**
     * Log an error message
     */
    public static error(message: string, ...args: unknown[]): void {
        const formattedMessage = Logger.format('ERROR', message, args);
        Logger.outputChannel.appendLine(formattedMessage);
    }

    /**
     * Log a debug message (only shown when trace is enabled)
     */
    public static debug(message: string, ...args: unknown[]): void {
        const config = vscode.workspace.getConfiguration('legesher');
        const traceLevel = config.get<string>('trace.server', 'off');

        if (traceLevel === 'verbose') {
            const formattedMessage = Logger.format('DEBUG', message, args);
            Logger.outputChannel.appendLine(formattedMessage);
        }
    }

    /**
     * Format a log message with timestamp and level
     */
    private static format(level: string, message: string, args: unknown[]): string {
        const timestamp = new Date().toISOString();
        const argsString = args.length > 0 ? ` ${JSON.stringify(args)}` : '';
        return `[${timestamp}] [${level}] ${message}${argsString}`;
    }

    /**
     * Show the output channel
     */
    public static show(): void {
        Logger.outputChannel.show();
    }
}
