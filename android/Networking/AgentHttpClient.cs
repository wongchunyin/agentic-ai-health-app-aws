using System.Diagnostics;
using System.Net.Http.Json;
using LiveWell.Models;

namespace LiveWell.Networking
{
    internal class AgentHttpClient : HttpClient
    {
        string requestUri = @"https://7xhw2qub6l.execute-api.us-east-1.amazonaws.com/prod/ai-v2";
        private class RequestContent
        {
            public string query { get; set; } = string.Empty;
        }
        public class ResponseContent
        {
            public string response { get; set; } = "Sorry, I couldn't process your request at the moment.";
            public string query { get; set; } = string.Empty;
            public string response_type { get; set; } = string.Empty;
            public int steps_count { get; set; } = 0;
            public string user_id { get; set; } = string.Empty;
            public string chat_session_id { get; set; } = string.Empty;
        }

        public async Task<ResponseContent?> GetAgentResponse(string message)
        {
            RequestContent content = new()
            {
                query = message
            };
            ResponseContent? response = await PostAsync(content);
            if (response == null)
            {
                return null;
            }
            return response;
        }

        private async Task<ResponseContent?> PostAsync(RequestContent content)
        {
            try
            {
                DefaultRequestHeaders.Authorization = new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", Account.Current?.token?.id_token);
                HttpResponseMessage response = await PostAsync(requestUri, JsonContent.Create(content));

                if (response.IsSuccessStatusCode)
                {
                    ResponseContent? responseContent = await response.Content.ReadFromJsonAsync<ResponseContent>();
                    return responseContent;
                }
                else
                {
                    Debug.Print(response.Content.ToString());
                    return null;
                }
            }
            catch (Exception ex)
            {
                Debug.Print(ex.Message);
                return null;
            }
        }
    }
}
