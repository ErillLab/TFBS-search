// src/services/genomeWorkerClient.js
import { getTfbsWorker, getTfbsWorkerReady } from "./tfbsWorkerInstance";

export const genomeWorkerClient = {
  async validateGenomeFile({ filename, content }) {
    const w = getTfbsWorker();
    await getTfbsWorkerReady();

    return new Promise((resolve) => {
      const handler = (e) => {
        if (e.data.type === "genome-valid") {
          w.removeEventListener("message", handler);
          resolve(e.data.payload);
        }
        if(e.data.type === "debug") {
          console.log("[DEBUG FROM WORKER]", e.data.payload.received)
        }
      };


      w.addEventListener("message", handler);

      w.postMessage({
        type: "validate-genome",
        payload: { filename, content },
      });
    });
  },

  async validateAccession(accession) {
    const w = getTfbsWorker();
    await getTfbsWorkerReady();

    return new Promise((resolve) => {
      const handler = (e) => {
        if (e.data.type === "accession-valid") {
          w.removeEventListener("message", handler);
          console.log("[CLIENT] Worker response:", e.data);

          resolve(e.data.payload);
        }
      };

      w.addEventListener("message", handler);

      w.postMessage({
        type: "validate-accession",
        payload: { accession },
      });
    });
  },
};