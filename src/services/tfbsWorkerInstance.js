// src/services/tfbsWorkerInstance.js
let worker = null;
let readyPromise = null;
let cancelBuffer = null;

export const cancelSupported = typeof SharedArrayBuffer !== "undefined" && crossOriginIsolated === true;

export function getTfbsWorker() {
    if (!worker) {
        
        worker = new Worker(
            new URL("../workers/tfbsWorker.js", import.meta.url));


        worker.onerror = (e) => {
            console.error("[tfbsWorker] ERROR:", e.message, e);
        };
        worker.onmessageerror = (e) => {
            console.error("[tfbsWorker] MESSAGE ERROR:", e);
        }; 

        if(cancelSupported){
            cancelBuffer = new SharedArrayBuffer(1);
            worker.postMessage({type:"init-cancel-buffer", buffer: cancelBuffer })
        }
        //Send the shared buffer to the worker 
        

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
        Atomics.store(new Uint8Array(cancelBuffer), 0, 1);
    }
    else {
        const w = getTfbsWorker();
        w.postMessage({type: "cancel"});
    }
}

export function clearCancelFlag() {
    if(cancelBuffer) {
        Atomics.store(new Uint8Array(cancelBuffer), 0, 0);
    }
}