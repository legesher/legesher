/**
 * The repo attribution label, byte for byte the Python helper's.
 *
 * The canonical forms and labels come from the shared vector file in
 * libs/core/tests/fixtures, which the Python suite loads too, so the two
 * helpers cannot drift without one of the suites failing. The vectors use
 * Devanagari, vocalised Arabic, Sinhala with ZWJ and CJK in NFC and NFD
 * spellings; Latin-only vectors would not catch a normalization gap.
 */

import * as assert from 'assert';
import { createHash } from 'crypto';
import * as fs from 'fs';
import * as path from 'path';

import {
    HEADER,
    LABEL_PREFIX,
    canonicalRemote,
    killSwitchSet,
    labelForRemote,
    repoAttributionAllowed,
    repoAttributionHeaders,
    repoLabel,
} from '../../src/repoAttribution';

interface Vector {
    name: string;
    input: string;
    canonical: string | null;
    label: string | null;
}

interface VectorFile {
    label_prefix: string;
    label_hex_length: number;
    vectors: Vector[];
    same_label: Record<string, string[]>;
    different_label: [string, string][];
    kill_switch: { value: string; set: boolean }[];
}

const VECTORS_PATH = path.resolve(__dirname, '../../../core/tests/fixtures/repo_attribution_vectors.json');
const VECTORS: VectorFile = JSON.parse(fs.readFileSync(VECTORS_PATH, 'utf8'));
const BY_NAME = new Map(VECTORS.vectors.map((vector) => [vector.name, vector]));

const HEX32 = /^[0-9a-f]{32}$/;
const SALT = 'deadbeefdeadbeefdeadbeefdeadbeef';

function sha256Label(material: string): string {
    return createHash('sha256').update(material, 'utf8').digest('hex').slice(0, 32);
}

function vector(name: string): Vector {
    const found = BY_NAME.get(name);
    assert.ok(found, `no vector named ${JSON.stringify(name)}`);
    return found;
}

describe('repoAttribution', () => {
    describe('shared vectors', () => {
        it('uses the same prefix and width as the vector file', () => {
            assert.strictEqual(VECTORS.label_prefix, LABEL_PREFIX);
            assert.strictEqual(VECTORS.label_hex_length, 32);
            assert.ok(VECTORS.vectors.length > 0);
        });

        for (const item of VECTORS.vectors) {
            it(`canonicalizes and labels ${JSON.stringify(item.name)}`, () => {
                assert.strictEqual(canonicalRemote(item.input) ?? null, item.canonical);
                assert.strictEqual(labelForRemote(item.input) ?? null, item.label);
                if (item.canonical !== null) {
                    // The file's own labels are the documented recipe.
                    assert.strictEqual(item.label, sha256Label(LABEL_PREFIX + item.canonical));
                }
            });
        }

        for (const [group, names] of Object.entries(VECTORS.same_label)) {
            it(`gives one label to every spelling in ${JSON.stringify(group)}`, () => {
                const members = names.map(vector);
                assert.strictEqual(new Set(members.map((m) => m.input)).size, members.length);
                const labels = new Set(members.map((m) => labelForRemote(m.input)));
                assert.strictEqual(labels.size, 1);
                assert.ok(HEX32.test([...labels][0] ?? ''));
            });
        }

        for (const [first, second] of VECTORS.different_label) {
            it(`keeps ${JSON.stringify(first)} and ${JSON.stringify(second)} apart`, () => {
                const a = labelForRemote(vector(first).input);
                const b = labelForRemote(vector(second).input);
                assert.ok(a && b && a !== b);
            });
        }

        it('holds NFC and NFD spellings that really differ', () => {
            const nfc = vector('vocalised Arabic, NFC').input;
            const nfd = vector('vocalised Arabic, NFD').input;
            assert.notStrictEqual(nfc, nfd);
            assert.strictEqual(nfc.normalize('NFD'), nfd);
            const sinhala = vector('Sinhala with ZWJ, NFC').input;
            assert.ok(sinhala.includes('\u200d'), 'the Sinhala vector keeps its ZWJ');
        });
    });

    describe('repoAttributionAllowed', () => {
        const on = { telemetryEnabled: true, repoAttribution: true, vscodeTelemetryEnabled: true, env: {} };

        it('needs every switch on', () => {
            assert.strictEqual(repoAttributionAllowed(on), true);
            assert.strictEqual(repoAttributionAllowed({ ...on, telemetryEnabled: false }), false);
            assert.strictEqual(repoAttributionAllowed({ ...on, repoAttribution: false }), false);
        });

        it("is off when VS Code's own telemetry switch is off", () => {
            assert.strictEqual(repoAttributionAllowed({ ...on, vscodeTelemetryEnabled: false }), false);
        });

        for (const word of ['off', 'no', 'false', 'true', 'yes', '1']) {
            it(`never treats the string ${JSON.stringify(word)} as consent`, () => {
                const asString = word as unknown as boolean;
                assert.strictEqual(repoAttributionAllowed({ ...on, repoAttribution: asString }), false);
                assert.strictEqual(repoAttributionAllowed({ ...on, telemetryEnabled: asString }), false);
                assert.strictEqual(repoAttributionAllowed({ ...on, vscodeTelemetryEnabled: asString }), false);
            });
        }

        // The Python suite reads the same values: ASCII whitespace only is
        // trimmed, so a BOM or an information separator keeps the switch set.
        for (const name of ['LEGESHER_TELEMETRY_DISABLED', 'DO_NOT_TRACK']) {
            for (const kill of VECTORS.kill_switch) {
                it(`reads ${name}=${JSON.stringify(kill.value)} as ${kill.set ? 'set' : 'not set'}`, () => {
                    assert.strictEqual(killSwitchSet({ [name]: kill.value }), kill.set);
                    assert.strictEqual(repoAttributionAllowed({ ...on, env: { [name]: kill.value } }), !kill.set);
                });
            }
        }

        for (const value of ['\ufeff0', '\x1c0', '0\x1f']) {
            it(`trips the kill switch for ${JSON.stringify(value)}, as Python does`, () => {
                assert.ok(VECTORS.kill_switch.some((kill) => kill.value === value && kill.set));
                assert.strictEqual(killSwitchSet({ DO_NOT_TRACK: value }), true);
            });
        }

        for (const name of ['LEGESHER_TELEMETRY_DISABLED', 'DO_NOT_TRACK']) {
            it(`honours the ${name} kill switch over every setting`, () => {
                assert.strictEqual(repoAttributionAllowed({ ...on, env: { [name]: '1' } }), false);
                assert.strictEqual(killSwitchSet({ [name]: 'true' }), true);
                assert.strictEqual(killSwitchSet({ [name]: '0' }), false);
            });
        }
    });

    describe('repoLabel', () => {
        const optedIn = {
            repoRoot: '/Users/someone/my-private-project',
            installSalt: SALT,
            telemetryEnabled: true,
            repoAttribution: true,
            vscodeTelemetryEnabled: true,
            env: {},
        };

        it('is the exact digest of the canonical remote, not an encoding of it', () => {
            const label = repoLabel({ ...optedIn, remoteUrl: 'git@github.com:Org/my-private-project.git' });
            const material = `${LABEL_PREFIX}github.com/org/my-private-project`;
            assert.strictEqual(label, sha256Label(material));
            assert.ok(label && HEX32.test(label));
            const bytes = Buffer.from(material, 'utf8');
            for (const encoded of [
                bytes.toString('hex'),
                Buffer.from('github.com/org/my-private-project', 'utf8').toString('hex'),
                bytes.toString('base64'),
                bytes.toString('base64url'),
            ]) {
                assert.notStrictEqual(label, encoded.slice(0, 32));
            }
            const decoded = Buffer.from(label, 'hex').toString('latin1').toLowerCase();
            for (const secret of ['my-private-project', 'private', 'org', 'github', 'legesher']) {
                assert.ok(!label.toLowerCase().includes(secret));
                assert.ok(!decoded.includes(secret), `the label decodes to text containing ${secret}`);
            }
        });

        it('is off unless every gate is on', () => {
            const remoteUrl = 'git@github.com:Org/Repo.git';
            assert.strictEqual(repoLabel({ ...optedIn, repoAttribution: false, remoteUrl }), undefined);
            assert.strictEqual(repoLabel({ ...optedIn, telemetryEnabled: false, remoteUrl }), undefined);
            assert.strictEqual(repoLabel({ ...optedIn, vscodeTelemetryEnabled: false, remoteUrl }), undefined);
            assert.strictEqual(repoLabel({ ...optedIn, env: { DO_NOT_TRACK: '1' }, remoteUrl }), undefined);
        });

        it('falls back to a per-install label without a remote', () => {
            const label = repoLabel({ ...optedIn, remoteUrl: undefined });
            assert.ok(label && HEX32.test(label));
            assert.strictEqual(label, sha256Label(`${LABEL_PREFIX}local:${SALT}:${optedIn.repoRoot}`));
            const other = repoLabel({ ...optedIn, remoteUrl: undefined, installSalt: 'feedface'.repeat(4) });
            assert.ok(other && other !== label);
            assert.ok(!label.includes(SALT));
        });

        for (const remoteUrl of ['user:hunter2@github.com:acme/repo.git', 'https://user:p/ss@github.com/acme/repo.git']) {
            it(`keeps the password in ${JSON.stringify(remoteUrl)} out of the hash`, () => {
                assert.strictEqual(canonicalRemote(remoteUrl), undefined);
                const label = repoLabel({ ...optedIn, remoteUrl });
                assert.strictEqual(label, sha256Label(`${LABEL_PREFIX}local:${SALT}:${optedIn.repoRoot}`));
            });
        }

        it('falls back for a local-path remote such as a Windows drive', () => {
            const label = repoLabel({ ...optedIn, remoteUrl: 'C:/Users/alice/repo' });
            assert.strictEqual(label, sha256Label(`${LABEL_PREFIX}local:${SALT}:${optedIn.repoRoot}`));
        });

        for (const salt of ['', '   ', 'x', 'DEADBEEFDEADBEEFDEADBEEFDEADBEEF', SALT.slice(1), `${SALT}0`, undefined]) {
            it(`gives no label, never an unsalted one, for the salt ${JSON.stringify(salt)}`, () => {
                const label = repoLabel({ ...optedIn, remoteUrl: undefined, installSalt: salt });
                assert.strictEqual(label, undefined);
                assert.notStrictEqual(label, sha256Label(`${LABEL_PREFIX}local::${optedIn.repoRoot}`));
            });
        }

        for (const remoteUrl of [
            'https://alice:s3cr3t\ufe6b@github.com/acme/repo.git',
            'https://[github.com/owner/repo',
            'https://github.com/owner/re\ud800po.git',
        ]) {
            it(`never throws and never echoes the input for ${JSON.stringify(remoteUrl)}`, () => {
                let label: string | undefined;
                assert.doesNotThrow(() => {
                    label = repoLabel({ ...optedIn, remoteUrl });
                });
                assert.ok(label === undefined || HEX32.test(label));
                assert.ok(!(label ?? '').includes('s3cr3t'));
            });
        }

        it('exposes the header under the documented name', () => {
            const headers = repoAttributionHeaders({ ...optedIn, remoteUrl: 'git@github.com:Org/Repo.git' });
            assert.deepStrictEqual(Object.keys(headers), [HEADER]);
            assert.strictEqual(HEADER, 'X-Legesher-Repo');
            assert.deepStrictEqual(repoAttributionHeaders({ ...optedIn, repoAttribution: false, remoteUrl: 'x' }), {});
        });
    });
});
