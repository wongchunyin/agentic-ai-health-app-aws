namespace LiveWell.Networking
{
    public class Token
    {
        public string id_token { get; set; } = string.Empty;
        public string access_token { get; set; } = string.Empty;
        public string refresh_token { get; set; } = string.Empty;
        public int expires_in { get; set; } = 0;
        public string token_type { get; set; } = string.Empty;
    }
}
