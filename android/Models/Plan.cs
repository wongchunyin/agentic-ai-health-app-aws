using System.Text.Json.Serialization;

namespace LiveWell.Models
{
    public class Plan
    {
        public string plan_type { get; set; }
        public Action action { get; set; }
        public string actor { get; set; }
        public Context context { get; set; }
        public string target { get; set; }
        public Time time { get; set; }

        [JsonIgnore]
        public string? plan_id { get; set; }
        [JsonInclude]
        [JsonPropertyName("plan_id")]
        private string? _plan_id
        {
            set { plan_id = value; }
        }
        [JsonIgnore]
        public string? created_at { get; set; }
        [JsonInclude]
        [JsonPropertyName("created_at")]
        private string? _created_at
        {
            set { created_at = value; }
        }
        [JsonIgnore]
        public string? end_at { get; set; }
        [JsonInclude]
        [JsonPropertyName("end_at")]
        private string? _end_at
        {
            set { end_at = value; }
        }
        [JsonIgnore]
        public string? status { get; set; }
        [JsonInclude]
        [JsonPropertyName("status")]
        private string? _status
        {
            set { status = value; }
        }

        public class Action
        {
            public string name { get; set; }
            public string action_type { get; set; }
            public string description { get; set; }
        }
        public class Context
        {
            public string location { get; set; }
            public string condition { get; set; }
        }
        public class Time
        {
            public Frequency frequency { get; set; }
            public Duration duration { get; set; }

            public class Frequency
            {
                public int value { get; set; }
                public string unit { get; set; }
            }
            public class Duration
            {
                public int value { get; set; }
                public string unit { get; set; }
            }
        }
    }
}
