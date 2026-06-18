
import { getTfbsWorker, getTfbsWorkerReady } from "./tfbsWorkerInstance";

export const motifWorkerClient = {
    async validateMotifFile({ filename, content }) {
        const w = getTfbsWorker();
        await getTfbsWorkerReady();
        return new Promise((resolve) => {
        const handler = (e) => {
            if (e.data.type === "motif-valid") {
            w.removeEventListener("message", handler);
            resolve(e.data.payload);
            }
        };

        w.addEventListener("message", handler);

        w.postMessage({
            type: "validate-motif-file",
            payload: { filename, content },
        });
        });
    },

    async validateMotifText(sequences) {
        const w = getTfbsWorker();
        await getTfbsWorkerReady();

        return new Promise((resolve) => {
        const handler = (e) => {
            if (e.data.type === "motif-text-valid") {
            w.removeEventListener("message", handler);
            resolve(e.data.payload);
            }
        };

        w.addEventListener("message", handler);

        w.postMessage({
            type: "validate-motif-text",
            payload: { sequences },
        });
        });
    },
};
