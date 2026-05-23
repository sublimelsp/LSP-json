/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/
import { ResponseError, LSPErrorCodes } from 'vscode-languageserver';
export function formatError(message, err) {
    if (err instanceof Error) {
        const error = err;
        return `${message}: ${error.message}\n${error.stack}`;
    }
    else if (typeof err === 'string') {
        return `${message}: ${err}`;
    }
    else if (err) {
        return `${message}: ${err.toString()}`;
    }
    return message;
}
export function runSafeAsync(runtime, func, errorVal, errorMessage, token) {
    return new Promise((resolve) => {
        runtime.timer.setImmediate(() => {
            if (token.isCancellationRequested) {
                resolve(cancelValue());
                return;
            }
            return func().then(result => {
                if (token.isCancellationRequested) {
                    resolve(cancelValue());
                    return;
                }
                else {
                    resolve(result);
                }
            }, e => {
                console.error(formatError(errorMessage, e));
                resolve(errorVal);
            });
        });
    });
}
export function runSafe(runtime, func, errorVal, errorMessage, token) {
    return new Promise((resolve) => {
        runtime.timer.setImmediate(() => {
            if (token.isCancellationRequested) {
                resolve(cancelValue());
            }
            else {
                try {
                    const result = func();
                    if (token.isCancellationRequested) {
                        resolve(cancelValue());
                        return;
                    }
                    else {
                        resolve(result);
                    }
                }
                catch (e) {
                    console.error(formatError(errorMessage, e));
                    resolve(errorVal);
                }
            }
        });
    });
}
function cancelValue() {
    return new ResponseError(LSPErrorCodes.RequestCancelled, 'Request cancelled');
}
//# sourceMappingURL=runner.js.map