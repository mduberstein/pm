import { appendChatExchange, createChatMessage, toChatHistory } from "@/lib/chat";

describe("chat helpers", () => {
  it("creates a chat message with role and content", () => {
    const message = createChatMessage("user", "Hello");

    expect(message.role).toBe("user");
    expect(message.content).toBe("Hello");
    expect(message.id).toMatch(/^msg-/);
  });

  it("maps messages to API chat history payload", () => {
    const messages = [
      createChatMessage("user", "First"),
      createChatMessage("assistant", "Second"),
    ];

    expect(toChatHistory(messages)).toEqual([
      { role: "user", content: "First" },
      { role: "assistant", content: "Second" },
    ]);
  });

  it("appends user and assistant messages for a completed turn", () => {
    const start = [createChatMessage("assistant", "Welcome")];

    const updated = appendChatExchange(start, "Move card-1", "Done. I moved it.");

    expect(updated).toHaveLength(3);
    expect(updated[1].role).toBe("user");
    expect(updated[1].content).toBe("Move card-1");
    expect(updated[2].role).toBe("assistant");
    expect(updated[2].content).toBe("Done. I moved it.");
  });
});
