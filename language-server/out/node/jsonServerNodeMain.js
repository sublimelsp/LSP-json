"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/
const l10n = require("@vscode/l10n");
async function setupMain() {
    const l10nLog = [];
    const i10lLocation = process.env['VSCODE_L10N_BUNDLE_LOCATION'];
    if (i10lLocation) {
        try {
            await l10n.config({ uri: i10lLocation });
            l10nLog.push(`l10n: Configured to ${i10lLocation.toString()}`);
        }
        catch (e) {
            l10nLog.push(`l10n: Problems loading ${i10lLocation.toString()} : ${e}`);
        }
    }
    await Promise.resolve().then(() => require('./jsonServerMain'));
    l10nLog.forEach(console.log);
}
setupMain();
//# sourceMappingURL=jsonServerNodeMain.js.map