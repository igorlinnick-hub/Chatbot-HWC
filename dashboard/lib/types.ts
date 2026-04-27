export type Platform = "instagram" | "practice";
export type Status = "active" | "booked" | "dead" | "handed_off";

export interface Message {
  role: "user" | "assistant";
  content: string;
}

export interface HandoffMeta {
  type: "urgent" | "normal";
  summary: string;
  at: string;
  seen: boolean;
}

export interface ConversationMetadata {
  handoff?: HandoffMeta;
  booking_link_sent_at?: string;
  pain_point?: string;
  duration?: string;
  name?: string;
  timezone?: string;
  [key: string]: any;
}

export interface Conversation {
  id: string;
  platform: Platform;
  user_id: string;
  step: number;
  history: Message[];
  metadata: ConversationMetadata;
  status: Status;
  created_at: string;
  last_message_at: string;
}

export interface Correction {
  id: string;
  context: string;
  original_response: string;
  corrected_response: string;
  created_at: string;
}

export interface TrainingExample {
  id: string;
  user_message: string;
  ideal_response: string;
  notes: string | null;
  created_at: string;
}

export interface Stats {
  active: number;
  booked: number;
  handed_off: number;
  dead: number;
  total_corrections: number;
  total_training: number;
}
