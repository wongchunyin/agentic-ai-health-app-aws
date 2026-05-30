using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text.Json;
using System.Text.Json.Serialization;

using LiveWell.Models;

namespace LiveWell.Networking
{
    public static partial class NetworkingAPI
    {
        private static HttpClient client = new HttpClient();
        private static JsonSerializerOptions IgnoreWritingNullOption = new JsonSerializerOptions
        {
            DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull
        };

        private static void SetAuthorizationHeader()
        {
            client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", Account.Current?.token?.id_token);
        }


        public static async Task<List<AgentConversation>?> GetChatHistory()
        {
            string requestUrl = @"https://7xhw2qub6l.execute-api.us-east-1.amazonaws.com/prod/get-chat-history";
            SetAuthorizationHeader();
            HttpResponseMessage response = await client.GetAsync(requestUrl);
            if (!response.IsSuccessStatusCode)
            {
                throw new Exception($"Failed to get chat history. Status code: {response.StatusCode}");
            }
            var responseJson = await response.Content.ReadFromJsonAsync<Dictionary<string, object>>();
            if (responseJson == null || !responseJson.ContainsKey("conversations"))
            {
                throw new Exception("Invalid response from server.");
            }
            List<AgentConversation>? conversations = JsonSerializer.Deserialize<List<AgentConversation>>(responseJson["conversations"].ToString()!);
            return conversations;
        }

        public static async Task RemoveChatHistory(string chat_session_id)
        {
            string requestUrl = $"https://7xhw2qub6l.execute-api.us-east-1.amazonaws.com/prod/remove-chat-history?chat_session_id={chat_session_id}";
            SetAuthorizationHeader();
            HttpResponseMessage response = await client.DeleteAsync(requestUrl);
            if (!response.IsSuccessStatusCode)
            {
                throw new Exception($"Failed to delete chat history. Status code: {response.StatusCode}");
            }
        }

        public static async Task<List<ScheduleTask>?> GetScheduleTasks()
        {
            string requestUrl = $"https://7xhw2qub6l.execute-api.us-east-1.amazonaws.com/prod/schedule-tasks";
            SetAuthorizationHeader();
            HttpResponseMessage response = await client.GetAsync(requestUrl);
            if (!response.IsSuccessStatusCode)
            {
                throw new Exception($"Failed to get scheduled tasks. Status code: {response.StatusCode}");
            }
            var responseJson = await response.Content.ReadFromJsonAsync<Dictionary<string, object>>();
            if (responseJson == null || !responseJson.ContainsKey("tasks"))
            {
                throw new Exception("Invalid response from server.");
            }
            List<ScheduleTask>? tasks = JsonSerializer.Deserialize<List<ScheduleTask>>(responseJson["tasks"].ToString()!);
            return tasks;
        }

        public static async Task RecordActivityDone(string plan_id)
        {
            string requestUrl = $"https://7xhw2qub6l.execute-api.us-east-1.amazonaws.com/prod/increment-activity?plan_id={plan_id}";

            SetAuthorizationHeader();
            HttpResponseMessage response = await client.PatchAsync(requestUrl, null);
            if (!response.IsSuccessStatusCode)
            {
                throw new Exception($"Failed to update plan. Status code: {response.StatusCode}");
            }
        }
    }
}
