export async function getItem(key: string): Promise<string | null> {
  return window.localStorage.getItem(key);
}

export async function setItem(key: string, value: string): Promise<void> {
  window.localStorage.setItem(key, value);
}

export async function deleteItem(key: string): Promise<void> {
  window.localStorage.removeItem(key);
}
