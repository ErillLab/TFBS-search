// src/services/tfbsWorkerInstance.js
let worker = null;
let readyPromise = null;

export function getTfbsWorker() {
    if (!worker) {
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