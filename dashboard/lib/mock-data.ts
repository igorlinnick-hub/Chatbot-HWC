import type { Conversation, Correction, TrainingExample, Stats } from "./types";

const now = Date.now();
const minsAgo = (n: number) => new Date(now - n * 60_000).toISOString();
const hoursAgo = (n: number) => new Date(now - n * 3_600_000).toISOString();
const daysAgo = (n: number) => new Date(now - n * 86_400_000).toISOString();

export const mockConversations: Conversation[] = [
  {
    id: "mock-1",
    platform: "instagram",
    user_id: "ig_user_482931",
    step: 4,
    status: "active",
    history: [
      { role: "assistant", content: "Aloha, thanks for the follow. Are you here for the content or exploring how we could support your wellness journey?" },
      { role: "user", content: "honestly i've been so wiped out lately, no energy to do anything after work" },
      { role: "assistant", content: "That sounds really draining, like you're running on empty by the time the day's done. I'm wondering, what area of your wellness are you most wanting to work on right now?" },
      { role: "user", content: "energy and sleep mostly, i fall asleep fine but wake up at 3am" },
      { role: "assistant", content: "The 3am wake-up is rough, especially when you're already tired. I'm curious, if you were able to really shift this, what would that change open up for you?" },
      { role: "user", content: "honestly just being present with my kids again, not running on fumes" },
    ],
    metadata: { name: "Sarah", timezone: "HST", pain_point: "low energy and broken sleep", duration: "about 6 months" },
    created_at: daysAgo(2),
    last_message_at: minsAgo(12),
  },
  {
    id: "mock-2",
    platform: "instagram",
    user_id: "ig_user_193847",
    step: 9,
    status: "booked",
    history: [
      { role: "assistant", content: "Aloha, thanks for the follow." },
      { role: "user", content: "hi i want to try wellness coaching for stress" },
      { role: "assistant", content: "Stress work is one of our favourite areas to support people in." },
      { role: "user", content: "can i book a call" },
      { role: "assistant", content: "Absolutely, here's the calendar:" },
    ],
    metadata: { name: "Marcus", booking_link_sent_at: hoursAgo(3) },
    created_at: daysAgo(1),
    last_message_at: hoursAgo(3),
  },
  {
    id: "mock-3",
    platform: "instagram",
    user_id: "ig_user_72819",
    step: 2,
    status: "handed_off",
    history: [
      { role: "assistant", content: "Aloha, thanks for the follow." },
      { role: "user", content: "URGENT i am having panic attack right now help" },
    ],
    metadata: {
      handoff: {
        type: "urgent",
        summary: "Client reported active panic attack — needs immediate human contact, bot withheld medical advice.",
        at: hoursAgo(5),
        seen: false,
      },
    },
    created_at: hoursAgo(5),
    last_message_at: hoursAgo(5),
  },
  {
    id: "mock-4",
    platform: "instagram",
    user_id: "ig_user_301200",
    step: 6,
    status: "active",
    history: [
      { role: "assistant", content: "Aloha." },
      { role: "user", content: "i've been wanting to get a routine going around movement and eating but i keep falling off" },
      { role: "assistant", content: "That on-and-off cycle is so common, and exhausting in its own way." },
    ],
    metadata: {},
    created_at: daysAgo(3),
    last_message_at: hoursAgo(8),
  },
  {
    id: "mock-5",
    platform: "instagram",
    user_id: "ig_user_555020",
    step: 3,
    status: "dead",
    history: [
      { role: "assistant", content: "Aloha." },
      { role: "user", content: "how much do sessions cost" },
    ],
    metadata: {},
    created_at: daysAgo(14),
    last_message_at: daysAgo(10),
  },
  {
    id: "mock-6",
    platform: "instagram",
    user_id: "ig_user_887123",
    step: 5,
    status: "active",
    history: [
      { role: "assistant", content: "Aloha." },
      { role: "user", content: "stress is killing me right before exams" },
      { role: "assistant", content: "Exam stress is so real. Tell me more about how it shows up for you." },
      { role: "user", content: "i cant sleep night before" },
    ],
    metadata: {},
    created_at: hoursAgo(18),
    last_message_at: minsAgo(45),
  },
];

export const mockCorrections: Correction[] = [
  {
    id: "mc-1",
    context: "i've been so wiped out lately",
    original_response: "I'm sorry to hear you're struggling with low energy. Many people benefit from a regular sleep routine.",
    corrected_response: "That sounds really draining, like you're running on empty by the time the day's done. I'm wondering, what area of your wellness are you most wanting to work on right now?",
    created_at: daysAgo(1),
  },
  {
    id: "mc-2",
    context: "i have trouble sleeping",
    original_response: "Try meditation and a consistent bedtime routine.",
    corrected_response: "The 3am wake-up can feel so isolating, especially when it's just you and your thoughts. What does it usually look like for you — trouble falling asleep, or waking up?",
    created_at: daysAgo(4),
  },
];

export const mockTraining: TrainingExample[] = [
  {
    id: "mt-1",
    user_message: "I feel like nothing ever works for my energy levels",
    ideal_response: "That exhaustion of trying and trying and still feeling drained — it's so real, and it's not your fault. Can I ask what you've already tried?",
    notes: "Mirror + validate + gentle inquiry, no advice yet",
    created_at: daysAgo(5),
  },
  {
    id: "mt-2",
    user_message: "How much do sessions cost?",
    ideal_response: "Great question — I want to first make sure the clinic is the right fit for what you're working through. Tell me a bit about what brought you here?",
    notes: "Redirect price questions back to qualification",
    created_at: daysAgo(8),
  },
];

export const mockStats: Stats = {
  active: mockConversations.filter((c) => c.status === "active").length,
  booked: mockConversations.filter((c) => c.status === "booked").length,
  handed_off: mockConversations.filter((c) => c.status === "handed_off").length,
  dead: mockConversations.filter((c) => c.status === "dead").length,
  total_corrections: mockCorrections.length,
  total_training: mockTraining.length,
};
