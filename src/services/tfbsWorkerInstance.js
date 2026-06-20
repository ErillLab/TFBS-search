// src/services/tfbsWorkerInstance.js
let worker = null;
let readyPromise = null;

let cancelBuffer = null;

export function getTfbsWorker() {
    if (!worker) {
        cancelBuffer = new SharedArrayBuffer(1);
        worker = new Worker(
            new URL("../workers/tfbsWorker.js", import.meta.url),
            { type: "module" }
        );


        worker.onerror = (e) => {
            console.error("[tfbsWorker] ERROR:", e.message, e);
        };
        worker.onmessageerror = (e) => {
            console.error("[tfbsWorker] MESSAGE ERROR:", e);
        }; 

        //Send the shared buffer to the worker 
        worker.postMessage({type:"init-cancel-buffer", buffer: cancelBuffer })

        readyPromise = new Promise((resolve) => {
            const handler = (e) => {
                console.log("[tfbsWorker] message:", e.data);
                if (e.data.type === "ready") {
                    worker.removeEventListener("message", handler);
                    resolve();
                }
            };
            worker.addEventListener("message", handler);
        });
    }
    return worker;
}

export function getTfbsWorkerReady() {
    getTfbsWorker();
    return readyPromise;
}

export function requestCancel() {
    if(cancelBuffer) {
        const view = new Uint8Array(cancelBuffer);
        Atomics.store(view, 0, 1);
    }
}

export function clearCancelFlag() {
    if(cancelBuffer) {
        const view = new Uint8Array(cancelBuffer);
        Atomics.store(view, 0, 0);
    }
}