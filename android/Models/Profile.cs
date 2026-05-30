namespace LiveWell.Models
{
    public class Profile
    {
        public string email { get; set; }
        public string first_name { get; set; }
        public string family_name { get; set; }

        //[JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public string? user_id { get; set; }
        public bool? email_validated { get; set; }
        public string? middle_name { get; set; }
        public string? preferred_name { get; set; }
        public string? full_name { get; set; }
        public string? dob { get; set; }
        public string? gender { get; set; }
        // male female other prefernot_to_say
        public double? height { get; set; }
        public double? weight { get; set; }
        public Address? address { get; set; }
        public List<FitnessDay>? preferred_fitness_days { get; set; }
        public List<Plan>? plans { get; set; }
        public string? provider { get; set; }
        public bool? sms_permission { get; set; }
        public bool? email_permission { get; set; }
        public List<FrailtyAssessment>? frailty_history { get; set; }
        public ProfileMetadata? metadata { get; set; }
        public int? activity_score { get; set; }
        public bool? allowShareName { get; set; }
        public bool? allowSMS { get; set; }
        public bool? allowEmail { get; set; }

        public class Address
        {
            public string? street { get; set; }
            public string? city { get; set; }
            public string? state_province { get; set; }
            public string? postal_code { get; set; }
            public string? country { get; set; }
        }
        public class FitnessDay
        {
            public string? day { get; set; }
            public bool? available { get; set; }
            public List<TimeSlot>? time_slots { get; set; }
            public string? notes { get; set; }

            public class TimeSlot
            {
                public string start_time { get; set; } = string.Empty;
                public string end_time { get; set; } = string.Empty;
            }
        }
        public class ProfileMetadata
        {
            public string? created_at { get; set; }
            public string? updated_at { get; set; }
            public string? created_by { get; set; }
            public string? updated_by { get; set; }
            public int? version { get; set; }
            public string? source { get; set; }
        }
    }
}
