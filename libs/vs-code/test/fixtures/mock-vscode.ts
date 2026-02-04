/**
 * Mock VS Code API for unit testing
 *
 * This module provides mock implementations of VS Code APIs
 * that can be used in unit tests without requiring the actual VS Code runtime.
 */

import * as sinon from 'sinon';

// Mock ExtensionContext
export function createMockExtensionContext(): any {
    const globalState = new Map<string, any>();

    return {
        subscriptions: [],
        globalState: {
            get: (key: string, defaultValue?: any) => globalState.get(key) ?? defaultValue,
            update: sinon.stub().callsFake((key: string, value: any) => {
                globalState.set(key, value);
                return Promise.resolve();
            }),
            keys: () => Array.from(globalState.keys()),
        },
        workspaceState: {
            get: sinon.stub().returns(undefined),
            update: sinon.stub().resolves(),
            keys: sinon.stub().returns([]),
        },
        extensionPath: '/mock/extension/path',
        extensionUri: { fsPath: '/mock/extension/path' },
        storagePath: '/mock/storage/path',
        globalStoragePath: '/mock/global/storage/path',
        logPath: '/mock/log/path',
        extensionMode: 1, // ExtensionMode.Development
        asAbsolutePath: (relativePath: string) => `/mock/extension/path/${relativePath}`,
    };
}

// Mock workspace configuration
export function createMockWorkspaceConfiguration(config: Record<string, any> = {}): any {
    return {
        get: sinon.stub().callsFake((key: string, defaultValue?: any) => {
            return config[key] ?? defaultValue;
        }),
        update: sinon.stub().resolves(),
        has: sinon.stub().callsFake((key: string) => key in config),
        inspect: sinon.stub().returns(undefined),
    };
}

// Mock vscode.workspace
export function createMockWorkspace(config: Record<string, any> = {}): any {
    return {
        getConfiguration: sinon.stub().returns(createMockWorkspaceConfiguration(config)),
        onDidChangeConfiguration: sinon.stub().returns({ dispose: sinon.stub() }),
        workspaceFolders: undefined,
        name: undefined,
        fs: {
            readFile: sinon.stub().resolves(Buffer.from('')),
            writeFile: sinon.stub().resolves(),
        },
    };
}

// Mock vscode.window
export function createMockWindow(): any {
    return {
        showInformationMessage: sinon.stub().resolves(undefined),
        showWarningMessage: sinon.stub().resolves(undefined),
        showErrorMessage: sinon.stub().resolves(undefined),
        showQuickPick: sinon.stub().resolves(undefined),
        showInputBox: sinon.stub().resolves(undefined),
        createStatusBarItem: sinon.stub().returns({
            text: '',
            tooltip: '',
            command: '',
            show: sinon.stub(),
            hide: sinon.stub(),
            dispose: sinon.stub(),
        }),
        createOutputChannel: sinon.stub().returns({
            appendLine: sinon.stub(),
            append: sinon.stub(),
            clear: sinon.stub(),
            show: sinon.stub(),
            hide: sinon.stub(),
            dispose: sinon.stub(),
        }),
        activeTextEditor: undefined,
    };
}

// Mock vscode.commands
export function createMockCommands(): any {
    const registeredCommands = new Map<string, Function>();

    return {
        registerCommand: sinon.stub().callsFake((command: string, callback: Function) => {
            registeredCommands.set(command, callback);
            return { dispose: sinon.stub() };
        }),
        executeCommand: sinon.stub().callsFake(async (command: string, ...args: any[]) => {
            const handler = registeredCommands.get(command);
            if (handler) {
                return handler(...args);
            }
            return undefined;
        }),
        getCommands: sinon.stub().resolves(Array.from(registeredCommands.keys())),
    };
}

// Mock vscode.env
export function createMockEnv(): any {
    return {
        machineId: 'mock-machine-id',
        sessionId: 'mock-session-id',
        language: 'en',
        appName: 'Visual Studio Code',
        appRoot: '/mock/app/root',
        uriScheme: 'vscode',
        clipboard: {
            readText: sinon.stub().resolves(''),
            writeText: sinon.stub().resolves(),
        },
        openExternal: sinon.stub().resolves(true),
    };
}

// Mock vscode.extensions
export function createMockExtensions(): any {
    return {
        getExtension: sinon.stub().returns({
            id: 'legesher.legesher-vscode',
            extensionPath: '/mock/extension/path',
            isActive: true,
            packageJSON: {
                version: '0.1.2',
                name: 'legesher-vscode',
            },
            activate: sinon.stub().resolves(),
            exports: undefined,
        }),
        all: [],
        onDidChange: sinon.stub().returns({ dispose: sinon.stub() }),
    };
}

// Create a complete mock vscode module
export function createMockVscode(config: Record<string, any> = {}): any {
    return {
        workspace: createMockWorkspace(config),
        window: createMockWindow(),
        commands: createMockCommands(),
        env: createMockEnv(),
        extensions: createMockExtensions(),
        Uri: {
            file: (path: string) => ({ fsPath: path, scheme: 'file' }),
            parse: (uri: string) => ({ fsPath: uri, scheme: 'https' }),
        },
        EventEmitter: class MockEventEmitter {
            private listeners: Function[] = [];
            event = (listener: Function) => {
                this.listeners.push(listener);
                return { dispose: () => {} };
            };
            fire(data: any) {
                this.listeners.forEach(l => l(data));
            }
        },
        Disposable: class MockDisposable {
            static from(...disposables: any[]) {
                return { dispose: () => disposables.forEach(d => d.dispose?.()) };
            }
        },
        StatusBarAlignment: { Left: 1, Right: 2 },
        ConfigurationTarget: { Global: 1, Workspace: 2, WorkspaceFolder: 3 },
        version: '1.85.0',
    };
}
