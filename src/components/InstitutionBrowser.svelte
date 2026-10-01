<script>
  import { onMount } from "svelte";
  import { readParams, writeParams, normalize } from "../lib/urlstate.js";

  const BASE = import.meta.env.BASE_URL.replace(/\/$/, "");
  const PAGE = 90;

  let items = $state([]);
  let loading = $state(true);
  let q = $state("");
  let type = $state("");
  let district = $state("");
  let oblast = $state("");
  let limit = $state(PAGE);

  onMount(async () => {
    ({ q, institution_type: type, district, oblast } = readParams(["q", "institution_type", "district", "oblast"]));
    const res = await fetch(`${BASE}/Archives/Authorities.json`);
    items = (await res.json()).map((it) => ({
      ...it,
      haystack: normalize([it.name, it.ver, it.district].join(" ")),
    }));
    loading = false;
  });


  const tally = (key) => {
    const m = new Map();
    for (const it of items) if (it[key]) m.set(it[key], (m.get(it[key]) ?? 0) + 1);
    return [...m].sort((a, b) => b[1] - a[1]);
  };
  let types = $derived(tally("type"));
  let districts = $derived(tally("district").sort((a, b) => a[0].localeCompare(b[0])));

  let filtered = $derived.by(() => {
    const needle = normalize(q.trim());
    return items.filter(
      (it) =>
        (!type || it.type === type) &&
        (!district || it.district === district) &&
        (!oblast || it.oblast === oblast) &&
        (!needle || it.haystack.includes(needle)),
    );
  });


  $effect(() => {
    const values = { q, institution_type: type, district, oblast };
    if (loading) return;
    writeParams(values);
    limit = PAGE;
  });

  let oblastLabel = $derived(items.find((it) => it.oblast === oblast)?.oblastName ?? oblast);

  const cls = (c) => (c === "1" ? "on" : c === "0" ? "off" : "unknown");
</script>

<div class="controls">
  <input type="search" bind:value={q} placeholder="Search by name, in English or Ukrainian" aria-label="Search institutions" />
  <select bind:value={district} aria-label="District">
    <option value="">All districts</option>
    {#each districts as [d, n]}
      <option value={d}>{d} ({n})</option>
    {/each}
  </select>
</div>

{#if oblast}
  <p class="region">
    Region: <strong>{oblastLabel}</strong>
    <button class="button" onclick={() => (oblast = "")}>Show all regions</button>
    <a href={`${BASE}/Archives/Map/`}>Back to map</a>
  </p>
{/if}

<div class="types" role="group" aria-label="Institution type">
  <button class:active={!type} onclick={() => (type = "")}>All</button>
  {#each types as [t, n]}
    <button class:active={type === t} onclick={() => (type = type === t ? "" : t)}>
      {t} <span class="num">{n}</span>
    </button>
  {/each}
</div>

{#if loading}
  <p class="muted">Loading institutions…</p>
{:else}
  <p class="count muted">
    <span class="num">{filtered.length.toLocaleString("en-US")}</span>
    {filtered.length === 1 ? "institution" : "institutions"}
  </p>

  <ul class="wall">
    {#each filtered.slice(0, limit) as it (it.id)}
      <li>
        <a href={`${BASE}/Archives/Authorities/${it.id}/`}>
          <span class="name">{it.name}</span>
          {#if it.ver}<span class="ver" lang="uk">{it.ver}</span>{/if}
          <span class="foot">
            <span class="meta">{it.type ?? ""}{it.type && it.district ? ", " : ""}{it.district ?? ""}</span>
            <span class="dots" title={`${it.s.length} web archive${it.s.length === 1 ? "" : "s"}`}>
              {#each it.s.slice(0, 12) as c}<span class="dot {cls(c)}"></span>{/each}
            </span>
          </span>
        </a>
      </li>
    {/each}
  </ul>

  {#if filtered.length > limit}
    <button class="button more" onclick={() => (limit += PAGE)}>
      Show more ({(filtered.length - limit).toLocaleString("en-US")} left)
    </button>
  {/if}
{/if}

<style>
  .controls {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
  }
  .controls input {
    flex: 1 1 320px;
  }
  .region {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.5rem 1rem;
    margin: 1rem 0 0;
  }
  .region .button {
    padding: 0.25em 0.7em;
    font-size: 0.85rem;
  }
  .types {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    margin: 1rem 0 1.5rem;
  }
  .types button {
    font: inherit;
    font-size: 0.95rem;
    color: var(--text);
    background: transparent;
    border: 1px solid var(--line);
    border-radius: 999px;
    padding: 0.3em 0.85em;
    cursor: pointer;
  }
  .types button:hover {
    border-color: var(--muted);
  }
  .types button.active {
    background: var(--yellow);
    border-color: var(--yellow);
    color: #1b1b1b;
  }
  .types .num {
    opacity: 0.65;
    margin-left: 0.2em;
  }
  .count {
    margin-bottom: 0.75rem;
  }
  .wall {
    list-style: none;
    margin: 0;
    padding: 0;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    border-top: 1px solid var(--line);
    border-left: 1px solid var(--line);
  }
  .wall li {
    border-right: 1px solid var(--line);
    border-bottom: 1px solid var(--line);
  }
  .wall a {
    display: flex;
    flex-direction: column;
    height: 100%;
    padding: 1rem 1.1rem;
    color: var(--text);
  }
  .wall a:hover {
    background: var(--surface);
    text-decoration: none;
  }
  .name {
    font-weight: 500;
    line-height: 1.3;
  }
  .ver {
    color: var(--muted);
    font-size: 0.92rem;
    line-height: 1.35;
    margin-top: 0.2rem;
  }
  .foot {
    margin-top: auto;
    padding-top: 0.9rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.75rem;
    font-size: 0.85rem;
  }
  .meta {
    color: var(--muted);
  }
  .dots {
    display: flex;
    gap: 3px;
    font-size: 0.75rem;
  }
  .more {
    margin-top: 1.5rem;
  }
</style>
