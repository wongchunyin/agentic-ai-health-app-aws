namespace LiveWell.Models
{
    public class AgentConversation
    {
        public string? conversation_id { get; set; }
        public string? chat_session_name { get; set; }
        public int? message_count { get; set; }
        public string? created_at { get; set; }
        public string? updated_at { get; set; }
        public List<Message>? messages { get; set; }

        public class Message
        {
            public string? role { get; set; }
            public string? content { get; set; }
            public string? timestamp { get; set; }
            public bool? hidden_for_user { get; set; }
        }
    }
}
