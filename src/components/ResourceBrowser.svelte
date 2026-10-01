<script>
  import { onMount } from "svelte";
  import { readParams, writeParams, normalize } from "../lib/urlstate.js";

  const BASE = import.meta.env.BASE_URL.replace(/\/$/, "");
  const PAGE = 100;

  let items = $state([]);
  let loading = $state(true);
  let q = $state("");
  let status = $state(""); // "", "online", "offline"
  let sort = $state("date"); // "date" | "id"
  let limit = $state(PAGE);

  onMount(async () => {
    const p = readParams(["q", "status", "sort"]);
    q = p.q;
    status = p.status;
    sort = p.sort || "date";
    const res = await fetch(`${BASE}/Archives/Resources.json`);
    items = (await res.json()).map((it) => {
      const m = String(it.url).match(/^(?:https?:\/\/)?(?:www\.)?([^/]+)(.*)$/);
      return {
        ...it,
        host: m ? m[1] : it.url,
        path: m && m[2] !== "/" ? m[2] : "",
        haystack: normalize(`${it.url} ${it.name ?? ""} ${it.inst ?? ""}`),
      };
    });
    loading = false;
  });

  const statuses = [
    ["", "All"],
    ["online", "Online"],
    ["offline", "Offline"],
  ];
  let counts = $derived({
    "": items.length,
    online: items.filter((it) => it.s === 1).length,
    offline: items.filter((it) => it.s === 0).length,
  });

  let filtered = $derived.by(() => {
    const needle = normalize(q.trim());
    const out = items.filter(
      (it) =>
        (!status || (status === "online" ? it.s === 1 : it.s === 0)) &&
        (!needle || it.haystack.includes(needle)),
    );
    if (sort === "date") out.sort((a, b) => (a.date ?? "9999").localeCompare(b.date ?? "9999"));
    else out.sort((a, b) => a.id - b.id);
    return out;
  });

  $effect(() => {
    const values = { q, status, sort: sort === "date" ? "" : sort };
    if (loading) return;
    writeParams(values);
    limit = PAGE;
  });

  const cls = (s) => (s === 1 ? "on" : s === 0 ? "off" : "unknown");
  const label = (s) => (s === 1 ? "Online" : s === 0 ? "Offline" : "Not checked");
</script>

<div class="controls">
  <input type="search" bind:value={q} placeholder="Search by URL, collection or institution" aria-label="Search archived sites" />
  <div class="segmented" role="group" aria-label="Online status">
    {#each statuses as [value, text]}
      <button class:active={status === value} onclick={() => (status = value)}>
        {#if value}<span class="dot {value === 'online' ? 'on' : 'off'}"></span>{/if}
        {text}
        {#if !loading}<span class="num">{counts[value].toLocaleString("en-US")}</span>{/if}
      </button>
    {/each}
  </div>
  <select bind:value={sort} aria-label="Sort">
    <option value="date">Oldest archive first</option>
    <option value="id">By SUCHO ID</option>
  </select>
</div>

{#if loading}
  <p class="muted">Loading archived sites…</p>
{:else}
  <p class="count muted">
    <span class="num">{filtered.length.toLocaleString("en-US")}</span>
    {filtered.length === 1 ? "archived site" : "archived sites"}
  </p>

  <ol class="list">
    {#each filtered.slice(0, limit) as it (it.id)}
      <li>
        <span class="dot {cls(it.s)}" title={label(it.s)}></span>
        <a class="url" href={`${BASE}/Archives/Resources/${it.id}/`}>
          <span class="host">{it.host}</span><span class="path">{it.path}</span>
        </a>
        <span class="inst">
          {#if it.iid}<a href={`${BASE}/Archives/Authorities/${it.iid}/`}>{it.inst}</a>{/if}
        </span>
        <span class="date num">{it.date ?? "–"}</span>
      </li>
    {/each}
  </ol>

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
    margin-bottom: 1.5rem;
  }
  .controls input {
    flex: 1 1 300px;
  }
  .segmented {
    display: flex;
    border: 1px solid var(--line);
    border-radius: var(--radius);
    overflow: hidden;
  }
  .segmented button {
    display: flex;
    align-items: center;
    gap: 0.45em;
    font: inherit;
    font-size: 0.95rem;
    color: var(--text);
    background: var(--surface);
    border: 0;
    border-left: 1px solid var(--line);
    padding: 0.5em 0.9em;
    cursor: pointer;
  }
  .segmented button:first-child {
    border-left: 0;
  }
  .segmented button.active {
    background: var(--surface-2);
    box-shadow: inset 0 -2px 0 var(--yellow);
  }
  .segmented .num {
    color: var(--muted);
    font-size: 0.85em;
  }
  .count {
    margin-bottom: 0.5rem;
  }
  .list {
    list-style: none;
    margin: 0;
    padding: 0;
    border-top: 1px solid var(--line);
  }
  .list li {
    display: grid;
    grid-template-columns: 1rem minmax(0, 1.4fr) minmax(0, 1fr) 6.5rem;
    align-items: baseline;
    gap: 1rem;
    padding: 0.65rem 0.25rem;
    border-bottom: 1px solid var(--line);
  }
  .list li:hover {
    background: var(--surface);
  }
  .url {
    color: var(--text);
    overflow-wrap: anywhere;
  }
  .host {
    font-weight: 500;
  }
  .path {
    color: var(--muted);
  }
  .inst {
    font-size: 0.92rem;
  }
  .date {
    color: var(--muted);
    font-size: 0.9rem;
    text-align: right;
  }
  .more {
    margin-top: 1.5rem;
  }
  @media (max-width: 700px) {
    .list li {
      grid-template-columns: 1rem minmax(0, 1fr);
      gap: 0.2rem 0.75rem;
    }
    .inst,
    .date {
      grid-column: 2;
      text-align: left;
    }
  }
</style>
