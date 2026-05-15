/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/
import { createConnection } from 'vscode-languageserver/node';
import { formatError } from '../utils/runner.js';
import { startServer } from '../jsonServer.js';
import requestLight from 'request-light';
import { URI as Uri } from 'vscode-uri';
import { promises as fs } from 'fs';
import * as l10n from '@vscode/l10n';
const { xhr, configure: configureHttpRequests, getErrorStatusDescription } = requestLight;
// Create a connection for the server.
const connection = createConnection();
console.log = connection.console.log.bind(connection.console);
console.error = connection.console.error.bind(connection.console);
process.on('unhandledRejection', (e) => {
    connection.console.error(formatError(`Unhandled exception`, e));
});
function getHTTPRequestService() {
    return {
        getContent(uri, _encoding) {
            const headers = { 'Accept-Encoding': 'gzip, deflate' };
            return xhr({ url: uri, followRedirects: 5, headers }).then(response => {
                return response.responseText;
            }, (error) => {
                return Promise.reject(error.responseText || getErrorStatusDescription(error.status) || error.toString());
            });
        }
    };
}
function getFileRequestService() {
    return {
        async getContent(location, encoding) {
            try {
                const uri = Uri.parse(location);
                return (await fs.readFile(uri.fsPath, encoding)).toString();
            }
            catch (e) {
                if (e.code === 'ENOENT') {
                    throw new Error(l10n.t('Schema not found: {0}', location));
                }
                else if (e.code === 'EISDIR') {
                    throw new Error(l10n.t('{0} is a directory, not a file', location));
                }
                throw e;
            }
        }
    };
}
const runtime = {
    timer: {
        setImmediate(callback, ...args) {
            const handle = setImmediate(callback, ...args);
            return { dispose: () => clearImmediate(handle) };
        },
        setTimeout(callback, ms, ...args) {
            const handle = setTimeout(callback, ms, ...args);
            return { dispose: () => clearTimeout(handle) };
        }
    },
    file: getFileRequestService(),
    http: getHTTPRequestService(),
    configureHttpRequests
};
startServer(connection, runtime);
//# sourceMappingURL=jsonServerMain.js.map