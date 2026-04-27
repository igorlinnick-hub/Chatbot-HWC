import { getSupabase, isSupabaseConfigured } from "./supabase";
import {
  mockConversations,
  mockCorrections,
  mockTraining,
  mockStats,
} from "./mock-data";
import type {
  Conversation,
  Correction,
  TrainingExample,
  Stats,
  Status,
} from "./types";

export async function getBotEnabled(): Promise<boolean> {
  const sb = getSupabase();
  if (!sb) return true;
  const { data } = await sb
    .from("bot_settings")
    .select("value")
    .eq("key", "instagram_enabled")
    .maybeSingle();
  return data?.value !== "false";
}

export async function setBotEnabled(enabled: boolean): Promise<void> {
  const sb = getSupabase();
  if (!sb) return;
  await sb
    .from("bot_settings")
    .upsert({ key: "instagram_enabled", value: enabled ? "true" : "false" });
}

function sortForDisplay(rows: Conversation[]): Conversation[] {
  return [...rows].sort((a, b) => {
    const aUnread = a.metadata?.handoff && a.metadata.handoff.seen === false ? 1 : 0;
    const bUnread = b.metadata?.handoff && b.metadata.handoff.seen === false ? 1 : 0;
    if (aUnread !== bUnread) return bUnread - aUnread;
    if (aUnread) {
      const aUrgent = a.metadata?.handoff?.type === "urgent" ? 1 : 0;
      const bUrgent = b.metadata?.handoff?.type === "urgent" ? 1 : 0;
      if (aUrgent !== bUrgent) return bUrgent - aUrgent;
    }
    return (
      new Date(b.last_message_at).getTime() - new Date(a.last_message_at).getTime()
    );
  });
}

export async function listConversations(filters?: {
  status?: Status;
  search?: string;
}): Promise<Conversation[]> {
  const sb = getSupabase();
  if (!sb) {
    let data = mockConversations.filter((c) => c.platform !== "practice");
    if (filters?.status) data = data.filter((c) => c.status === filters.status);
    if (filters?.search) {
      const q = filters.search.toLowerCase();
      data = data.filter((c) => c.user_id.toLowerCase().includes(q));
    }
    return sortForDisplay(data);
  }

  let query = sb
    .from("conversations")
    .select("*")
    .neq("platform", "practice")
    .order("last_message_at", { ascending: false });
  if (filters?.status) query = query.eq("status", filters.status);
  if (filters?.search) query = query.ilike("user_id", `%${filters.search}%`);
  const { data, error } = await query.limit(200);
  if (error) throw error;
  return sortForDisplay((data ?? []) as Conversation[]);
}

export async function getConversation(id: string): Promise<Conversation | null> {
  const sb = getSupabase();
  if (!sb) {
    return mockConversations.find((c) => c.id === id) ?? null;
  }
  const { data } = await sb.from("conversations").select("*").eq("id", id).maybeSingle();
  return (data as Conversation) ?? null;
}

export async function setConversationStatus(
  id: string,
  status: Status
): Promise<void> {
  const sb = getSupabase();
  if (!sb) return;
  await sb.from("conversations").update({ status }).eq("id", id);
}

export async function markHandoffSeen(id: string): Promise<void> {
  const sb = getSupabase();
  if (!sb) {
    const c = mockConversations.find((c) => c.id === id);
    if (c?.metadata?.handoff) c.metadata.handoff.seen = true;
    return;
  }
  const { data } = await sb
    .from("conversations")
    .select("metadata")
    .eq("id", id)
    .maybeSingle();
  const metadata = (data?.metadata ?? {}) as Record<string, any>;
  if (metadata.handoff) {
    metadata.handoff = { ...metadata.handoff, seen: true };
    await sb.from("conversations").update({ metadata }).eq("id", id);
  }
}

export async function getStats(): Promise<Stats> {
  const sb = getSupabase();
  if (!sb) return mockStats;

  const [
    { count: active },
    { count: booked },
    { count: handed },
    { count: dead },
    { count: corrections },
    { count: training },
  ] = await Promise.all([
    sb.from("conversations").select("*", { count: "exact", head: true }).neq("platform", "practice").eq("status", "active"),
    sb.from("conversations").select("*", { count: "exact", head: true }).neq("platform", "practice").eq("status", "booked"),
    sb.from("conversations").select("*", { count: "exact", head: true }).neq("platform", "practice").eq("status", "handed_off"),
    sb.from("conversations").select("*", { count: "exact", head: true }).neq("platform", "practice").eq("status", "dead"),
    sb.from("corrections").select("*", { count: "exact", head: true }),
    sb.from("training_examples").select("*", { count: "exact", head: true }),
  ]);

  return {
    active: active ?? 0,
    booked: booked ?? 0,
    handed_off: handed ?? 0,
    dead: dead ?? 0,
    total_corrections: corrections ?? 0,
    total_training: training ?? 0,
  };
}

export async function listCorrections(): Promise<Correction[]> {
  const sb = getSupabase();
  if (!sb) return mockCorrections;
  const { data } = await sb
    .from("corrections")
    .select("*")
    .order("created_at", { ascending: false })
    .limit(200);
  return (data ?? []) as Correction[];
}

export async function addCorrection(input: {
  context: string;
  original_response: string;
  corrected_response: string;
}): Promise<void> {
  const sb = getSupabase();
  if (!sb) return;
  await sb.from("corrections").insert(input);
}

export async function deleteCorrection(id: string): Promise<void> {
  const sb = getSupabase();
  if (!sb) return;
  await sb.from("corrections").delete().eq("id", id);
}

export async function listTraining(): Promise<TrainingExample[]> {
  const sb = getSupabase();
  if (!sb) return mockTraining;
  const { data } = await sb
    .from("training_examples")
    .select("*")
    .order("created_at", { ascending: false })
    .limit(500);
  return (data ?? []) as TrainingExample[];
}

export async function addTraining(input: {
  user_message: string;
  ideal_response: string;
  notes?: string;
}): Promise<void> {
  const sb = getSupabase();
  if (!sb) return;
  await sb.from("training_examples").insert(input);
}

export async function deleteTraining(id: string): Promise<void> {
  const sb = getSupabase();
  if (!sb) return;
  await sb.from("training_examples").delete().eq("id", id);
}

export { isSupabaseConfigured };
