/**
 * The data contract (export/WEB_CONTRACT.md §1): three files loaded in order.
 *   quiz_core.json  — ~2 KB, bundled with the app: the start page and the core questions never wait for a request;
 *   quiz_data.json  — fetched as soon as the app is up (hashed asset URL, cached forever);
 *   quiz_bills.json — fetched as soon as quiz_data has arrived.
 * All three carry the same generated / source_commit; a mismatch (a deploy mid-session) is retried once
 * bypassing the cache, then reported.
 */
import coreRaw from '@export/quiz_core.json';
import dataUrl from '@export/quiz_data.json?url';
import billsUrl from '@export/quiz_bills.json?url';
import type { BillsFile, CoreFile, DataFile, FileHead } from './engine/types';

export const core = coreRaw as CoreFile;

export interface LoadedFiles {
  data: DataFile;
  bills: BillsFile;
}

export type FileName = keyof LoadedFiles;
export type LoadedFile = { name: 'data'; file: DataFile } | { name: 'bills'; file: BillsFile };

export function sameBuild(a: FileHead, b: FileHead): boolean {
  return a.generated === b.generated && a.source_commit === b.source_commit;
}

async function fetchJson<T>(url: string, reload: boolean): Promise<T> {
  const res = await fetch(url, reload ? { cache: 'reload' } : {});
  if (!res.ok) throw new Error(`${url}: HTTP ${res.status}`);
  return (await res.json()) as T;
}

/**
 * Fetches quiz_data, then quiz_bills; calls onFile for each as it arrives (in that order), onError if a file cannot be
 * loaded or does not belong to the same build as the bundled quiz_core even after one retry bypassing the cache.
 */
export async function loadFiles(onFile: (loaded: LoadedFile) => void, onError: (error: Error) => void): Promise<void> {
  const urls: Record<FileName, string> = { data: dataUrl, bills: billsUrl };
  try {
    for (const name of ['data', 'bills'] as const) {
      let file = await fetchJson<FileHead>(urls[name], false);
      if (!sameBuild(file, core)) file = await fetchJson<FileHead>(urls[name], true);
      if (!sameBuild(file, core)) throw new Error(`${name}: data files from different builds`);
      onFile(name === 'data' ? { name, file: file as DataFile } : { name, file: file as BillsFile });
    }
  } catch (e) {
    onError(e instanceof Error ? e : new Error(String(e)));
  }
}
