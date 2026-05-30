namespace LiveWell.Models
{
    public class FrailtyAssessment
    {
        public string? assessment_id { get; set; }
        public string? timestamp { get; set; }
        public string? assessment_type { get; set; }
        public double? score { get; set; }
        public Dictionary<string, object>? assessment_data { get; set; }
        public string? status { get; set; }
        public FrailtyResult? result { get; set; }
        public string? notes { get; set; }
        public Metadata? metadata { get; set; }

        public class FrailtyResult
        {
            public double? score { get; set; }
            public string? level { get; set; }
            public string? description { get; set; }
        }
        public class Metadata
        {
            public string? created_at { get; set; }
            public string? updated_at { get; set; }
            public string? created_by { get; set; }
            public string? updated_by { get; set; }
            public double? version { get; set; }
            public string? source { get; set; }
        }
    }
}
