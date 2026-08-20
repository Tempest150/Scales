export const titleCase = (str) => {
  return str
    .split(" ")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}
export const parseTagField = (value) => {
  if (Array.isArray(value)) return value;
  if (typeof value === "string") {
    try {
      const parsed = JSON.parse(value.replace(/'/g, '"'));
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  }
  return [];
}

export const parseTags = (tags) => {
  console.log("Parsing tags:", typeof tags);

  if (!tags) return {};

  // Handle JSON-string input
  if (typeof tags === "string") {
    try {
      tags = JSON.parse(tags);
    } catch (e) {
      console.warn("Failed to parse tags string:", tags, e);
      return {};
    }
  }

  if (typeof tags !== "object") return {};

  const result = {};
  for (const [key, value] of Object.entries(tags)) {
    const items = parseTagField(value);
    if (items.length > 0) result[key] = items;
  }
  return result;
};