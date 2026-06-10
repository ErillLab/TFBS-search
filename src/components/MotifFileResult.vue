<template>
  <div class="file-list">
    <div class="file-item">
      <span class="file-item-name">
        <i class="ti ti-file" aria-hidden="true"></i>
        {{ fileName }}
      </span>
      <div class="file-item-actions">
        <button
          v-if="sequences.length"
          class="btn btn-ghost"
          :aria-label="show ? 'Hide sequences' : 'Show sequences'"
          @click="show = !show"
        >
          <i class="ti" :class="show ? 'ti-chevron-up' : 'ti-chevron-down'" aria-hidden="true"></i>
        </button>
        <button class="btn btn-ghost" aria-label="Remove" @click="$emit('clear')">
          <i class="ti ti-x" aria-hidden="true"></i>
        </button>
      </div>
    </div>

    <div v-if="show && sequences.length" class="sublist">
      <div
        v-for="(seq, i) in sequences.slice(0, 10)"
        :key="i"
        class="sublist-item"
      >
        <span class="sublist-index">{{ i + 1 }}</span>
        <code class="sublist-mono">{{ seq }}</code>
      </div>
      <div v-if="sequences.length > 10" class="sublist-more">
        + {{ sequences.length - 10 }} more sequences
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'MotifFileResult',
  emits: ['clear'],
  props: {
    fileName:  { type: String,  required: true },
    sequences: { type: Array,   default: () => [] }
  },
  data() {
    return { show: false }
  }
}
</script>


<style scoped>
/* ── Sublist (sequences / accessions) ── */
.sublist {
  margin-top: 0.4rem;
  border: 1px solid var(--c-border);
  border-radius: 8px;
  overflow: hidden;
}

.sublist-item {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.35rem 0.75rem;
  border-bottom: 1px solid var(--c-border);
  font-size: 0.78rem;
}
.sublist-item:last-child { border-bottom: none; }
.sublist-item:nth-child(even) { background: var(--c-bg); }

.sublist-index {
  font-family: var(--mono);
  font-size: 0.68rem;
  color: var(--c-muted);
  min-width: 1.2rem;
  text-align: right;
  flex-shrink: 0;
}

.sublist-mono {
  font-family: var(--mono);
  font-size: 0.78rem;
  color: var(--c-text);
  letter-spacing: 0.05em;
  word-break: break-all;
}

.sublist-more {
  padding: 0.35rem 0.75rem;
  font-size: 0.72rem;
  font-family: var(--mono);
  color: var(--c-muted);
  font-style: italic;
  background: var(--c-bg);
}

/* ── File item actions ── */
.file-item-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}
</style>